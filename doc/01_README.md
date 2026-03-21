# SIGDT - Sistema de Gestão de Diretivas Técnicas (v2.0.0-dev)

O **SIGDT** é uma aplicação web de alta performance desenvolvida para a gestão de diretivas técnicas (DT) de manutenção aeronáutica. O sistema substitui planilhas complexas por uma interface relacional, permitindo o controle individualizado por aeronave enquanto mantém a padronização global das diretivas.

## 🚀 Arquitetura Técnica
Focado em eficiência e hardware limitado:
*   **Backend:** Python 3.11+ (FastAPI, SQLModel/SQLAlchemy).
*   **Frontend:** HTMX (reatividade leve) e Tailwind CSS.
*   **Banco de Dados:** PostgreSQL (Relacional - Aeronave <-> Diretiva).
*   **Containerização:** Docker & Docker Compose.
*   **Processamento de Documentos:** PyMuPDF para extração inteligente de dados.

## 🛡️ Camadas de Segurança
1.  **Gatekeeper:** Proteção de borda via senha global (`asdf1234`) para acesso ao site.
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

## 📅 Roadmap v2.0.0
*   Extração Automática de Dados de PDFs (AT Parser).
*   Logs de Auditoria detalhados.
*   Dashboards gráficos de conformidade.
*   Notificações automáticas de DTs críticas.
