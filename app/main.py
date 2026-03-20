import os
from fastapi import FastAPI, Request, UploadFile, File, Depends, Form, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
import io
import pandas as pd
from sqlmodel import Session, select, desc, or_

from app.database import init_db, get_session
from app.models import Diretiva
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
    from app.database import engine
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
    # Fetch first 100 directives ordered by GUT desc
    statement = select(Diretiva).order_by(desc(Diretiva.gut)).limit(100)
    diretivas = session.exec(statement).all()
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "diretivas": diretivas,
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
    statement = select(Diretiva).order_by(desc(Diretiva.gut))
    if search:
        search_filter = f"%{search}%"
        statement = statement.where(
            or_(
                Diretiva.sn_cjm.like(search_filter), 
                Diretiva.diretiva_tecnica.like(search_filter),
                Diretiva.matr.like(search_filter)
            )
        )
    
    diretivas = session.exec(statement.limit(100)).all()
    return templates.TemplateResponse("partials/directives_table.html", {
        "request": request, 
        "diretivas": diretivas
    })

@app.get("/directives/{diretiva_id}", response_class=HTMLResponse)
async def get_directive_details(
    request: Request,
    diretiva_id: int,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    diretiva = session.get(Diretiva, diretiva_id)
    if not diretiva:
        raise HTTPException(status_code=404, detail="Diretiva not found")
    
    return templates.TemplateResponse("directive_details.html", {
        "request": request,
        "diretiva": diretiva,
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
    diretiva = session.get(Diretiva, diretiva_id)
    if not diretiva:
        raise HTTPException(status_code=404, detail="Diretiva not found")
    
    # Check specialty permission for inspectors
    if current_user.role == 'inspector':
        if diretiva.especialidade and current_user.especialidade != diretiva.especialidade:
            # We can't easily return a nice error message with HTMX here without more setup, 
            # but let's at least block it and maybe return the same page with a flash message if we had one.
            # For now, let's just return the same page (it will look like it didn't save)
            # Or raise a 403.
            raise HTTPException(status_code=403, detail="Você não tem permissão para alterar diretivas desta especialidade.")

    # Update fields
    diretiva.status = status
    diretiva.observacoes = observacoes
    
    # Admin can update specialty
    if current_user.role == 'admin' and especialidade:
        diretiva.especialidade = especialidade

    # Handle PDF upload
    if pdf_file and pdf_file.filename:
        upload_dir = "app/static/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_ext = os.path.splitext(pdf_file.filename)[1]
        new_filename = f"diretiva_{diretiva_id}_{int(datetime.utcnow().timestamp())}{file_ext}"
        file_path = os.path.join(upload_dir, new_filename)
        
        with open(file_path, "wb") as buffer:
            content = await pdf_file.read()
            buffer.write(content)
        
        diretiva.pdf_path = new_filename

    session.add(diretiva)
    session.commit()
    session.refresh(diretiva)
    
    return templates.TemplateResponse("directive_details.html", {
        "request": request,
        "diretiva": diretiva,
        "current_user": current_user
    })

@app.post("/update-tendencia/{diretiva_id}", dependencies=[Depends(get_current_admin_user)])
async def update_tendencia(
    request: Request,
    diretiva_id: int,
    tendencia: int = Form(...),
    session: Session = Depends(get_session)
):
    diretiva = session.get(Diretiva, diretiva_id)
    if diretiva:
        diretiva.tendencia = tendencia
        diretiva.calculate_gut()
        session.add(diretiva)
        session.commit()
        session.refresh(diretiva)
    
    return templates.TemplateResponse("partials/directive_row.html", {
        "request": request,
        "diretiva": diretiva
    })

@app.get("/users/manage", response_class=HTMLResponse, dependencies=[Depends(get_current_admin_user)])
async def manage_users_page(request: Request, session: Session = Depends(get_session)):
    users = session.exec(select(User)).all()
    return templates.TemplateResponse("user_management.html", {"request": request, "users": users})

@app.get("/export/xlsx", dependencies=[Depends(get_current_inspector_user)])
async def export_xlsx(session: Session = Depends(get_session)):
    statement = select(Diretiva)
    diretivas = session.exec(statement).all()
    
    # Convert to list of dicts for pandas
    # Use d.dict() or similar to get all fields
    data = []
    for d in diretivas:
        d_dict = d.dict()
        # Ensure we only have relevant columns or rename them
        data.append(d_dict)
    
    if not data:
        df = pd.DataFrame(columns=['PN', 'CFF', 'MATRICULA', 'DIRETIVA_TECNICA', 'STATUS', 'CLA', 'CAT', 'OBJETIVO', 'ESPECIALIDADE'])
    else:
        df = pd.DataFrame(data)
        # Select and rename columns for a cleaner output
        cols_map = {
            'pn': 'PN',
            'cff': 'CFF',
            'matr': 'MATRICULA',
            'diretiva_tecnica': 'DIRETIVA_TECNICA',
            'status': 'STATUS',
            'cla': 'CLA',
            'cat': 'CAT',
            'objetivo': 'OBJETIVO',
            'especialidade': 'ESPECIALIDADE',
            'observacoes': 'OBSERVACOES'
        }
        df = df[list(cols_map.keys())].rename(columns=cols_map)
    
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
