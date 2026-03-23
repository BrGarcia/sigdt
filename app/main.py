from dotenv import load_dotenv
load_dotenv()

import os
from fastapi import FastAPI, Request, UploadFile, File, Depends, Form, HTTPException, status, Response, Query
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
import io
import pandas as pd
from sqlmodel import Session, select, desc, or_, func
from datetime import datetime
from typing import List, Optional

from app.database import init_db, get_session, engine
from app.models import Diretiva, Aeronave, DiretivaAeronave, SecurityLog
from app.services.csv_service import process_csv
from app.services.pdf_parser import parse_at_pdf
from app.constants import Especialidade
from app.logging_config import setup_logging, get_logger

# Initialize Logging
setup_logging()
logger = get_logger("SIGDT")

from app.users import routes as user_routes
from app.users import actions as user_actions
from app.users import schemas as user_schemas
from app.users.routes import get_current_user, get_current_admin_user, get_optional_current_user, get_current_inspetor_user
from app.users.models import User

from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.csrf import CSRFMiddleware

app = FastAPI(title="SIGDT - Sistema de Gestão de Diretivas Técnicas")

# Secret Key for CSRF and Sessions
SECRET_KEY = os.getenv("SECRET_KEY", "sigdt-secret-key-change-it-in-prod")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.add_middleware(CSRFMiddleware, secret_key=SECRET_KEY)

# Templates
templates = Jinja2Templates(directory="app/templates")

# Context Processor for Templates
@app.middleware("http")
async def add_context_to_templates(request: Request, call_next):
    # This is a bit tricky with FastAPI/Jinja2Templates as they don't have a 
    # native "context processor" like Flask. We'll use a different approach 
    # by adding it to the templates.env.globals.
    return await call_next(request)

templates.env.globals['Especialidade'] = Especialidade

def format_especialidade(esp_string: str):
    if not esp_string:
        return []
    
    parts = [p.strip().upper() for p in esp_string.split(';')]
    codes = set()
    for p in parts:
        if not p: continue
        codes.add(Especialidade.normalize(p))
            
    core = set(Especialidade.list_codes())
    if core.issubset(codes) or 'TODAS' in codes:
        return ['TODAS']
        
    return sorted(list(codes))

def format_especialidade_label(esp_string: str):
    codes = format_especialidade(esp_string)
    if not codes:
        return "Não definida"
    if codes == ['TODAS']:
        return "TODAS"
    labels = [Especialidade.get_label(c) for c in codes]
    return ", ".join(labels)

templates.env.filters['format_especialidade'] = format_especialidade
templates.env.filters['format_especialidade_label'] = format_especialidade_label

# Gatekeeper Password
GATEKEEPER_PASSWORD = os.getenv("GATEKEEPER_PASSWORD")
if not GATEKEEPER_PASSWORD:
    raise ValueError("Variável de ambiente GATEKEEPER_PASSWORD é obrigatória.")

# Simple Persistent Rate Limiting
def is_rate_limited(key: str, event_type: str, max_attempts: int = 5, window_seconds: int = 60):
    from datetime import timedelta
    now = datetime.now(datetime.timezone.utc)
    window_start = now - timedelta(seconds=window_seconds)
    
    with Session(engine) as session:
        statement = select(func.count(SecurityLog.id)).where(
            SecurityLog.key == key,
            SecurityLog.event_type == event_type,
            SecurityLog.timestamp >= window_start,
            SecurityLog.success == False
        )
        count = session.exec(statement).one()
        return count >= max_attempts

