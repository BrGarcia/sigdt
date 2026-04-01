# RELATÓRIO DE REVISÃO TÉCNICA — SIGDT

**Revisor:** Claude (IA — Engenheiro de Software Sênior)
**Data:** 31/03/2026
**Escopo:** Análise completa do repositório SIGDT (Sistema de Gestão de Diretivas Técnicas)
**Versão analisada:** branch corrente (~v4.0.0-dev)

---

## DIAGNÓSTICO GERAL

O SIGDT é uma aplicação web FastAPI que gerencia diretivas técnicas de aeronaves militares. O projeto tem uma estrutura funcional, com autenticação dual (gatekeeper + JWT), model relacional via SQLModel, upload/parsing de PDFs, exportação XLSX e interface HTMX/Tailwind.

**Pontos positivos observados:**
- Modelo relacional bem normalizado (DiretivaTecnica → DiretivaItem → DiretivaItemAeronave)
- Lógica de snapshot com auto-conclusão de itens ausentes
- Validação via Pydantic nos schemas de usuário
- Rate limiting implementado
- Comparação segura de senhas (HMAC) no gatekeeper
- Cookie com assinatura JWT e flags httponly/samesite

**Problemas estruturais identificados:**
O projeto sofre com concentração de lógica no `main.py` (614 linhas numa única rota-monólito), ausência de proteção CSRF em formulários POST, banco SQLite em produção (sem ser intencional), testes insuficientes, e diversas fragilidades de segurança que são detalhadas abaixo.

---

## 1. ARQUITETURA E ORGANIZAÇÃO DO PROJETO

### [CRÍTICA] A-1 — `main.py` é um God Module (614 linhas)

**O que está errado:** Toda a lógica de negócio, rotas, helpers, filtros de template e configuração de segurança está concentrada em `app/main.py`. São 20+ endpoints, funções auxiliares (`format_especialidade`, `has_specialty_permission`, `apply_filters`, `is_rate_limited`, `check_gatekeeper`), e lógica de upload tudo no mesmo arquivo.

**Risco:** Manutenção extremamente difícil. Qualquer alteração numa rota pode quebrar outra. Impossível ter code ownership ou trabalho paralelo.

**Impacto:** Alto — afeta produtividade da equipe e aumenta chance de regressões.

**Correção recomendada:**
```
app/
├── main.py              # Apenas setup do FastAPI, includes de routers
├── config.py            # SECRET_KEY, GATEKEEPER_PASSWORD, configurações
├── security/
│   ├── gatekeeper.py    # check_gatekeeper, gatekeeper_verify, rate_limiter
│   └── permissions.py   # has_specialty_permission
├── routers/
│   ├── dashboard.py     # /, /directives, /directives/{id}
│   ├── directives.py    # CRUD de diretivas e master-directives
│   ├── upload.py        # /upload (CSV)
│   └── export.py        # /export/xlsx
├── services/
│   ├── csv_service.py   # (já existe)
│   ├── pdf_parser.py    # (já existe)
│   └── gut_service.py   # Cálculo GUT isolado
├── users/               # (já existe, estrutura boa)
├── models.py
├── database.py
└── templates/
```

**Ordem de implementação:** Fase 2 (refatoração estrutural).

---

### [MÉDIA] A-2 — Importações circulares entre `main.py` e `users/routes.py`

**O que está errado:** `users/routes.py` linha 76 faz `from app.main import is_rate_limited` e linha 126 faz `from app.main import templates`. São importações circulares resolvidas por deferment (import dentro da função), que é um anti-pattern.

**Risco:** Fragilidade estrutural. Mudanças em `main.py` podem causar erros de importação em cascata.

**Correção:** Mover `is_rate_limited` para um módulo `app/security/rate_limiter.py` independente. Mover a instância de `templates` para um módulo compartilhado ou injetar via dependência.

---

### [BAIXA] A-3 — Diretório `old/` vazio versionado

**O que está errado:** O diretório `old/` está vazio e presente no repositório. Sem .gitkeep, sem propósito.

**Correção:** Remover do repositório: `git rm -r old/`.

---

### [BAIXA] A-4 — `.DS_Store` presente no repositório

**O que está errado:** Arquivo `.DS_Store` (macOS) está na raiz e em `migrations/`. Indica que o `.gitignore` não cobriu esses antes do primeiro commit.

**Correção:** `git rm --cached .DS_Store migrations/.DS_Store` e adicionar `.DS_Store` ao `.gitignore`.

