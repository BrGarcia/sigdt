from fastapi import APIRouter, Request, Depends, HTTPException, Form, UploadFile, File, Query
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from sqlmodel import Session, select, desc, or_, func
from datetime import datetime, timezone
import os
import io
import pandas as pd
from typing import List, Optional

from app.database import get_session
from app.models import Aeronave, DiretivaTecnica, DiretivaItem, DiretivaItemAeronave
from app.core.config import check_gatekeeper
from app.core.templates import templates
from app.users.routes import get_current_admin_user, get_current_inspetor_user, get_current_user
from app.users.models import User
from app.services.csv_service import process_csv, sanitize_codigo

router = APIRouter(tags=["admin"])

MAX_CSV_SIZE = 50 * 1024 * 1024  # 50MB
REQUIRED_CSV_COLUMNS = {'MATR', 'SN', 'FADT', 'DIRETIVA TÉCNICA'}

@router.post("/upload", dependencies=[Depends(get_current_admin_user)])
async def upload_csv(
    request: Request, 
    files: List[UploadFile] = File(...), 
    session: Session = Depends(get_session)
):
    for file in files:
        content = await file.read()
        if len(content) > MAX_CSV_SIZE:
            raise HTTPException(status_code=400, detail=f"Arquivo '{file.filename}' excede o limite de 50MB.")
        try:
            preview_df = pd.read_csv(io.StringIO(content.decode('utf-8')), sep=';', nrows=0)
            missing = REQUIRED_CSV_COLUMNS - set(col.strip() for col in preview_df.columns)
            if missing:
                raise HTTPException(status_code=400, detail=f"CSV inválido. Colunas obrigatórias ausentes: {missing}")
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=400, detail=f"Não foi possível ler o arquivo '{file.filename}'. Verifique o formato CSV.")
        process_csv(content.decode('utf-8'), filename=file.filename, session=session)
    return RedirectResponse(url="/", status_code=303)

@router.post("/update-tendencia/{diretiva_id}", dependencies=[Depends(get_current_admin_user)])
async def update_tendencia(
    request: Request,
    diretiva_id: int,
    tendencia: int = Form(...),
    session: Session = Depends(get_session)
):
    link = session.get(DiretivaItemAeronave, diretiva_id)
    if link:
        link.tendencia = tendencia
        link.calculate_gut()
        session.add(link)
        session.commit()
        session.refresh(link)
    
    return templates.TemplateResponse(request=request, name="partials/directive_row.html", context={
        "diretiva": link
    })

@router.get("/users/manage", response_class=HTMLResponse, dependencies=[Depends(get_current_admin_user)])
async def manage_users_page(request: Request, session: Session = Depends(get_session), current_user: User = Depends(get_current_admin_user)):
    if not check_gatekeeper(request):
        return RedirectResponse(url="/gatekeeper")
    users = session.exec(select(User)).all()
    return templates.TemplateResponse(request=request, name="user_management.html", context={"users": users, "current_user": current_user})