def log_security_event(key: str, event_type: str, success: bool, request: Request):
    logger.warning(f"Security Event: {event_type} - Key: {key} - Success: {success} - IP: {request.client.host}")
    with Session(engine) as session:
        log = SecurityLog(
            key=key,
            event_type=event_type,
            success=success,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        session.add(log)
        session.commit()

def check_gatekeeper(request: Request):
    if request.cookies.get("gatekeeper_access") == "granted":
        return True
    return False

@app.on_event("startup")
def on_startup():
    logger.info("Iniciando aplicação SIGDT...")
    os.makedirs("app/static", exist_ok=True)
    init_db()
    with Session(engine) as session:
        admin_user = user_actions.get_user(session, "admin")
        admin_pwd = os.getenv("ADMIN_PASSWORD")
        if not admin_pwd:
            logger.error("ADMIN_PASSWORD não configurada!")
            raise ValueError("Variável de ambiente ADMIN_PASSWORD é obrigatória no startup.")
        if not admin_user:
            logger.info("Criando usuário administrador padrão...")
            user_in = user_schemas.UserCreate(username="admin", email="admin@example.com", password=admin_pwd)
            admin_user = user_actions.create_user(session, user_in, role="admin")
        else:
            # Update admin password if ENV is different from current hash (always updates to match ENV for safety)
            from app.users import security as user_security
            admin_user.hashed_password = user_security.get_password_hash(admin_pwd)
            admin_user.role = "admin"
            session.add(admin_user)
            session.commit()
    logger.info("Startup concluído com sucesso.")


# Static files and user routes
if not os.path.exists("app/static"):
    os.makedirs("app/static", exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(user_routes.router)

@app.get("/gatekeeper", response_class=HTMLResponse)
async def gatekeeper_page(request: Request):
    return templates.TemplateResponse("gatekeeper.html", {"request": request})

@app.post("/gatekeeper")
async def gatekeeper_verify(request: Request, password: str = Form(...)):
    client_ip = request.client.host
    key = f"gatekeeper_{client_ip}"
    
    if is_rate_limited(key, "gatekeeper_attempt"):
        log_security_event(key, "gatekeeper_attempt_blocked", False, request)
        raise HTTPException(status_code=429, detail="Muitas tentativas. Tente novamente em 1 minuto.")

    if password == GATEKEEPER_PASSWORD:
        log_security_event(key, "gatekeeper_attempt", True, request)
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(
            key="gatekeeper_access", 
            value="granted", 
            max_age=86400 * 7,
            httponly=True,
            samesite="lax",
            secure=os.getenv("ENVIRONMENT") == "production"
        )
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

MAX_CSV_SIZE = 50 * 1024 * 1024  # 50MB
REQUIRED_CSV_COLUMNS = {'MATR', 'SN', 'FADT', 'DIRETIVA TÉCNICA'}

@app.post("/upload", dependencies=[Depends(get_current_admin_user)])
async def upload_csv(
    request: Request, 
    files: List[UploadFile] = File(...), 
    session: Session = Depends(get_session)
):
    for file in files:
        content = await file.read()
        # Item 8: Validar tamanho máximo
        if len(content) > MAX_CSV_SIZE:
            raise HTTPException(status_code=400, detail=f"Arquivo '{file.filename}' excede o limite de 50MB.")
        # Item 8: Validar colunas obrigatórias
        import io as _io
        import pandas as _pd
        try:
            preview_df = _pd.read_csv(_io.StringIO(content.decode('utf-8')), sep=';', nrows=0)
            missing = REQUIRED_CSV_COLUMNS - set(col.strip() for col in preview_df.columns)
            if missing:
                raise HTTPException(status_code=400, detail=f"CSV inválido. Colunas obrigatórias ausentes: {missing}")
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=400, detail=f"Não foi possível ler o arquivo '{file.filename}'. Verifique o formato CSV.")
        process_csv(content.decode('utf-8'))
    return RedirectResponse(url="/", status_code=303)

@app.get("/directives", response_class=HTMLResponse)
async def list_directives(
    request: Request, 
    search: Optional[str] = None, 
    status: Optional[str] = None,
    especialidade: List[str] = Query(None),
    page: int = 1,
    session: Session = Depends(get_session)
):
    # Item 6: Proteger rota HTMX com gatekeeper
    if not check_gatekeeper(request):
        return HTMLResponse(status_code=403, content="<p>Acesso negado.</p>")
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
        
    if status:
        statement = statement.where(DiretivaAeronave.status == status)
        
    if especialidade:
        conditions = [Diretiva.especialidade.like(f"%{esp}%") for esp in especialidade if esp]
        if conditions:
            statement = statement.where(or_(*conditions))
    
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

@app.post("/directives/{diretiva_id}", response_class=HTMLResponse, dependencies=[Depends(get_current_inspetor_user)])
async def update_directive_details(
    request: Request,
    diretiva_id: int,
    status: str = Form(...),
    observacoes: str = Form(...),
    especialidades: List[str] = Form([]),
    pdf_file: Optional[UploadFile] = File(None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_inspetor_user)
):
    link = session.get(DiretivaAeronave, diretiva_id)
    if not link:
        raise HTTPException(status_code=404, detail="Vínculo de Diretiva not found")
    
    # Check specialty permission for inspetors
    if current_user.role == 'inspetor':
        allowed_specs = link.diretiva.especialidade.split(';') if link.diretiva.especialidade else []
        if allowed_specs and current_user.especialidade not in allowed_specs:
            raise HTTPException(status_code=403, detail="Você não tem permissão para alterar diretivas desta especialidade.")

    # Update fields
    link.status = status
    link.observacao = observacoes
    link.data_status = datetime.now(datetime.timezone.utc)  # Item 13: datetime moderno

    # Handle PDF upload
    if pdf_file and pdf_file.filename:
        # 10MB Limit check
        MAX_FILE_SIZE = 10 * 1024 * 1024 # 10MB
        content = await pdf_file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="O arquivo é muito grande. O limite máximo é 10MB.")
        
        # Magic Number Check (PDF signature: %PDF-)
        if not content.startswith(b'%PDF-'):
            raise HTTPException(status_code=400, detail="Arquivo inválido. Apenas arquivos PDF reais são permitidos.")
        
        upload_dir = "app/static/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Item 9: Forçar extensão .pdf independentemente do nome original
        new_filename = f"diretiva_link_{diretiva_id}_{int(datetime.now(datetime.timezone.utc).timestamp())}.pdf"
        file_path = os.path.join(upload_dir, new_filename)
        
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        link.pdf_path = new_filename

        parsed_data = parse_at_pdf(file_path)
        if "error" not in parsed_data:
            extra_info = "\n--- DADOS EXTRAÍDOS AUTOMATICAMENTE (Ficha AT) ---\n"
            
            # Ordem prioritária de exibição na caixa de observação (só para ficar bonito)
            important_keys = ["Ficha A.T.", "PN", "Nomenclatura", "SN", "Situação"]
            for key in important_keys:
                if key in parsed_data:
                    extra_info += f"{key}: {parsed_data.pop(key)}\n"
            
            # Adicionar o restante dos dados meta
            extra_info += "\n[DADOS ADICIONAIS]\n"
            for k, v in list(parsed_data.items()):
                if k not in ["Serviço Solicitado", "Parecer da Engenharia"]:
                    extra_info += f"{k}: {v}\n"
                    parsed_data.pop(k, None)

            # E por fim colocar os blocos grandes
            extra_info += f"\n[SERVIÇO SOLICITADO]\n{parsed_data.get('Serviço Solicitado', 'N/A')}\n"
            extra_info += f"\n[PARECER DA ENGENHARIA]\n{parsed_data.get('Parecer da Engenharia', 'N/A')}\n"
            extra_info += "--------------------------------------------------\n"

            if link.observacao:
                if "--- DADOS EXTRAÍDOS AUTOMATICAMENTE" not in link.observacao:
                    link.observacao = link.observacao.rstrip() + "\n" + extra_info
            else:
                link.observacao = extra_info.strip()

    session.add(link)
    session.commit()
    session.refresh(link)
    
    return templates.TemplateResponse("directive_details.html", {
        "request": request,
        "diretiva": link,
        "current_user": current_user
    })