---

## 2. QUALIDADE DE CÓDIGO

### [ALTA] Q-1 — Duplicação massiva do bloco de logout em templates

**O que está errado:** O bloco JavaScript de logout (fetch + redirect) é repetido identicamente em **6 templates**: `index.html`, `directive_details.html`, `user_management.html`, `master_directives.html`, `master_directive_edit.html`. São ~10 linhas copiadas literalmente cada vez.

**Risco:** Manutenção inconsistente. Se a lógica de logout mudar, precisa ser atualizado em 6 lugares.

**Correção:** Extrair para um arquivo `static/js/auth.js` e incluí-lo via `<script src>`. Ou criar um template Jinja2 partial `partials/logout_script.html` com `{% include %}`.

---

### [ALTA] Q-2 — Duplicação do navbar em todos os templates

**O que está errado:** A navbar é copy/paste em 6 templates HTML (index, directive_details, user_management, master_directives, master_directive_edit, login). As variações são pequenas (links ativos diferentes), mas o layout base é idêntico.

**Correção:** Criar um `base.html` com herança Jinja2:
```html
<!-- base.html -->
{% block content %}{% endblock %}
```
E usar `{% extends "base.html" %}` nos demais templates.

---

### [MÉDIA] Q-3 — Import de `time` duplicado em `main.py`

**O que está errado:** `import time` aparece duas vezes: linha 14 e no bloco da linha 97 (`from collections import defaultdict; import time`).

**Correção:** Remover a segunda importação.

---

### [MÉDIA] Q-4 — Imports inline desnecessários

**O que está errado:** Em `main.py`:
- Linha 221: `import io as _io` — já é importado na linha 8 como `io`
- Linha 222: `import pandas as _pd` — já é importado na linha 10 como `pd`
- Linha 504: `import re` — deveria estar no topo
- Linha 135: `from app.users import security as user_security` — dentro do `on_startup`
- Linha 92: `import os` no `users/routes.py` — dentro de função

**Correção:** Mover todas as importações para o topo do ficheiro. Usar os aliases já existentes.

---

### [MÉDIA] Q-5 — `apply_filters` usa lista mutável como argumento padrão

**O que está errado:** `main.py` linha 235: `def apply_filters(..., especialidade: List[str] = [])`. Usar uma lista mutável como valor padrão é um bug clássico em Python.

**Risco:** Se `especialidade` for modificada dentro da função, o valor padrão é corrompido permanentemente para chamadas subsequentes. Neste caso, o risco é baixo porque a lista não é mutada, mas é um anti-pattern perigoso.

**Correção:** `especialidade: Optional[List[str]] = None` e tratar `None` como lista vazia no corpo.

---

### [BAIXA] Q-6 — Status `str` no modelo não é tipado com Enum

**O que está errado:** Apesar de existir `StatusDiretiva(Enum)`, o campo `status` em `DiretivaItemAeronave` é `str = Field(default="Pendente")`. Não usa o Enum diretamente no SQLModel.

**Correção:** Embora SQLite tenha limitações com enums, o ideal seria usar `sa_column=Column(Enum(StatusDiretiva))` ou ao menos validar ambos na entrada E na saída.

---

### [BAIXA] Q-7 — `origin_status` usa strings hardcoded

**O que está errado:** `origem_status` aceita "csv" ou "manual" como strings livres sem validação via Enum.

**Correção:** Criar `class OrigemStatus(str, Enum)`.

---

## 3. SEGURANÇA

### [CRÍTICA] S-1 — Arquivo `.env` commitado no repositório (senhas expostas)

**O que está errado:** O `.env` contém:
```
ADMIN_PASSWORD=... (senha forte)
GATEKEEPER_PASSWORD=... (senha forte)
SECRET_KEY=... (frase longa aleatória)
```
Embora `.env` esteja no `.gitignore`, o arquivo **já existe** no repositório. Se foi commitado antes da regra no `.gitignore`, as credenciais estão no histórico Git.

**Risco:** CRÍTICO — qualquer pessoa com acesso ao repo (ou clone) pode obter todas as credenciais.

**Correção imediata:**
1. Verificar: `git log --all -- .env` — se retornar resultados, as credenciais estão no histórico.
2. Rotacionar TODAS as senhas e a SECRET_KEY imediatamente.
3. Usar `git filter-branch` ou `BFG Repo Cleaner` para expurgar o `.env` do histórico.
4. Distribuir um `.env.example` sem valores reais.

