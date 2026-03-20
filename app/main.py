import os
from fastapi import FastAPI, Request, UploadFile, File, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session, select, desc
from app.database import init_db, get_session
from app.models import Diretiva
from app.services.csv_service import process_csv
from typing import Optional

app = FastAPI(title="SIGDT - Sistema de Gestão de Diretivas Técnicas")

# Templates
templates = Jinja2Templates(directory="app/templates")

@app.on_event("startup")
def on_startup():
    os.makedirs("app/static", exist_ok=True)
    init_db()

# Static files
if not os.path.exists("app/static"):
    os.makedirs("app/static", exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, session: Session = Depends(get_session)):
    # Fetch first 100 directives ordered by GUT desc
    statement = select(Diretiva).order_by(desc(Diretiva.gut)).limit(100)
    diretivas = session.exec(statement).all()
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "diretivas": diretivas,
        "message": "Dashboard de Diretivas Técnicas"
    })

@app.post("/upload")
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
            (Diretiva.sn_cjm.like(search_filter)) | 
            (Diretiva.diretiva_tecnica.like(search_filter)) |
            (Diretiva.matr.like(search_filter))
        )
    
    diretivas = session.exec(statement.limit(100)).all()
    return templates.TemplateResponse("partials/directives_table.html", {
        "request": request, 
        "diretivas": diretivas
    })

@app.post("/update-tendencia/{diretiva_id}")
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

@app.get("/health")
async def health_check():
    return {"status": "ok"}