@app.delete("/directives/{diretiva_id}/attachment", dependencies=[Depends(get_current_inspetor_user)])
async def delete_attachment(
    request: Request,
    diretiva_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_inspetor_user)
):
    link = session.get(DiretivaAeronave, diretiva_id)
    if not link:
        raise HTTPException(status_code=404, detail="Vínculo de Diretiva not found")
    
    # Check specialty permission for inspetors
    if current_user.role == 'inspetor':
        allowed_specs = link.diretiva.especialidade.split(';') if link.diretiva.especialidade else []
        if allowed_specs and current_user.especialidade not in allowed_specs:
            raise HTTPException(status_code=403, detail="Você não tem permissão para alterar diretivas desta especialidade.")

    if link.pdf_path:
        file_path = os.path.join("app/static/uploads", link.pdf_path)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass # Continue even if file removal fails
        
        link.pdf_path = None
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
async def manage_users_page(request: Request, session: Session = Depends(get_session), current_user: User = Depends(get_current_admin_user)):
    if not check_gatekeeper(request):
        return RedirectResponse(url="/gatekeeper")
    users = session.exec(select(User)).all()
    return templates.TemplateResponse("user_management.html", {"request": request, "users": users, "current_user": current_user})

@app.get("/export/xlsx", dependencies=[Depends(get_current_user)])
async def export_xlsx(session: Session = Depends(get_session)):
    statement = select(DiretivaAeronave).join(Diretiva).join(Aeronave)
    links = session.exec(statement).all()
    
    def sanitize_formula(value):
        if isinstance(value, str) and value.startswith(('=', '+', '-', '@')):
            return "'" + value
        return value

    data = []
    for link in links:
        data.append({
            # Item 11: Campo 'pn' removido do modelo na V2 — coluna removida do export
            'MATRICULA': sanitize_formula(link.aeronave.matricula),
            'NUMERO_SERIE': sanitize_formula(link.aeronave.numero_serie),
            'DIRETIVA_TECNICA': sanitize_formula(link.diretiva.codigo_diretiva),
            'FADT': sanitize_formula(link.diretiva.fadt),
            'STATUS': sanitize_formula(link.status),
            'CLA': sanitize_formula(link.diretiva.classe),
            'CAT': sanitize_formula(link.diretiva.categoria),
            'ESPECIALIDADE': sanitize_formula(link.diretiva.especialidade),
            'OBSERVACOES': sanitize_formula(link.observacao),
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

@app.get("/master-directives", response_class=HTMLResponse, dependencies=[Depends(get_current_inspetor_user)])
async def list_master_directives(
    request: Request, 
    search: Optional[str] = None, 
    page: int = 1,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_inspetor_user)
):
    if not check_gatekeeper(request):
        return RedirectResponse(url="/gatekeeper")
        
    per_page = 50
    offset = (page - 1) * per_page
    
    statement = select(Diretiva).order_by(Diretiva.codigo_diretiva)
    if search:
        search_filter = f"%{search}%"
        statement = statement.where(
            or_(
                Diretiva.codigo_diretiva.like(search_filter), 
                Diretiva.fadt.like(search_filter),
                Diretiva.objetivo.like(search_filter)
            )
        )
    
    # Item 12: Contagem eficiente com subquery ao invés de carregar tudo na memória
    count_statement = select(func.count()).select_from(statement.subquery())
    total_count = session.exec(count_statement).one()
    total_pages = (total_count + per_page - 1) // per_page
    
    master_directives = session.exec(statement.offset(offset).limit(per_page)).all()
    
    return templates.TemplateResponse("master_directives.html", {
        "request": request, 
        "directives": master_directives,
        "current_user": current_user,
        "page": page,
        "total_pages": total_pages,
        "search": search
    })

@app.get("/master-directives/{id}", response_class=HTMLResponse, dependencies=[Depends(get_current_inspetor_user)])
async def get_master_directive_edit(
    request: Request,
    id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_inspetor_user)
):
    master_dt = session.get(Diretiva, id)
    if not master_dt:
        raise HTTPException(status_code=404, detail="Diretiva Master not found")
    
    return templates.TemplateResponse("master_directive_edit.html", {
        "request": request,
        "directive": master_dt,
        "current_user": current_user
    })