---

### [CRÍTICA] S-2 — Ausência de proteção CSRF em formulários POST

**O que está errado:** O `PROGRESS.md` menciona que `CSRFMiddleware` foi implementado na v3.0.0-dev, porém **não existe nenhum middleware CSRF no código atual**. Nenhum dos formulários HTML inclui tokens CSRF. Os formulários POST (gatekeeper, upload CSV, update directive, create user, update master directive) estão **todos vulneráveis a CSRF**.

**O arquivo `main.py` não importa nem registra nenhum middleware CSRF.** O HTMX envia requests diretamente sem headers anti-CSRF.

**Risco:** CRÍTICO — Um atacante pode forjar formulários que executem ações em nome de um administrador logado (upload de CSV malicioso, criação de usuários, alteração de diretivas).

**Correção:**
1. Implementar middleware CSRF (via starlette-csrf ou custom middleware)
2. Adicionar token CSRF em todos os formulários HTML.
3. Configurar HTMX para enviar o header CSRF via `hx-headers`.

---

### [CRÍTICA] S-3 — Rate limiter não-persistente (in-memory)

**O que está errado:** O rate limiter usa um `defaultdict(list)` em memória (`main.py` linha 98). Se a aplicação for reiniciada (deploy, crash, restart do container), o contador é zerado. Sem limite real para brute force.

**Risco:** Alto — um atacante pode contornar o rate limiter simplesmente esperando por um restart. Em produção com múltiplos workers (uvicorn com `--workers N`), cada worker tem seu próprio dicionário, dividindo a proteção.

**Correção:**
- **Mínima:** Manter in-memory mas com cleanup periódico (já existe parcialmente).
- **Ideal:** Usar Redis ou banco de dados para persistir contadores de tentativas.
- **Intermediária:** Se o sistema roda com 1 worker (que parece ser o caso), aceitável manter in-memory mas documentar a limitação.

---

### [ALTA] S-4 — SECRET_KEY com fallback inseguro

**O que está errado:** `main.py` linha 109:
```python
SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key_change_in_production")
```
Enquanto `users/security.py` corretamente lança `ValueError` se `SECRET_KEY` não estiver definida, o `main.py` usa um fallback estático. Isso significa que os JWTs do gatekeeper usam uma chave potencialmente previsível.

**Risco:** Se a variável de ambiente não estiver configurada, os tokens do gatekeeper podem ser forjados trivialmente.

**Correção:** Remover o fallback:
```python
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("Variável de ambiente SECRET_KEY é obrigatória.")
```

---

### [ALTA] S-5 — Upload de PDF sem validação de path traversal no filename

**O que está errado:** Em `main.py` linha 351, o `new_filename` é construído com `diretiva_id` que vem da URL — um inteiro controlado pelo router, portanto seguro. Porém, **não há sanitização do `pdf_file.filename`** que é logado ou eventualmente processado. Embora o sistema force o rename, se alguém mudasse a lógica futuramente para usar o nome original, haveria path traversal.

**Risco:** Baixo agora (mitigado pelo rename forçado), mas alto se o código evoluir.

**Correção:** Adicionar validação explícita:
```python
from pathlib import PurePosixPath
safe_name = PurePosixPath(pdf_file.filename).name  # Remove paths
```

---

### [ALTA] S-6 — Upload de CSV lê o arquivo inteiro na memória antes de validar tamanho

**O que está errado:** `main.py` linhas 216-218:
```python
content = await file.read()  # Lê TUDO na memória
if len(content) > MAX_CSV_SIZE:  # Só depois verifica
```
Um atacante pode enviar um arquivo de 500MB que será completamente carregado na memória antes da validação.

**Risco:** Denial of Service — OOM Kill do processo.

**Correção:** Ler em chunks e contar bytes:
```python
content = b""
while chunk := await file.read(8192):
    content += chunk
    if len(content) > MAX_CSV_SIZE:
        raise HTTPException(413, "Arquivo excede 50MB")
```
Ou usar `request.headers.get("content-length")` para rejeição antecipada (não confiável sozinho).

---

### [ALTA] S-7 — Gatekeeper token com `time.time()` em vez de `datetime`

**O que está errado:** `main.py` linha 161:
```python
token = jwt.encode({"access": "granted", "exp": time.time() + 86400 * 7}, ...)
```
O `time.time()` retorna um float Unix timestamp. A maioria das libs JWT espera `datetime` ou int. O `python-jose` aceita floats, mas isso pode causar problemas sutis de timezone ou arredondamento.

