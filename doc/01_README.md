# SIGDT - Sistema de Gestão de Diretivas Técnicas (v3.5.0-dev)

O **SIGDT** é uma aplicação web de alta performance desenvolvida para a gestão de diretivas técnicas (DT) de manutenção aeronáutica. O sistema substitui planilhas complexas por uma interface relacional, permitindo o controle individualizado por aeronave enquanto mantém a padronização global das diretivas.

## 🚀 Arquitetura Técnica
Focado em eficiência e hardware limitado:
*   **Backend:** Python 3.11+ (FastAPI, SQLModel/SQLAlchemy).
*   **Frontend:** HTMX (reatividade leve) e Tailwind CSS.
*   **Banco de Dados:** PostgreSQL (Relacional - Aeronave <-> Diretiva).
*   **Containerização:** Docker & Docker Compose.
*   **Processamento de Documentos:** PyMuPDF para extração inteligente de dados em formulários AT.
*   **Migrações DB:** Alembic para versionamento estrutural.

## 🛡️ Camadas de Segurança
1.  **Gatekeeper:** Proteção de borda via senha global configurada no `.env` do servidor.
2.  **RBAC:** Controle de acesso baseado em cargos (Admin, Inspetor, Usuário).
3.  **Especialidades:** Inspetores só podem editar diretivas vinculadas à sua especialidade técnica.

## ⚙️ Principais Funcionalidades
*   **Dashboard Relacional:** Visualização por aeronave com cálculo automático da Matriz GUT.
*   **Gestão Global de DTs:** Menu exclusivo para editar normas que afetam toda a frota.
*   **AT Parser (v2.0):** Extração automática de texto de arquivos PDF (Assessoramento Técnico) para preenchimento imediato de pareceres e serviços solicitados.
*   **Anexos Técnicos:** Upload e visualização de comprovantes em PDF por aeronave com exibição de texto extraído.
*   **Importação Inteligente:** Ingestão de múltiplos CSVs com lógica de Upsert (evita duplicidade).
*   **Exportação:** Gerador de relatórios XLSX acessível para todos os níveis de usuário.

## 🛠️ Como Iniciar (Docker)
```powershell
docker-compose up --build -d
```
Acesse: **[http://localhost:8000](http://localhost:8000)**

## 📅 Versão 3.5.0 (Concluída - Estabilização e Segurança)
*   **[✅ C1]** Dependências pinadas no `requirements.txt` (build reprodutível).
*   **[✅ C2]** Bug `datetime.now(timezone.utc)` corrigido em `app/main.py`.
*   **[✅ C3]** `logs.txt` adicionado ao `.gitignore`.
*   **[✅ A2]** Comparação segura no Gatekeeper (`hmac.compare_digest`).
*   **[✅ A3]** Cookie do Gatekeeper assinado com `SECRET_KEY` (JWT).
*   **[✅ A6]** Validação robusta de inputs nos schemas Pydantic.
*   **[✅ A7]** Enum de status de diretiva para bloquear valores arbitrários no backend.
*   **[✅ T1]** Expansão da suíte de testes (Segurança e Integridade).

## 📅 Roadmap Futuro (v4.0.0+)
*   Multi-Ambientes (Hangar X / Y).
*   WebSocket Real-Time Locks.
*   Dashboards visuais de conformidade da frota.
