# SIGDT - Sistema de Gestão de Diretivas Técnicas

O **SIGDT** é uma aplicação web de alta performance desenvolvida para facilitar a gestão de diretivas técnicas (DT) de manutenção aeronáutica. O sistema substitui planilhas de Excel por uma interface reativa e moderna, priorizando a velocidade de acesso e o baixo consumo de recursos.

## 🚀 Arquitetura Técnica
O sistema foi construído para ser "extremamente leve" e funcionar bem em hardware limitado:

*   **Backend:** Python 3.11+ com **FastAPI** e **SQLModel**.
*   **Frontend:** **HTMX** (para fragmentos de HTML reativos sem o peso de SPAs como React/Vue) e **Tailwind CSS**.
*   **Banco de Dados:** SQLite (Desenvolvimento) / PostgreSQL (Produção).
*   **Ingestão de Dados:** Lógica de **Upsert** inteligente para arquivos CSV seguindo o padrão `modelo.csv`.

## ⚙️ Principais Funcionalidades
1.  **Matriz de Prioridade (GUT):** Cálculo automático baseado em Gravidade (CLA), Urgência (CAT) e Tendência (T).
2.  **Busca Instantânea:** Filtre por SN, Matrícula ou Diretiva em tempo real.
3.  **Gestão Dinâmica:** Ajuste fino da tendência individualmente por registro.
4.  **Upload CSV:** Ingestão de novas bases de dados sem duplicidade.

## 🛠️ Como Iniciar

### Com Docker
Certifique-se de ter o Docker e Docker Compose instalados:
```powershell
docker-compose up --build
```

### Manualmente (Python)
1. Instale as dependências:
   ```powershell
   pip install -r requirements.txt
   ```
2. Inicie o servidor:
   ```powershell
   uvicorn app.main:app --reload
   ```

Acesse o sistema em: **[http://localhost:8000](http://localhost:8000)**

## 📅 Próximos Passos
Consulte o arquivo `NEXT.md` para ver o roteiro detalhado de melhorias (RBAC, Paginação Server-side, etc).
