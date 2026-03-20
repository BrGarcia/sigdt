# Guia de Deploy no Railway - SIGDT

Siga estes passos para colocar o sistema online:

1.  **Acesse o [Railway.app](https://railway.app/)** e faça login com seu GitHub.
2.  **Novo Projeto:** Clique em `+ New Project` -> `Deploy from GitHub repo`.
3.  **Selecione o Repositório:** Escolha `BrGarcia/sigdt`.
4.  **Adicionar Banco de Dados:**
    *   No painel do projeto, clique em `+ New` -> `Database` -> `Add PostgreSQL`.
    *   O Railway criará o banco e gerará automaticamente uma variável chamada `DATABASE_URL`.
5.  **Configurar Variáveis de Ambiente:**
    *   Clique no serviço `web` (seu app) -> Aba `Variables`.
    *   Adicione as seguintes variáveis:
        *   `SECRET_KEY`: (Crie uma frase longa aleatória)
        *   `ADMIN_PASSWORD`: `5Hr9Mk>06=L%`
        *   `GATEKEEPER_PASSWORD`: `@J6!~@s6q67eN~k/`
    *   *Nota: O Railway já conecta o DATABASE_URL do banco de dados ao seu app se estiverem no mesmo projeto.*
6.  **Deploy:** O Railway iniciará o build automaticamente. Assim que terminar, ele gerará uma URL (ex: `sigdt-production.up.railway.app`).

---
**Dica:** Se o deploy falhar no primeiro boot, verifique se o banco de dados já terminou de inicializar antes do app.
