# SIGDT - Sistema de Gestão de Diretivas Técnicas (v3.0.0)

O **SIGDT** é uma aplicação web de alta performance desenvolvida para a gestão de diretivas técnicas (DT) de manutenção aeronáutica. O sistema substitui planilhas complexas por uma interface relacional, permitindo o controle individualizado por aeronave enquanto mantém a padronização global das diretivas.

## 🚀 Arquitetura Técnica
Focado em eficiência e hardware limitado:
*   **Backend:** Python 3.11+ (FastAPI, SQLModel/SQLAlchemy).
*   **Frontend:** HTMX (reatividade leve) e Tailwind CSS.
*   **Banco de Dados:** PostgreSQL/SQLite (Relacional - Aeronave <-> Diretiva).
*   **Segurança Global:** Proteção Anti-CSRF e Rate Limiting persistente.
*   **Observabilidade:** Logging estruturado com rotação automática de arquivos.
*   **Containerização:** Docker & Docker Compose.
*   **Processamento de Documentos:** PyMuPDF para extração inteligente de dados em formulários AT.

## 🛡️ Camadas de Segurança
1.  **Gatekeeper:** Proteção de borda via senha global com limitador de tentativas persistente.
2.  **Anti-CSRF:** Proteção contra ataques de falsificação de solicitação entre sites em todas as operações de escrita.
3.  **RBAC:** Controle de acesso baseado em cargos (Admin, Inspetor, Usuário).
4.  **Especialidades Centralizadas:** Validação estrita baseada em uma fonte única de verdade (`app/constants.py`).

## ⚙️ Principais Funcionalidades
*   **Dashboard Relacional:** Visualização por aeronave com cálculo automático da Matriz GUT.
*   **Inserção Manual:** Cadastro individual de diretivas e aeronaves via formulário inteligente.
*   **Gestão Global de DTs:** Menu exclusivo para editar normas que afetam toda a frota.
*   **AT Parser (v2.0):** Extração automática de texto de arquivos PDF (Assessoramento Técnico).
*   **Importação Inteligente:** Ingestão de múltiplos CSVs com lógica de Upsert.

## 🛠️ Como Iniciar (Docker)
```powershell
docker-compose up --build -d
```
Acesse: **[http://localhost:8000](http://localhost:8000)**

## 📅 Roadmap Futuro (v3.0.0+)
*   Proteção Global Anti-CSRF.
*   Rate Limiter de Logins com persistência.
*   Logs de Auditoria estruturados.
*   Dashboards gráficos de conformidade.