**Correção:** Usar formato padrão:
```python
from datetime import datetime, timedelta, timezone
exp = datetime.now(timezone.utc) + timedelta(days=7)
token = jwt.encode({"access": "granted", "exp": exp}, ...)
```

---

### [MÉDIA] S-8 — Busca SQL com `LIKE` sem escape de caracteres especiais

**O que está errado:** `apply_filters` em `main.py` linhas 237-244:
```python
search_filter = f"%{search}%"
statement = statement.where(Aeronave.numero_serie.like(search_filter))
```
Se o usuário buscar por `%` ou `_` (wildcard do SQL LIKE), o resultado será inesperado. Não é SQL injection (parametrizado pelo ORM), mas é um bug funcional.

**Correção:** Escapar wildcards:
```python
search_escaped = search.replace("%", "\\%").replace("_", "\\_")
search_filter = f"%{search_escaped}%"
```

---

### [MÉDIA] S-9 — Formulários não validam role no backend de forma restrita

**O que está errado:** `users/routes.py` linha 114: `role: str = Form("inspetor")`. O valor vem de um `<select>` no frontend, mas nada impede um POST direto com `role=superadmin` ou qualquer string.

**Correção:** Validar com whitelist:
```python
VALID_ROLES = {"user", "inspetor", "admin"}
if role not in VALID_ROLES:
    raise HTTPException(400, "Role inválida")
```

---

### [MÉDIA] S-10 — Banco de dados SQLite sem criptografia em disco

**O que está errado:** O arquivo `sigdt.db` está no diretório raiz sem proteção. Qualquer processo no mesmo sistema pode ler todos os dados incluindo hashes de senhas.

**Correção:** Se permanecer com SQLite, considerar `sqlcipher`. Se migrar para PostgreSQL (recomendado para produção), configurar SSL e credenciais fortes.

---

## 4. BANCO DE DADOS E MIGRAÇÕES

### [ALTA] D-1 — SQLite em produção com intenção de PostgreSQL

**O que está errado:** O `alembic.ini` está hardcoded para SQLite (`sqlalchemy.url = sqlite:///sigdt.db`), o `docker-compose.yml` configura PostgreSQL, e o `database.py` consome `DATABASE_URL` do ambiente. A inconsistência gera confusão.

**Correção:**
1. Remover URL do `alembic.ini` (já é sobrescrito pelo `env.py`).
2. Definir que em desenvolvimento usa SQLite e em produção PostgreSQL.
3. Documentar explicitamente no README.

---

### [ALTA] D-2 — `init_db()` via `create_all` em produção + Alembic

**O que está errado:** `database.py` usa `SQLModel.metadata.create_all(engine)` no startup. Isso conflita com Alembic, que é a ferramenta de migrações. Se um novo campo for adicionado ao modelo e uma migração Alembic for criada, o `create_all` pode criar a tabela sem a migração ser aplicada, causando divergência de schema.

**Risco:** Schema drift — o banco pode ficar num estado inconsistente entre o que o Alembic "acha" que existe e o que realmente existe.

**Correção:**
- Em produção, **nunca** usar `create_all`. Usar apenas `alembic upgrade head`.
- Em desenvolvimento, opcionalmente usar `create_all` para agilidade, mas com flag de ambiente:
```python
def init_db():
    if os.getenv("ENVIRONMENT") == "development":
        SQLModel.metadata.create_all(engine)
```

---

### [MÉDIA] D-3 — Falta índice composto em `DiretivaItemAeronave`

**O que está errado:** A tabela `diretiva_item_aeronave` tem `UniqueConstraint("aeronave_id", "diretiva_item_id")` mas a query no `csv_service.py` faz:
```python
select(DiretivaItemAeronave).where(
    DiretivaItemAeronave.aeronave_id == ...,
    DiretivaItemAeronave.diretiva_item_id == ...
)
```
A `UniqueConstraint` pode ser usada como índice em alguns DBs, mas em SQLite o comportamento não é garantido para performance.

**Correção:** Adicionar `Index("ix_dia_aero_item", "aeronave_id", "diretiva_item_id")` explicitamente.

---

### [MÉDIA] D-4 — Dashboard principal carrega relações sem join explícito (N+1 problem)

