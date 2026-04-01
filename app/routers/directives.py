from fastapi import APIRouter, Request, Depends, HTTPException, Form, UploadFile, File, Query
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from sqlmodel import Session, select, desc, or_, func
from datetime import datetime, timezone
import os
from typing import List, Optional

from app.database import get_session
from app.models import Aeronave, DiretivaTecnica, DiretivaItem, DiretivaItemAeronave, StatusDiretiva
from app.core.config import check_gatekeeper
from app.core.templates import templates
from app.users.routes import get_optional_current_user, get_current_inspetor_user
from app.users.models import User
from app.services.pdf_parser import parse_at_pdf

router = APIRouter(tags=["directives"])

def apply_filters(statement, search: Optional[str] = None, status: Optional[str] = None, especialidade: List[str] = []):
    if search:
        search_filter = f"%{search}%"
        statement = statement.where(
            or_(
                Aeronave.numero_serie.like(search_filter), 
                Aeronave.matricula.like(search_filter),
                DiretivaTecnica.codigo.like(search_filter),
                DiretivaItem.fadt.like(search_filter)
            )
        )
        
    if status:
        statement = statement.where(DiretivaItemAeronave.status == status)
        
    if especialidade:
        conditions = [DiretivaTecnica.especialidade.like(f"%{esp}%") for esp in especialidade if esp]
        if conditions:
            statement = statement.where(or_(*conditions))
    return statement

def has_specialty_permission(user: User, directive_specs_string: str) -> bool:
    if user.role == 'admin':
        return True
    
    mapping = {
        "BMA": ["MOT", "CEL", "HID"],
        "BET": ["ELT"],
        "BEI": ["ELE"],
        "BEP": ["EST"],
        "BEV": ["EQV"],
        "BMB": ["ARM"]
    }
    
    inspector_spec = user.especialidade
    if not inspector_spec:
        return False
        
    allowed_areas = mapping.get(inspector_spec, [])
    directive_specs = [s.strip().upper() for s in directive_specs_string.split(';')] if directive_specs_string else []
    
    if "TODAS" in directive_specs:
        return True
        
    return any(spec in allowed_areas for spec in directive_specs)

from sqlalchemy.orm import selectinload

