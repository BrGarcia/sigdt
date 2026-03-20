import os
from fastapi import FastAPI, Request, UploadFile, File, Depends, Form, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
import io
import pandas as pd
from sqlmodel import Session, select, desc, or_
from datetime import datetime

from app.database import init_db, get_session, engine
from app.models import Diretiva, Aeronave, DiretivaAeronave
from app.services.csv_service import process_csv
from typing import Optional

from app.users import routes as user_routes
from app.users import actions as user_actions
from app.users import schemas as user_schemas
from app.users.routes import get_current_user, get_current_admin_user, get_optional_current_user, get_current_inspector_user
from app.users.models import User

app = FastAPI(title="SIGDT - Sistema de Gestão de Diretivas Técnicas")

# Templates
templates = Jinja2Templates(directory="app/templates")

@app.on_event("startup")
def on_startup():
    os.makedirs("app/static", exist_ok=True)
    init_db()
    with Session(engine) as session:
        admin_user = user_actions.get_user(session, "admin")
        if not admin_user:
            user_in = user_schemas.UserCreate(username="admin", email="admin@example.com", password="admin")
            admin_user = user_actions.create_user(session, user_in, role="admin")
        else:
            admin_user.role = "admin"
            session.add(admin_user)
            session.commit()


# Static files and user routes
if not os.path.exists("app/static"):
    os.makedirs("app/static", exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(user_routes.router)


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, session: Session = Depends(get_session), current_user: Optional[User] = Depends(get_optional_current_user)):
    # Fetch first 100 directive links ordered by GUT desc
    statement = select(DiretivaAeronave).order_by(desc(DiretivaAeronave.gut)).limit(100)
    diretiva_links = session.exec(statement).all()
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "diretivas": diretiva_links,
        "current_user": current_user
    })

@app.post("/upload", dependencies=[Depends(get_current_admin_user)])
async def upload_csv(request: Request, file: UploadFile = File(...), session: Session = Depends(get_session)):
    content = await file.read()
    process_csv(content.decode('utf-8'))
    return RedirectResponse(url="/", status_code=303)

@app.get("/directives", response_class=HTMLResponse)
async def list_directives(
    request: Request, 
    search: Optional[str] = None, 
    session: Session = Depends(get_session)
):
    statement = select(DiretivaAeronave).join(Diretiva).join(Aeronave).order_by(desc(DiretivaAeronave.gut))
    if search:
        search_filter = f"%{search}%"
        statement = statement.where(
            or_(
                Aeronave.numero_serie.like(search_filter), 
                Diretiva.codigo_diretiva.like(search_filter),
                Aeronave.matricula.like(search_filter)
            )
        )
    
    diretiva_links = session.exec(statement.limit(100)).all()
    return templates.TemplateResponse("partials/directives_table.html", {
        "request": request, 
        "diretivas": diretiva_links
    })

@app.get("/directives/{diretiva_id}", response_class=HTMLResponse)
async def get_directive_details(
    request: Request,
    diretiva_id: int,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    # diretiva_id here refers to the ID of DiretivaAeronave (the link)
    link = session.get(DiretivaAeronave, diretiva_id)
    if not link:
        raise HTTPException(status_code=404, detail="Vínculo de Diretiva not found")
    
    return templates.TemplateResponse("directive_details.html", {
        "request": request,
        "diretiva": link,
        "current_user": current_user
    })

@app.post("/directives/{diretiva_id}", response_class=HTMLResponse, dependencies=[Depends(get_current_inspector_user)])
async def update_directive_details(
    request: Request,
    diretiva_id: int,
    status: str = Form(...),
    observacoes: str = Form(...),
    especialidade: Optional[str] = Form(None),
    pdf_file: Optional[UploadFile] = File(None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_inspector_user)
):
    link = session.get(DiretivaAeronave, diretiva_id)
    if not link:
        raise HTTPException(status_code=404, detail="Vínculo de Diretiva not found")
    
    # Check specialty permission for inspectors
    if current_user.role == 'inspector':
        if link.diretiva.especialidade and current_user.especialidade != link.diretiva.especialidade:
            raise HTTPException(status_code=403, detail="Você não tem permissão para alterar diretivas desta especialidade.")

    # Update fields
    link.status = status
    link.observacao = observacoes
    
    # Admin can update master directive specialty
    if current_user.role == 'admin' and especialidade:
        link.diretiva.especialidade = especialidade
        session.add(link.diretiva)

    # Handle PDF upload
    if pdf_file and pdf_file.filename:
        upload_dir = "app/static/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_ext = os.path.splitext(pdf_file.filename)[1]
        new_filename = f"diretiva_link_{diretiva_id}_{int(datetime.utcnow().timestamp())}{file_ext}"
        file_path = os.path.join(upload_dir, new_filename)
        
        with open(file_path, "wb") as buffer:
            content = await pdf_file.read()
            buffer.write(content)
        
        link.pdf_path = new_filename

    session.add(link)
    session.commit()
    session.refresh(link)
    
    return templates.TemplateResponse("directive_details.html", {
        "request": request,
        "diretiva": link,
        "current_user": current_user
    })

@app.post("/update-tendencia/{diretiva_id}", dependencies=[Depends(get_current_admin_user)])
async def update_tendencia(
    request: Request,
    diretiva_id: int,
    tendencia: int = Form(...),
    session: Session = Depends(get_session)
):
    link = session.get(DiretivaAeronave, diretiva_id)
    if link:
        link.tendencia = tendencia
        link.calculate_gut()
        session.add(link)
        session.commit()
        session.refresh(link)
    
    return templates.TemplateResponse("partials/directive_row.html", {
        "request": request,
        "diretiva": link
    })

@app.get("/users/manage", response_class=HTMLResponse, dependencies=[Depends(get_current_admin_user)])
async def manage_users_page(request: Request, session: Session = Depends(get_session)):
    users = session.exec(select(User)).all()
    return templates.TemplateResponse("user_management.html", {"request": request, "users": users})

@app.get("/export/xlsx", dependencies=[Depends(get_current_inspector_user)])
async def export_xlsx(session: Session = Depends(get_session)):
    statement = select(DiretivaAeronave).join(Diretiva).join(Aeronave)
    links = session.exec(statement).all()
    
    data = []
    for link in links:
        data.append({
            'PN': link.diretiva.pn if hasattr(link.diretiva, 'pn') else '', # Use logic if Master DT has PN or link has it
            'MATRICULA': link.aeronave.matricula,
            'NUMERO_SERIE': link.aeronave.numero_serie,
            'DIRETIVA_TECNICA': link.diretiva.codigo_diretiva,
            'FADT': link.diretiva.fadt,
            'STATUS': link.status,
            'CLA': link.diretiva.classe,
            'CAT': link.diretiva.categoria,
            'ESPECIALIDADE': link.diretiva.especialidade,
            'OBSERVACOES': link.observacao,
            'GUT': link.gut
        })
    
    if not data:
        df = pd.DataFrame(columns=['MATRICULA', 'DIRETIVA_TECNICA', 'STATUS', 'ESPECIALIDADE', 'GUT'])
    else:
        df = pd.DataFrame(data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Diretivas')
    
    output.seek(0)
    
    return StreamingResponse(
        output, 
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': 'attachment; filename="diretivas_tecnicas.xlsx"'}
    )

@app.get("/health")
async def health_check():
    return {"status": "ok"}