@router.get("/export/xlsx", dependencies=[Depends(get_current_user)])
async def export_xlsx(
    session: Session = Depends(get_session),
    search: Optional[str] = None,
    status: Optional[str] = None,
    especialidade: List[str] = Query(None)
):
    from app.routers.directives import apply_filters
    statement = select(DiretivaItemAeronave).join(DiretivaItem).join(DiretivaTecnica).join(Aeronave).order_by(desc(DiretivaItemAeronave.gut))
    statement = apply_filters(statement, search, status, especialidade)
    
    links = session.exec(statement).all()
    
    def sanitize_formula(value):
        if isinstance(value, str) and value.startswith(('=', '+', '-', '@')):
            return "'" + value
        return value

    data = []
    for link in links:
        dt = link.diretiva_item.diretiva_tecnica
        item = link.diretiva_item
        data.append({
            'MATRICULA': sanitize_formula(link.aeronave.matricula),
            'NUMERO_SERIE': sanitize_formula(link.aeronave.numero_serie),
            'DIRETIVA_TECNICA': sanitize_formula(dt.codigo),
            'FADT': sanitize_formula(item.fadt),
            'STATUS': sanitize_formula(link.status),
            'CLA': sanitize_formula(dt.classe),
            'CAT': sanitize_formula(dt.categoria),
            'OBJETIVO': sanitize_formula(dt.objetivo),
            'ESPECIALIDADE': sanitize_formula(dt.especialidade),
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
    
    filename = "diretivas_tecnicas.xlsx"
    if search:
        import re
        safe_name = re.sub(r'[\\/*?:"<>|]', "", search).strip()
        filename = f"{safe_name}.xlsx" if safe_name else "busca.xlsx"
    elif status:
        filename = f"status_{status}.xlsx"
    elif especialidade:
        filename = f"{'-'.join(especialidade)}.xlsx"
    
    return StreamingResponse(
        output,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )

@router.get("/master-directives", response_class=HTMLResponse, dependencies=[Depends(get_current_inspetor_user)])
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
    
    statement = select(DiretivaTecnica).order_by(DiretivaTecnica.codigo)
    if search:
        search_filter = f"%{search}%"
        statement = statement.where(
            or_(
                DiretivaTecnica.codigo.like(search_filter), 
                DiretivaTecnica.objetivo.like(search_filter)
            )
        )
    
    count_statement = select(func.count()).select_from(statement.subquery())
    total_count = session.exec(count_statement).one()
    total_pages = (total_count + per_page - 1) // per_page
    
    master_directives = session.exec(statement.offset(offset).limit(per_page)).all()
    
    return templates.TemplateResponse(request=request, name="master_directives.html", context={
        "directives": master_directives,
        "current_user": current_user,
        "page": page,
        "total_pages": total_pages,
        "search": search
    })

@router.get("/master-directives/new", response_class=HTMLResponse, dependencies=[Depends(get_current_inspetor_user)])
async def get_master_directive_create_page(
    request: Request,
    current_user: User = Depends(get_current_inspetor_user)
):
    if not check_gatekeeper(request):
        return RedirectResponse(url="/gatekeeper")
    return templates.TemplateResponse(request=request, name="master_directive_create.html", context={
        "current_user": current_user
    })

@router.post("/master-directives/new", response_class=HTMLResponse, dependencies=[Depends(get_current_inspetor_user)])
async def create_master_directive(
    request: Request,
    codigo: str = Form(...),
    objetivo: str = Form(...),
    classe: str = Form("I"),
    categoria: str = Form("R"),
    especialidades: List[str] = Form([]),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_inspetor_user)
):
    codigo_simplificado = sanitize_codigo(codigo)
    
    # Verificar se ja existe
    existing = session.get(DiretivaTecnica, codigo_simplificado)
    if existing:
        raise HTTPException(status_code=400, detail=f"Diretiva com código {codigo_simplificado} já existe.")

    new_dt = DiretivaTecnica(
        codigo_simplificado=codigo_simplificado,
        codigo=codigo,
        objetivo=objetivo,
        classe=classe,
        categoria=categoria,
        especialidade=";".join(especialidades),
        updated_at=datetime.now(timezone.utc)
    )
    
    session.add(new_dt)
    session.commit()
    session.refresh(new_dt)
    
    return RedirectResponse(url="/master-directives", status_code=303)

@router.get("/master-directives/{codigo_simplificado}", response_class=HTMLResponse, dependencies=[Depends(get_current_inspetor_user)])
async def get_master_directive_edit(
    request: Request,
    codigo_simplificado: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_inspetor_user)
):
    master_dt = session.get(DiretivaTecnica, codigo_simplificado)
    if not master_dt:
        raise HTTPException(status_code=404, detail="Diretiva Master not found")
    
    return templates.TemplateResponse(request=request, name="master_directive_edit.html", context={
        "directive": master_dt,
        "current_user": current_user
    })

@router.post("/master-directives/{codigo_simplificado}", response_class=HTMLResponse, dependencies=[Depends(get_current_inspetor_user)])
async def update_master_directive(
    request: Request,
    codigo_simplificado: str,
    codigo: str = Form(...),
    objetivo: str = Form(...),
    classe: str = Form(...),
    categoria: str = Form(...),
    especialidades: List[str] = Form([]),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_inspetor_user)
):
    master_dt = session.get(DiretivaTecnica, codigo_simplificado)
    if not master_dt:
        raise HTTPException(status_code=404, detail="Diretiva Master not found")
    
    master_dt.codigo = codigo
    master_dt.objetivo = objetivo
    master_dt.classe = classe
    master_dt.categoria = categoria
    master_dt.especialidade = ";".join(especialidades)
    master_dt.updated_at = datetime.now(timezone.utc)
    
    session.add(master_dt)
    session.commit()
    session.refresh(master_dt)
    
    for item in master_dt.items:
        for link in item.aeronave_links:
            link.calculate_gut()
            session.add(link)
    session.commit()
    
    return RedirectResponse(url="/master-directives", status_code=303)
