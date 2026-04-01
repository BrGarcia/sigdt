from fastapi.testclient import TestClient
import pytest
from sqlmodel import Session, select
from app.models import Aeronave, DiretivaTecnica, DiretivaItem, DiretivaItemAeronave
from app.users.models import User
from app.users import security
import uuid
import os

def get_csrf_token(response):
    return response.cookies.get("csrftoken")

def test_system_integrity(client: TestClient, session: Session):
    print("\n--- INICIANDO TESTES DE INTEGRIDADE ---")
    
    # 1. Testar Gatekeeper (Proteção Inicial)
    print("1. Testando Gatekeeper...")
    response = client.get("/gatekeeper", follow_redirects=True)
    csrf_token = get_csrf_token(response)
    
    response = client.get("/", follow_redirects=False)
    print(f"   Status recebido: {response.status_code}")
    assert response.status_code in [303, 307, 302]
    assert "/gatekeeper" in response.headers["location"]
    
    response = client.post("/gatekeeper", data={"password": "wrong"}, headers={"x-csrftoken": csrf_token}, follow_redirects=True)
    assert "error=1" in str(response.url)
    
    gatekeeper_password = os.getenv("GATEKEEPER_PASSWORD")
    response = client.post("/gatekeeper", data={"password": gatekeeper_password}, headers={"x-csrftoken": csrf_token}, follow_redirects=True)
    assert response.status_code == 200
    assert response.url.path == "/"
    print("   [OK] Gatekeeper protegendo e aceitando senha correta.")

    # Update CSRF token after login
    csrf_token = get_csrf_token(response)

    # 2. Testar Dashboard (Colunas e Conteúdo)
    print("2. Testando Dashboard...")
    response = client.get("/")
    assert response.status_code == 200
    assert "MATRÍCULA" in response.text
    assert "DIRETIVA TÉCNICA" in response.text
    print("   [OK] Colunas do Dashboard atualizadas.")

    # 3. Testar Visibilidade de PDF para Usuário Não Logado
    print("3. Testando visibilidade de PDF (Não Logado)...")
    uid = str(uuid.uuid4())[:8]
    
    a = Aeronave(matricula=f"TEST-{uid}", numero_serie=f"SN-{uid}")
    session.add(a)
    session.flush()
    
    dt = DiretivaTecnica(codigo_simplificado=f"DT{uid}", codigo=f"DT-{uid}", objetivo="TEST PDF VISIBILITY", especialidade="ELT")
    session.add(dt)
    session.flush()
    
    item = DiretivaItem(diretiva_tecnica_id=dt.codigo_simplificado, fadt=f"FADT-{uid}", chave_item=f"DT{uid}|FADT-{uid}||", descricao_item="TEST ITEM")
    session.add(item)
    session.flush()
    
    link = DiretivaItemAeronave(aeronave_id=a.id, diretiva_item_id=item.id, status="Pendente", pdf_path="test_file.pdf")
    session.add(link)
    session.commit()
    session.refresh(link)
    link_id = link.id

    response = client.get(f"/directives/{link_id}")
    assert response.status_code == 200
    assert "Visualizar Documento (PDF)" in response.text
    print("   [OK] PDF visível para todos.")

    # 4. Testar Restrição de Especialidade (Inspetor)
    print("4. Testando restrição de especialidade (Inspetor)...")
    user_in = User(username=f"insp_{uid}", email=f"insp_{uid}@test.com", hashed_password="hashed", role="inspetor", especialidade="BEI")
    session.add(user_in)
    session.commit()
    
    token = security.create_access_token(data={"sub": f"insp_{uid}"})
    client.cookies.set("access_token", token)
    
    # CSRF token should be updated
    response = client.get("/")
    csrf_token = get_csrf_token(response)
    
    response = client.post(f"/directives/{link_id}", data={"status": "Concluída", "observacoes": "tentativa", "csrftoken": csrf_token})
    assert response.status_code == 403
    print("   [OK] Inspetor impedido de editar especialidade diferente.")

    print("--- TODOS OS TESTES PASSARAM COM SUCESSO ---")