@app.post("/master-directives/{id}", response_class=HTMLResponse, dependencies=[Depends(get_current_inspetor_user)])
async def update_master_directive(
    request: Request,
    id: int,
    codigo_diretiva: str = Form(...),
    objetivo: str = Form(...),
    classe: str = Form(...),
    categoria: str = Form(...),
    especialidades: List[str] = Form([]),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_inspetor_user)
):
    master_dt = session.get(Diretiva, id)
    if not master_dt:
        raise HTTPException(status_code=404, detail="Diretiva Master not found")
    
    # Update master data
    master_dt.codigo_diretiva = codigo_diretiva
    master_dt.objetivo = objetivo
    master_dt.classe = classe
    master_dt.categoria = categoria
    master_dt.especialidade = ";".join(especialidades)
    
    session.add(master_dt)
    session.commit()
    session.refresh(master_dt)
    
    # Recalculate GUT for all aircraft links using this master DT
    statement = select(DiretivaAeronave).where(DiretivaAeronave.diretiva_id == master_dt.id)
    links = session.exec(statement).all()
    for link in links:
        link.calculate_gut()
        session.add(link)
    session.commit()
    
    return RedirectResponse(url="/master-directives", status_code=303)

@app.get("/directives/new", response_class=HTMLResponse, dependencies=[Depends(get_current_inspetor_user)])
async def new_directive_page(request: Request, current_user: User = Depends(get_current_inspetor_user)):
    return templates.TemplateResponse("directive_new.html", {"request": request, "current_user": current_user})