@router.get("/", response_class=HTMLResponse)
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
    
    total_count = session.exec(select(func.count(DiretivaItemAeronave.id))).one()
    total_pages = max(1, (total_count + per_page - 1) // per_page)

    # OTIMIZAÇÃO FASE 3: Eager Loading dos relacionamentos para evitar N+1
    statement = (
        select(DiretivaItemAeronave)
        .options(
            selectinload(DiretivaItemAeronave.aeronave),
            selectinload(DiretivaItemAeronave.diretiva_item).selectinload(DiretivaItem.diretiva_tecnica)
        )
        .order_by(desc(DiretivaItemAeronave.gut))
        .offset(offset)
        .limit(per_page)
    )
    diretiva_links = session.exec(statement).all()
    
    return templates.TemplateResponse(request=request, name="index.html", context={
        "diretivas": diretiva_links,
        "current_user": current_user,
        "page": page,
        "total_pages": total_pages
    })

@router.get("/directives", response_class=HTMLResponse)
async def list_directives(
    request: Request, 
    search: Optional[str] = None, 
    status: Optional[str] = None,
    especialidade: List[str] = Query(None),
    page: int = 1,
    session: Session = Depends(get_session)
):
    if not check_gatekeeper(request):
        return HTMLResponse(status_code=403, content="<p>Acesso negado.</p>")
    per_page = 50
    offset = (page - 1) * per_page
    
    # OTIMIZAÇÃO FASE 3: Eager Loading dos relacionamentos para evitar N+1
    statement = (
        select(DiretivaItemAeronave)
        .join(DiretivaItem)
        .join(DiretivaTecnica)
        .join(Aeronave)
        .options(
            selectinload(DiretivaItemAeronave.aeronave),
            selectinload(DiretivaItemAeronave.diretiva_item).selectinload(DiretivaItem.diretiva_tecnica)
        )
        .order_by(desc(DiretivaItemAeronave.gut))
    )
    statement = apply_filters(statement, search, status, especialidade)
    
    count_statement = select(func.count()).select_from(statement.subquery())
    total_count = session.exec(count_statement).one()
    total_pages = max(1, (total_count + per_page - 1) // per_page)
    
    diretiva_links = session.exec(statement.offset(offset).limit(per_page)).all()
    
    return templates.TemplateResponse(request=request, name="partials/directives_table.html", context={
        "diretivas": diretiva_links,
        "page": page,
        "total_pages": total_pages
    })

@router.get("/directives/{diretiva_id}", response_class=HTMLResponse)
async def get_directive_details(
    request: Request,
    diretiva_id: int,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    if not check_gatekeeper(request):
        return RedirectResponse(url="/gatekeeper")
        
    link = session.get(DiretivaItemAeronave, diretiva_id)
    if not link:
        raise HTTPException(status_code=404, detail="Vínculo de Diretiva not found")
    
    return templates.TemplateResponse(request=request, name="directive_details.html", context={
        "diretiva": link,
        "current_user": current_user
    })

@router.post("/directives/{diretiva_id}", response_class=HTMLResponse, dependencies=[Depends(get_current_inspetor_user)])
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
    link = session.get(DiretivaItemAeronave, diretiva_id)
    if not link:
        raise HTTPException(status_code=404, detail="Vínculo de Diretiva not found")
    
    if not has_specialty_permission(current_user, link.diretiva_item.diretiva_tecnica.especialidade):
        raise HTTPException(status_code=403, detail="Você não tem permissão para alterar diretivas desta especialidade.")

    if status not in [s.value for s in StatusDiretiva]:
        raise HTTPException(status_code=400, detail=f"Status inválido: {status}")

    link.status = status
    link.observacao = observacoes
    link.data_status = datetime.now(timezone.utc)
    link.origem_status = "manual"

    if pdf_file and pdf_file.filename:
        MAX_FILE_SIZE = 10 * 1024 * 1024 # 10MB
        content = await pdf_file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="O arquivo é muito grande. O limite máximo é 10MB.")
        
        if not content.startswith(b'%PDF-'):
            raise HTTPException(status_code=400, detail="Arquivo inválido. Apenas arquivos PDF reais são permitidos.")
        
        upload_dir = "app/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        new_filename = f"diretiva_link_{diretiva_id}_{int(datetime.now(timezone.utc).timestamp())}.pdf"
        file_path = os.path.join(upload_dir, new_filename)
        
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        link.pdf_path = new_filename

        parsed_data = parse_at_pdf(file_path)
        if "error" not in parsed_data:
            extra_info = "\n--- DADOS EXTRAÍDOS AUTOMATICAMENTE (Ficha AT) ---\n"
            important_keys = ["Ficha A.T.", "PN", "Nomenclatura", "SN", "Situação"]
            for key in important_keys:
                if key in parsed_data:
                    extra_info += f"{key}: {parsed_data.pop(key)}\n"
            
            extra_info += "\n[DADOS ADICIONAIS]\n"
            for k, v in list(parsed_data.items()):
                if k not in ["Serviço Solicitado", "Parecer da Engenharia"]:
                    extra_info += f"{k}: {v}\n"
                    parsed_data.pop(k, None)

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
    
    return templates.TemplateResponse(request=request, name="directive_details.html", context={
        "diretiva": link,
        "current_user": current_user
    })

@router.delete("/directives/{diretiva_id}/attachment", dependencies=[Depends(get_current_inspetor_user)])
async def delete_attachment(
    request: Request,
    diretiva_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_inspetor_user)
):
    link = session.get(DiretivaItemAeronave, diretiva_id)
    if not link:
        raise HTTPException(status_code=404, detail="Vínculo de Diretiva not found")
    
    if not has_specialty_permission(current_user, link.diretiva_item.diretiva_tecnica.especialidade):
        raise HTTPException(status_code=403, detail="Você não tem permissão para alterar diretivas desta especialidade.")

    if link.pdf_path:
        file_path = os.path.join("app/uploads", link.pdf_path)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
        
        link.pdf_path = None
        session.add(link)
        session.commit()
        session.refresh(link)
    
    return templates.TemplateResponse(request=request, name="directive_details.html", context={
        "diretiva": link,
        "current_user": current_user
    })

@router.get("/uploads/{filename}")
async def get_upload(
    request: Request, 
    filename: str, 
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    if not check_gatekeeper(request):
        raise HTTPException(status_code=403, detail="Acesso negado (Gatekeeper)")

    if not current_user:
        raise HTTPException(status_code=401, detail="Autenticação exigida para visualizar anexos")

    file_path = os.path.join("app/uploads", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

    return FileResponse(file_path)

