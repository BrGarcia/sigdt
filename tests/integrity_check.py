from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db, engine
from sqlmodel import Session, select
from app.models import Aeronave, DiretivaTecnica, DiretivaItem, DiretivaItemAeronave
from app.users.models import User
from app.users import security
import uuid

client = TestClient(app)

def test_system_integrity():
    print("\n--- INICIANDO TESTES DE INTEGRIDADE ---")
    init_db()
    
    # 1. Testar Gatekeeper (Proteção Inicial)
    print("1. Testando Gatekeeper...")
    response = client.get("/", follow_redirects=False)
    print(f"   Status recebido: {response.status_code}")
    if response.status_code not in [303, 307]:
        print(f"   Conteúdo: {response.text[:200]}")
    assert response.status_code in [303, 307]
    assert "/gatekeeper" in response.headers["location"]
    
    response = client.post("/gatekeeper", data={"password": "wrong"}, follow_redirects=True)
    assert "error=1" in str(response.url)
    
    import os
    gatekeeper_password = os.getenv("GATEKEEPER_PASSWORD")
    response = client.post("/gatekeeper", data={"password": gatekeeper_password}, follow_redirects=True)
    assert response.status_code == 200
    assert response.url.path == "/"
    # O cookie já deve estar setado pelo TestClient após o POST bem sucedido.
    print("   [OK] Gatekeeper protegendo e aceitando senha correta.")

    # 2. Testar Dashboard (Colunas e Conteúdo)
    print("2. Testando Dashboard...")
    response = client.get("/")
    assert response.status_code == 200
    assert "MATRÍCULA" in response.text
    assert "DIRETIVA TÉCNICA" in response.text
    assert "PN/CFF" not in response.text
    print("   [OK] Colunas do Dashboard atualizadas.")

    # 3. Testar Visibilidade de PDF para Usuário Não Logado
    print("3. Testando visibilidade de PDF (Não Logado)...")
    uid = str(uuid.uuid4())[:8]
    with Session(engine) as session:
        a = Aeronave(matricula=f"TEST-{uid}", numero_serie=f"SN-{uid}")
        session.add(a)
        session.flush()
        
        # Novo Modelo: codigo_simplificado é PK
        dt = DiretivaTecnica(codigo_simplificado=f"DT{uid}", codigo=f"DT-{uid}", objetivo="TEST PDF VISIBILITY", especialidade="ELT")
        session.add(dt)
        session.flush()
        
        item = DiretivaItem(diretiva_tecnica_id=dt.codigo_simplificado, fadt=f"FADT-{uid}", chave_item=f"DT{uid}|FADT-{uid}||", descricao_item="TEST ITEM")
        session.add(item)
        session.flush()
        
        link = DiretivaItemAeronave(aeronave_id=a.id, diretiva_item_id=item.id, status="Pendente", pdf_path="test_file.pdf")
        session.add(link)
        session.commit()
        link_id = link.id

    response = client.get(f"/directives/{link_id}")
    assert response.status_code == 200
    assert "Visualizar Documento (PDF)" in response.text
    assert "Atualizar Execução" not in response.text # Não logado não vê form
    print("   [OK] PDF visível para todos, formulário oculto para não logados.")

    # 4. Testar Restrição de Especialidade (Inspetor)
    print("4. Testando restrição de especialidade (Inspetor)...")
    with Session(engine) as session:
        # Create inspector with career 'BEI' (Electrical/ELE)
        user_in = User(username=f"insp_{uid}", email=f"insp_{uid}@test.com", hashed_password="hashed", role="inspetor", especialidade="BEI")
        session.add(user_in)
        # Directive is 'ELT' (Electronics). Career 'BEI' maps to 'ELE'. Should block.
        session.commit()
    
    token = security.create_access_token(data={"sub": f"insp_{uid}"})
    client.cookies.set("access_token", token)
    
    # Tentar editar diretiva de ELETRÔNICA (ELT) sendo de ELÉTRICA (Career BEI -> ELE)
    response = client.post(f"/directives/{link_id}", data={"status": "Concluída", "observacoes": "tentativa"})
    assert response.status_code == 403
    print("   [OK] Inspetor impedido de editar especialidade diferente.")

    print("--- TODOS OS TESTES PASSARAM COM SUCESSO ---")

if __name__ == "__main__":
    test_system_integrity()