@app.post("/directives/new", dependencies=[Depends(get_current_inspetor_user)])
async def create_new_directive(
    request: Request,
    matricula: str = Form(...),
    numero_serie: str = Form(...),
    fadt: str = Form(...),
    codigo_diretiva: str = Form(...),
    objetivo: str = Form(...),
    classe: str = Form(...),
    categoria: str = Form(...),
    especialidades: List[str] = Form([]),
    status: str = Form(...),
    tendencia: int = Form(...),
    observacao: Optional[str] = Form(None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_inspetor_user)
):
    logger.info(f"Usuário {current_user.username} iniciando cadastro manual de diretiva {fadt} para aeronave {matricula}")
    
    # 1. Aeronave (Upsert)
    matricula = matricula.strip().upper()
    statement_aero = select(Aeronave).where(Aeronave.matricula == matricula)
    aeronave = session.exec(statement_aero).first()
    
    if not aeronave:
        aeronave = Aeronave(matricula=matricula, numero_serie=numero_serie.strip().upper())
        session.add(aeronave)
        session.flush()
        logger.info(f"Nova aeronave cadastrada: {matricula}")
    
    # 2. Diretiva Master (Upsert)
    fadt = fadt.strip().upper()
    statement_dt = select(Diretiva).where(Diretiva.fadt == fadt)
    master_dt = session.exec(statement_dt).first()
    
    dt_data = {
        "codigo_diretiva": codigo_diretiva.strip(),
        "fadt": fadt,
        "objetivo": objetivo.strip(),
        "classe": classe,
        "categoria": categoria,
        "especialidade": ";".join(especialidades)
    }
    
    if not master_dt:
        master_dt = Diretiva(**dt_data)
        session.add(master_dt)
        session.flush()
        logger.info(f"Nova diretiva master cadastrada: {fadt}")
    else:
        # Update existing master data if needed
        for key, value in dt_data.items():
            setattr(master_dt, key, value)
        session.add(master_dt)

    # 3. Vínculo (Link)
    statement_link = select(DiretivaAeronave).where(
        DiretivaAeronave.aeronave_id == aeronave.id,
        DiretivaAeronave.diretiva_id == master_dt.id
    )
    link = session.exec(statement_link).first()
    
    if not link:
        link = DiretivaAeronave(
            aeronave_id=aeronave.id,
            diretiva_id=master_dt.id,
            status=status,
            tendencia=tendencia,
            observacao=observacao
        )
        logger.info(f"Criando novo vínculo entre {matricula} e {fadt}")
    else:
        # Update existing link
        link.status = status
        link.tendencia = tendencia
        link.observacao = observacao
        logger.info(f"Atualizando vínculo existente entre {matricula} e {fadt}")
    
    link.data_status = datetime.now(datetime.timezone.utc)
    link.calculate_gut()
    
    session.add(link)
    session.commit()
    
    logger.info(f"Cadastro manual concluído com sucesso: {fadt} -> {matricula}")
    return RedirectResponse(url="/", status_code=303)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
