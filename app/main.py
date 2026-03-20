import os
from fastapi import FastAPI, Request, UploadFile, File, Depends, Form, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
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
    with Session(get_session().keywords['generator']()) as session:
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
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_inspector_user)
):
    diretiva = session.get(Diretiva, diretiva_id)
    if not diretiva:
        raise HTTPException(status_code=404, detail="Diretiva not found")
        
    diretiva.status = status
    diretiva.observacoes = observacoes
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

@app.get("/health")
async def health_check():
    return {"status": "ok"}
