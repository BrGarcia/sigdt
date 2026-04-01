import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session
from starlette_csrf import CSRFMiddleware

from app.database import engine
from app.users import routes as user_routes
from app.users import actions as user_actions
from app.users import schemas as user_schemas
from app.core.config import SECRET_KEY, ADMIN_PASSWORD
from app.routers import auth, directives, admin

app = FastAPI(title="SIGDT - Sistema de Gestão de Diretivas Técnicas")

# CSRF Protection
app.add_middleware(CSRFMiddleware, secret=SECRET_KEY)

# Static files
if not os.path.exists("app/static"):
    os.makedirs("app/static", exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include Routers
app.include_router(auth.router)
app.include_router(directives.router)
app.include_router(admin.router)
app.include_router(user_routes.router)

@app.on_event("startup")
def on_startup():
    # Nota: Em produção, as migrações devem ser rodadas via Alembic CLI.
    # SQLModel.metadata.create_all(engine) removido conforme RELATORIO_FINAL.MD Fase 2.
    
    # Criar diretório de uploads se não existir
    os.makedirs("app/uploads", exist_ok=True)
    
    # Bootstrap Admin User
    with Session(engine) as session:
        admin_user = user_actions.get_user(session, "admin")
        if not admin_user:
            user_in = user_schemas.UserCreate(
                username="admin", 
                email="admin@example.com", 
                password=ADMIN_PASSWORD
            )
            user_actions.create_user(session, user_in, role="admin")

@app.get("/health")
async def health_check():
    return {"status": "ok"}