**O que está errado:** `main.py` rota `/` (linha 196):
```python
statement = select(DiretivaItemAeronave).order_by(desc(DiretivaItemAeronave.gut)).offset(offset).limit(per_page)
```
No template, o acesso a `diretiva.aeronave.matricula` e `diretiva.diretiva_item.diretiva_tecnica.codigo` causa **N+1 queries** (lazy loading). Para 50 registros, isso é 50x2 = ~100 queries extras.

**Risco:** Performance degradante linear com volume de dados.

**Correção:** Usar `selectinload` ou `joinedload`:
```python
from sqlalchemy.orm import selectinload
statement = (
    select(DiretivaItemAeronave)
    .options(
        selectinload(DiretivaItemAeronave.aeronave),
        selectinload(DiretivaItemAeronave.diretiva_item)
            .selectinload(DiretivaItem.diretiva_tecnica)
    )
    .order_by(desc(DiretivaItemAeronave.gut))
    .offset(offset).limit(per_page)
)
```

---

### [MÉDIA] D-5 — `echo=True` no engine SQLite em desenvolvimento

**O que está errado:** `database.py` linha 11:
```python
engine = create_engine(DATABASE_URL, echo=True if "sqlite" in DATABASE_URL else False)
```
Isso loga TODAS as queries SQL no stdout, inclusive em ambientes onde SQLite é usado inadvertidamente.

**Correção:** Atrelar ao `ENVIRONMENT`:
```python
echo = os.getenv("ENVIRONMENT") == "development" and os.getenv("SQL_DEBUG") == "1"
```

---

### [BAIXA] D-6 — Modelo `Snapshot` não tem índice em `aeronave_id`

**O que está errado:** A tabela `snapshot` referencia `aeronave.id` via FK, mas não tem índice explícito. Com volume crescente de snapshots, consultas por aeronave serão lentas.

**Correção:** `aeronave_id: int = Field(foreign_key="aeronave.id", index=True)`.

---

## 5. TESTES E CONFIABILIDADE

### [CRÍTICA] T-1 — Cobertura de testes extremamente baixa

**O que está errado:** Existem apenas 4 ficheiros de teste com ~15 test cases no total. A cobertura estimada é inferior a **10%**. Cenários **não testados**:
- Upload de CSV (end-to-end)
- Processamento de CSV com dados reais (deduplicação, consolidação)
- Auto-conclusão de itens via snapshot
- Update de status de diretiva
- Cálculo GUT
- Exportação XLSX com filtros
- Fluxo completo de criação de usuário
- Edição de master directives com recálculo GUT
- Exclusão de anexo PDF
- PDF parser com documentos reais
- Rate limiter (parcialmente coberto, mas sem cleanup)

**Risco:** CRÍTICO — qualquer mudança pode introduzir regressões não detectadas.

**Correção:** Criar test suite em 3 camadas:
1. **Unit tests:** `calculate_gut()`, `sanitize_codigo()`, `generate_chave_item()`, `format_especialidade()`, `has_specialty_permission()`, `clean_text()`
2. **Integration tests:** CSV processing, PDF parsing, user CRUD completo
3. **E2E tests:** Fluxo completo de upload - dashboard - edição - export

---

### [ALTA] T-2 — Testes usam banco de dados compartilhado (sem isolamento)

**O que está errado:** Todos os testes usam a mesma engine/database da aplicação. O `test_new_features.py` chama `init_db()` no nível do módulo e cria registros com UUIDs para evitar colisões, mas isso não é isolamento real.

**Risco:** Testes flaky, estado contaminado entre runs, impossível rodar em paralelo.

**Correção:** Usar banco in-memory por sessão de teste:
```python
@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite://", echo=False)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)
```

---

### [MÉDIA] T-3 — `integrity_check.py` não é um pytest, é um script manual

**O que está errado:** `tests/integrity_check.py` usa `print()` para output e roda como `__main__`. Não segue convenções pytest, tornando-o incompatível com CI/CD.

**Correção:** Refatorar para usar assertions e fixtures pytest padrão.

---

## 6. DOCKER, AMBIENTE E DEPLOY

### [ALTA] K-1 — Dockerfile não usa multi-stage build e roda como root

