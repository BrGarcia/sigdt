# SIGDT - Sistema de Gestão de Diretivas Técnicas

Sistema para transpor a gestão de diretivas técnicas de manutenção aeronáutica para uma aplicação web robusta, segura e leve.

## Stack Técnica

- **Backend:** Python 3.10+ (FastAPI)
- **Frontend:** HTMX + Tailwind CSS
- **Banco de Dados:** PostgreSQL (Produção) / SQLite (Desenvolvimento)
- **Containerização:** Docker & Docker Compose

## Funcionalidades Principais

- Ingestão de dados via CSV com lógica de Upsert.
- Cálculo automático de prioridade via Matriz GUT (Gravidade, Urgência, Tendência).
- Dashboard com filtros dinâmicos e busca global.
- Controle de acesso (RBAC) e logs de auditoria.

## Como Iniciar

### Usando Docker

```bash
docker-compose up --build
```

O sistema estará disponível em `http://localhost:8000`.

### Localmente

1. Crie um ambiente virtual: `python -m venv venv`
2. Ative o ambiente: `source venv/bin/activate` (ou `venv\Scripts\activate` no Windows)
3. Instale as dependências: `pip install -r requirements.txt`
4. Execute o app: `uvicorn app.main:app --reload`
