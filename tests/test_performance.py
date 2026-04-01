import pytest
from app.services.csv_service import process_csv
from sqlmodel import Session, select, func
from app.models import DiretivaItemAeronave
import time

def test_performance_csv_import(session: Session):
    """
    Testa a performance da importação de um CSV com 1000 linhas.
    Verifica se a otimização de cache está funcionando (sem explosão de queries).
    """
    # Gerar 1000 linhas de CSV fake
    csv_header = "MATR;SN;FADT;DIRETIVA TÉCNICA;OBJETIVO;CLA;CAT;TIPO INCORPORAÇÃO;NAT;ESPECIALIDADE;STATUS;ORDEM;OBSERVAÇÕES\n"
    csv_lines = []
    for i in range(1000):
        # 10 aeronaves diferentes, 100 DTs por aeronave
        aero_id = i % 10
        dt_id = i // 10
        line = f"PR-T{aero_id};SN{aero_id};FADT-{i};DT-{dt_id};Objetivo Performance {dt_id};M;I;P;N;CEL;Pendente;ORD-{i};Obs {i}"
        csv_lines.append(line)
    
    csv_content = csv_header + "\n".join(csv_lines)
    
    start_time = time.time()
    processed = process_csv(csv_content, filename="perf_test.csv", session=session)
    end_time = time.time()
    
    duration = end_time - start_time
    print(f"\n   [PERF] Importação de 1000 linhas concluída em {duration:.2f}s")
    
    assert processed == 1000
    # Em hardware moderno e com as otimizações, 1000 linhas devem levar menos de 10 segundos
    assert duration < 10.0 

    # Verificar integridade no banco
    count = session.exec(select(func.count(DiretivaItemAeronave.id))).one()
    assert count >= 1000