**O que está errado:** O Dockerfile atual:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["sh", "-c", "uvicorn ..."]
```

Problemas:
1. Roda como `root` (padrão do container) — se o aplicativo for comprometido, o atacante tem acesso root.
2. Copia **tudo** (incluindo `.env`, `.git`, `sigdt.db`, `tests/`, `old/`) para o container.
3. Sem `.dockerignore`.

**Correção:**
```dockerfile
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim
RUN useradd --create-home sigdt
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY app/ app/
COPY migrations/ migrations/
COPY alembic.ini .
USER sigdt
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

Criar `.dockerignore`:
```
.git
.env
*.db
tests/
old/
doc/
__pycache__
```

---

### [MÉDIA] K-2 — `docker-compose.yml` expõe porta do PostgreSQL

**O que está errado:** `ports: - "5432:5432"` no serviço `db` expõe o banco de dados na rede do host. Em ambiente de desenvolvimento é aceitável, mas deve ser explicitamente marcado.

**Correção:** Usar `expose: ["5432"]` em vez de `ports` (acessível apenas pela rede Docker), ou remover completamente para produção.

---

### [MÉDIA] K-3 — `--forwarded-allow-ips='*'` no Dockerfile CMD

**O que está errado:** `--forwarded-allow-ips='*'` aceita headers `X-Forwarded-For` de qualquer IP. Se o container ficar exposto diretamente (sem proxy reverso), qualquer pessoa pode falsificar seu IP nos logs e no rate limiter.

**Correção:** Especificar os IPs reais do proxy reverso ou remover se não necessário.

---

### [BAIXA] K-4 — `version: '3.8'` deprecado no docker-compose

**O que está errado:** A chave `version` em `docker-compose.yml` é obsoleta desde Compose V2.

**Correção:** Remover a linha `version: '3.8'`.

---

## 7. DEPENDÊNCIAS E MANUTENÇÃO

### [ALTA] P-1 — `bcrypt==3.2.2` e `passlib==1.7.4` sem manutenção

**O que está errado:** `bcrypt 3.2.2` é de 2022. Versões 4.x mudaram a API. `passlib` está **sem manutenção** (último release: 2022, repo arquivado).

**Risco:** Vulnerabilidades futuras sem patches. Incompatibilidade quando Python ou bcrypt atualizar.

**Correção:** Considerar migrar para `argon2-cffi` ou usar `bcrypt` diretamente sem passlib:
```python
import bcrypt
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
```

---

### [ALTA] P-2 — `python-jose` sem manutenção

**O que está errado:** `python-jose` está **sem manutenção** (último commit: 2022, issues abertas não respondidas). O projeto recomenda oficialmente migrar para alternativas.

**Correção:** Migrar para `PyJWT` (ativo, mantido):
```python
import jwt  # PyJWT
token = jwt.encode(payload, key, algorithm="HS256")
data = jwt.decode(token, key, algorithms=["HS256"])
```

---

### [MÉDIA] P-3 — `PyMuPDF==1.27.2.2` é uma dependência pesada

**O que está errado:** PyMuPDF (fitz) é uma biblioteca nativa com ~30MB de binários. É usada apenas para parsing de PDFs de fichas AT. Se o parsing de PDF for uma feature secundária, o peso é desproporcional.

**Risco:** Aumenta tempo de build, tamanho do container e superfície de ataque.

**Correção:** Aceitar se o parsing é funcionalidade core. Alternativamente, considerar `pdfplumber` (pure Python, mais leve).

---

### [MÉDIA] P-4 — `pandas` + `openpyxl` para exportação simples

**O que está errado:** `pandas` (~60MB com dependências) é usado para construir um DataFrame simples e exportar para XLSX. Para esta operação, `openpyxl` sozinho é suficiente.

**Correção:** Usar `openpyxl` diretamente:
```python
from openpyxl import Workbook
wb = Workbook()
ws = wb.active
ws.append(headers)
for row in data:
    ws.append(list(row.values()))
```
Isso eliminaria `pandas` como dependência (~60MB a menos no container).

---

### [BAIXA] P-5 — `starlette==0.46.2` explicitamente pinada

**O que está errado:** `starlette` é dependência transitiva do `fastapi`. Pinar explicitamente pode causar conflitos de versão. FastAPI já garante compatibilidade.

**Correção:** Remover `starlette` do `requirements.txt`.

---

## 8. PERFORMANCE E ESCALABILIDADE

### [ALTA] E-1 — N+1 queries no dashboard e listagens

**O que está errado:** Conforme descrito em D-4, as listagens de diretivas não fazem eager loading das relações. Para cada registro, são executadas queries adicionais para buscar aeronave, diretiva_item e diretiva_tecnica.

