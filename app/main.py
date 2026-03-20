import os
from fastapi import FastAPI, Request, UploadFile, File, Depends, Form, HTTPException, status, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
import io
import pandas as pd
from sqlmodel import Session, select, desc, or_, func
from datetime import datetime
from typing import List, Optional

from app.database import init_db, get_session, engine
from app.models import Diretiva, Aeronave, DiretivaAeronave
from app.services.csv_service import process_csv

from app.users import routes as user_routes
from app.users import actions as user_actions
from app.users import schemas as user_schemas
from app.users.routes import get_current_user, get_current_admin_user, get_optional_current_user, get_current_inspector_user
from app.users.models import User

app = FastAPI(title="SIGDT - Sistema de Gestão de Diretivas Técnicas")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Gatekeeper Password
GATEKEEPER_PASSWORD = "asdf1234"

def check_gatekeeper(request: Request):
    if request.cookies.get("gatekeeper_access") == "granted":
        return True
    return False

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

@app.get("/gatekeeper", response_class=HTMLResponse)
async def gatekeeper_page(request: Request):
    return templates.TemplateResponse("gatekeeper.html", {"request": request})

@app.post("/gatekeeper")
async def gatekeeper_verify(password: str = Form(...)):
    if password == GATEKEEPER_PASSWORD:
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(key="gatekeeper_access", value="granted", max_age=86400 * 7) # 1 day * 7
        return response
    return RedirectResponse(url="/gatekeeper?error=1", status_code=303)

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if not check_gatekeeper(request):
        return RedirectResponse(url="/gatekeeper")
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/", response_class=HTMLResponse)
async def read_root(
    request: Request, 
    session: Session = Depends(get_session), 
    current_user: Optional[User] = Depends(get_optional_current_user),
    page: int = 1
):
    if not check_gatekeeper(request):
        return RedirectResponse(url="/gatekeeper")
    
    per_page = 50
    offset = (page - 1) * per_page
    
    # Count total
    total_count = session.exec(select(func.count(DiretivaAeronave.id))).one()
    total_pages = (total_count + per_page - 1) // per_page

    statement = select(DiretivaAeronave).order_by(desc(DiretivaAeronave.gut)).offset(offset).limit(per_page)
    diretiva_links = session.exec(statement).all()
    
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "diretivas": diretiva_links,
        "current_user": current_user,
        "page": page,
        "total_pages": total_pages
    })

@app.post("/upload", dependencies=[Depends(get_current_admin_user)])
async def upload_csv(
    request: Request, 
    files: List[UploadFile] = File(...), 
    session: Session = Depends(get_session)
):
    for file in files:
        content = await file.read()
        process_csv(content.decode('utf-8'))
    return RedirectResponse(url="/", status_code=303)

@app.get("/directives", response_class=HTMLResponse)
async def list_directives(
    request: Request, 
    search: Optional[str] = None, 
    page: int = 1,
    session: Session = Depends(get_session)
):
    per_page = 50
    offset = (page - 1) * per_page
    
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
    
    # For simplicity in HTMX updates, we might not show pagination inside the partial yet
    # but let's at least respect the limit
    diretiva_links = session.exec(statement.offset(offset).limit(per_page)).all()
    
    return templates.TemplateResponse("partials/directives_table.html", {
        "request": request, 
        "diretivas": diretiva_links,
        "page": page
    })

@app.get("/directives/{diretiva_id}", response_class=HTMLResponse)
async def get_directive_details(
    request: Request,
    diretiva_id: int,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    if not check_gatekeeper(request):
        return RedirectResponse(url="/gatekeeper")
        
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
    link.data_status = datetime.utcnow()
    
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
    
    # Return to details page (which will then allow user to go back to dashboard)
    # Or return a script to trigger dashboard refresh if it was an HTMX request
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
    if not check_gatekeeper(request):
        return RedirectResponse(url="/gatekeeper")
    users = session.exec(select(User)).all()
    return templates.TemplateResponse("user_management.html", {"request": request, "users": users})

@app.get("/export/xlsx", dependencies=[Depends(get_current_inspector_user)])
async def export_xlsx(session: Session = Depends(get_session)):
    statement = select(DiretivaAeronave).join(Diretiva).join(Aeronave)
    links = session.exec(statement).all()
    
    data = []
    for link in links:
        data.append({
            'PN': link.diretiva.pn if hasattr(link.diretiva, 'pn') else '', 
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