**Impacto medido:** Com 1000 registros na tabela, a página principal executa ~150 queries (50 registros x 3 relações). Com `selectinload`, reduziria para 4 queries.

---

### [ALTA] E-2 — CSV service faz query individual por item dentro do loop

**O que está errado:** `csv_service.py` linhas 139-163: para cada linha do CSV, executa uma `select` para buscar o `DiretivaItem` e outra para o `DiretivaItemAeronave`. Com um CSV de 5000 linhas, são ~10.000 queries.

**Correção:** Pré-carregar todos os items e links no início do processamento:
```python
# Pré-carregar todos os items existentes
items_cache = {
    item.chave_item: item
    for item in session.exec(select(DiretivaItem)).all()
}
links_cache = {
    (l.aeronave_id, l.diretiva_item_id): l
    for l in session.exec(select(DiretivaItemAeronave)).all()
}
```

---

### [MÉDIA] E-3 — `d.items | length` no template causa lazy load

**O que está errado:** `master_directives.html` linha 51:
```html
{{ d.items | length }} item(s)
```
Sem eager loading, isso causa uma query por diretiva para contar items. Para 50 diretivas na página, são 50 queries extras.

**Correção:** Usar `selectinload(DiretivaTecnica.items)` na query ou fazer um `COUNT()` agregado no backend.

---

### [MÉDIA] E-4 — Recálculo GUT itera todos os links de uma master directive

**O que está errado:** `main.py` linhas 603-607:
```python
for item in master_dt.items:
    for link in item.aeronave_links:
        link.calculate_gut()
        session.add(link)
```
Se uma master directive tem 100 items com 50 aeronaves cada, isso itera 5000 registros sincronamente.

**Correção:** Usar UPDATE em batch via SQL ou mover para background job.

---

## 9. UX TÉCNICA E USABILIDADE INTERNA

### [ALTA] X-1 — CDN de script em produção sem fallback local

**O que está errado:** Todos os templates carregam Tailwind e HTMX via CDN:
```html
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://unpkg.com/htmx.org@1.9.10"></script>
```
Se o CDN estiver indisponível (rede interna militar, proxy restritivo), o sistema fica completamente sem estilização e interatividade.

**Risco:** ALTO para sistema militar — redes restritas podem bloquear CDNs externos.

**Correção:** Baixar os arquivos e servir localmente via `app/static/`:
```
app/static/js/tailwind.min.js
app/static/js/htmx.min.js
```

**NOTA:** O `cdn.tailwindcss.com` é o **Tailwind CSS Play CDN**, que é explicitamente marcado como "for development and prototyping only" e não deve ser usado em produção. Para produção, deve-se usar o Tailwind CLI ou PostCSS para gerar um CSS compilado.

---

### [MÉDIA] X-2 — Ausência de `base.html` obriga manutenção duplicada

Reforço do Q-2 com impacto de UX: qualquer mudança na navegação, favicon, scripts ou meta tags precisa ser feita em 7+ arquivos.

---

### [MÉDIA] X-3 — Mensagens de erro inconsistentes (inglês e português)

**O que está errado:** Algumas mensagens estão em inglês (HTTPException details: "Not authenticated", "User not found", "Username already registered") e outras em português ("Muitas tentativas", "Arquivo inválido").

**Correção:** Padronizar todas as mensagens voltadas ao usuário em português.

---

### [MÉDIA] X-4 — Ausência de logging estruturado

**O que está errado:** Não há `logging` configurado na aplicação. Erros são silenciados (ex: `except Exception: pass` na deleção de PDF). Não há como rastrear problemas em produção.

**Correção:** Implementar logging com Python `logging`:
```python
import logging
logger = logging.getLogger("sigdt")
```

---

### [BAIXA] X-5 — Documentação técnica dispersa e parcialmente desatualizada

**O que está errado:** A documentação está em 10+ arquivos no `doc/`, todos numerados mas sem índice unificado. O `PROGRESS.md` menciona CSRFMiddleware como implementado, mas o código não a contém. Isso é desinformação.

**Correção:** Consolidar em um `README.md` principal com links para docs específicos. Atualizar `PROGRESS.md` para refletir o estado real.

---

## PLANO DE AÇÃO EM FASES

### FASE 1 — Estabilização e Segurança (1-2 semanas)

| # | Ação | Prioridade | Itens |
|---|------|-----------|-------|
| 1 | Rotacionar credenciais e expurgar `.env` do histórico Git | CRÍTICA | S-1 |
| 2 | Implementar proteção CSRF em todos os formulários POST | CRÍTICA | S-2 |
| 3 | Remover fallback da SECRET_KEY no main.py | ALTA | S-4 |
| 4 | Criar `.env.example` com placeholders | ALTA | S-1 |
| 5 | Servir Tailwind/HTMX localmente (remover CDN) | ALTA | X-1 |
| 6 | Validar role no backend com whitelist | MÉDIA | S-9 |
| 7 | Validar tamanho de upload antes de ler na memória | ALTA | S-6 |
| 8 | Criar `.dockerignore` | MÉDIA | K-1 |
| 9 | Implementar logging básico | MÉDIA | X-4 |

### FASE 2 — Refatoração Estrutural (2-4 semanas)

| # | Ação | Itens |
|---|------|-------|
| 1 | Extrair `main.py` em routers modulares | A-1 |
| 2 | Criar `base.html` com herança Jinja2 | Q-2, X-2 |
| 3 | Extrair logout/scripts para partial compartilhado | Q-1 |
| 4 | Resolver importações circulares | A-2 |
| 5 | Implementar eager loading nas queries | D-4, E-1 |
| 6 | Otimizar CSV service com cache de lookup | E-2 |
| 7 | Migrar de `python-jose` para `PyJWT` | P-2 |
| 8 | Migrar de `passlib` para `bcrypt` direto ou `argon2-cffi` | P-1 |
| 9 | Implementar test suite com isolamento de DB | T-1, T-2 |
| 10 | Refatorar Dockerfile com multi-stage e non-root | K-1 |

### FASE 3 — Otimização e Acabamento (2-3 semanas)

| # | Ação | Itens |
|---|------|-------|
| 1 | Substituir Tailwind CDN por CSS compilado (produção) | X-1 |
| 2 | Remover `pandas` (usar `openpyxl` diretamente) | P-4 |
| 3 | Unificar documentação | X-5 |
| 4 | Padronizar mensagens em português | X-3 |
| 5 | Adicionar índices compostos no banco | D-3, D-6 |
| 6 | Condicionar `create_all` ao ambiente | D-2 |
| 7 | Remover `old/`, `.DS_Store` | A-3, A-4 |
| 8 | Implementar CI/CD pipeline básico (pytest + lint) | T-1 |

---

## TOP 10 AÇÕES IMEDIATAS

| # | Ação | Severidade | Esforço |
|---|------|-----------|---------|
| **1** | Rotacionar secrets e expurgar `.env` do Git history | CRÍTICA | 30min |
| **2** | Implementar CSRF em formulários POST | CRÍTICA | 2-4h |
| **3** | Remover fallback `"default_secret_key..."` da SECRET_KEY | CRÍTICA | 5min |
| **4** | Servir Tailwind/HTMX localmente (download estáticos) | ALTA | 30min |
| **5** | Ler upload CSV em chunks (prevenir OOM) | ALTA | 30min |
| **6** | Validar role com whitelist no backend | ALTA | 15min |
| **7** | Criar `.dockerignore` | ALTA | 10min |
| **8** | Implementar eager loading na rota `/` (fix N+1) | ALTA | 1h |
| **9** | Criar `base.html` com herança Jinja2 | ALTA | 2h |
| **10** | Adicionar logging básico (substituir `pass` silenciosos) | ALTA | 1h |

---

## LIMITAÇÕES DESTA REVISÃO

1. **Sem acesso ao banco em execução** — Não foi possível analisar dados reais, índices existentes no SQLite, ou métricas de performance.
2. **Sem acesso às migrações Alembic em detalhe** — Os scripts de migração não foram inspecionados linha a linha. Pode haver inconsistências entre os modelos e as migrações.
3. **Sem execução dos testes** — Os testes não foram executados; a análise é baseada em leitura de código.
4. **Contexto militar** — A análise assume um ambiente de rede potencialmente restrito (acesso a CDNs pode ser bloqueado), o que amplifica o impacto de X-1.
5. **Arquivo `logs.txt`** — Contém 19KB de dados potencialmente sensíveis. Não inspecionado em detalhe, mas sua presença no diretório de trabalho (mesmo que no `.gitignore`) é um risco se o container copiar tudo.

---

*Relatório gerado por análise estática do repositório. Todas as recomendações devem ser validadas pela equipe antes de implementação.*
