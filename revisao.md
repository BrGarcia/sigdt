# Revisão Técnica Completa — SIGDT v3.0.0-dev

## Diagnóstico Geral

O SIGDT é um sistema funcional e bem estruturado para o seu escopo. A stack (FastAPI + HTMX + Tailwind + PostgreSQL) é adequada. Entretanto, há problemas que impedem uma operação confiável em produção, especialmente em segurança e manutenibilidade. Abaixo, cada problema é listado com sua prioridade, risco, impacto e correção recomendada.

---

## 🔴 PRIORIDADE CRÍTICA

### C1. Dependências não pinadas — Build não-reprodutível

| Item | Detalhe |
|---|---|
| **Arquivo** | `requirements.txt` |
| **O que está errado** | Nenhuma dependência tem versão fixa (exceto `bcrypt==3.2.2`). O Docker instala `fastapi==0.135.2` e `starlette==1.0.0`, que já quebraram o projeto hoje (`TemplateResponse` incompatível). |
| **Risco** | Build quebrado a qualquer momento. Já aconteceu. |
| **Impacto** | Indisponibilidade total do sistema. |
| **Correção** | Pinar todas as versões no `requirements.txt` a partir do `pip freeze` atual. |

### C2. `datetime.now(datetime.timezone.utc)` — Crash em Runtime

| Item | Detalhe |
|---|---|
| **Arquivo** | `app/main.py` (linhas 295 e 313) |
| **O que está errado** | `datetime.now(datetime.timezone.utc)` está errado. O import é `from datetime import datetime, timezone`, então deve ser `datetime.now(timezone.utc)`. Isso causa `AttributeError` ao salvar diretivas. |
| **Risco** | Crash ao atualizar qualquer diretiva. |
| **Correção** | Corrigir para `datetime.now(timezone.utc)` nas linhas 295 e 313. |

### C3. Arquivo `logs.txt` commitável no repositório

| Item | Detalhe |
|---|---|
| **Arquivo** | Raiz do projeto |
| **O que está errado** | O comando anterior tentou criar `logs.txt` na raiz. Não está no `.gitignore`. |
| **Risco** | Logs sensíveis (erros com stack traces) podem ser commitados. |
| **Correção** | Adicionar `logs.txt` ao `.gitignore` e remover se existir. |

---

## 🟠 PRIORIDADE ALTA

### A1. Ausência de proteção CSRF em formulários POST

| Item | Detalhe |
|---|---|
| **Arquivos** | Todos os templates com `<form method="post">` e rotas HTMX `hx-post`/`hx-delete` |
| **O que está errado** | Nenhum formulário possui token CSRF. Qualquer site terceiro pode submeter formulários em nome do usuário autenticado. |
| **Risco** | Ações administrativas (upload CSV, criar/apagar usuários, alterar diretivas) executáveis por ataque CSRF. |
| **Correção** | Implementar middleware CSRF ou tokens manuais. Já planejado no roadmap V3. |

### A2. Gatekeeper com comparação em plaintext

| Item | Detalhe |
|---|---|
| **Arquivo** | `app/main.py` (linha 118) |
| **O que está errado** | `if password == GATEKEEPER_PASSWORD` — comparação direta, vulnerável a timing attack. |
| **Risco** | Possível extração da senha do Gatekeeper por side-channel. |
| **Correção** | Usar `hmac.compare_digest()` ou armazenar hash bcrypt. |

### A3. Cookie do Gatekeeper sem assinatura/criptografia

| Item | Detalhe |
|---|---|
| **Arquivo** | `app/main.py` (linhas 120-128) |
| **O que está errado** | O cookie `gatekeeper_access=granted` é um valor fixo. Qualquer pessoa que conheça esse valor pode bypassar o gatekeeper editando cookies manualmente. |
| **Risco** | Bypass completo da camada de proteção de borda. |
| **Correção** | Assinar o cookie com `SECRET_KEY` (usar `itsdangerous` ou JWT). |

### A4. `main.py` monolítico com ~570 linhas

| Item | Detalhe |
|---|---|
| **Arquivo** | `app/main.py` |
| **O que está errado** | Todas as rotas, filtros, helpers e configuração estão num único arquivo. Viola separação de responsabilidades. |
| **Risco** | Dificuldade de manutenção crescente e conflitos em desenvolvimento paralelo. |
| **Correção** | Extrair em módulos: `app/routes/directives.py`, `app/routes/export.py`, `app/routes/gatekeeper.py`, `app/middleware/rate_limit.py`. |

### A5. Rate Limiter em memória — Não persiste entre deploys

| Item | Detalhe |
|---|---|
| **Arquivo** | `app/main.py` (linhas 63-74) |
| **O que está errado** | `login_attempts = defaultdict(list)` é in-memory. Reinicia com cada deploy/restart. Com múltiplos workers, cada um tem seu próprio contador. |
| **Risco** | Rate limiting ineficaz em produção (Railway usa restarts frequentes). |
| **Correção** | Migrar para Redis ou tabela no banco. Já planejado no roadmap V3. |

### A6. Validação de entrada insuficiente nos schemas

| Item | Detalhe |
|---|---|
| **Arquivo** | `app/users/schemas.py` |
| **O que está errado** | `UserCreate` aceita qualquer string como username, email e password. Sem validação de comprimento mínimo/máximo, formato de email, ou complexidade de senha. |
| **Risco** | Contas com senhas fracas ("1"), usernames com caracteres especiais, emails inválidos. |
| **Correção** | Adicionar validadores Pydantic: `min_length`, `EmailStr`, regex para username. |

### A7. Valores `status` da diretiva sem validação (enum)

| Item | Detalhe |
|---|---|
| **Arquivo** | `app/main.py` (linha 275), `app/models.py` (linha 36) |
| **O que está errado** | O campo `status` aceita qualquer string via Form. Não há constante/enum definido. Um POST manual pode injetar valores arbitrários. |
| **Risco** | Dados inconsistentes no banco. |
| **Correção** | Criar Enum `StatusDiretiva` e validar no backend. |

---

## 🟡 PRIORIDADE MÉDIA

### M1. Templates HTML sem template base (DRY violation)

| Item | Detalhe |
|---|---|
| **Arquivos** | Todos os 7 templates HTML |
| **O que está errado** | Cada template repete navbar, scripts CDN, e lógica de logout. Uma mudança no menu requer edição em 7 arquivos. |
| **Correção** | Criar `base.html` com Jinja2 `{% block %}` inheritance. |

### M2. Lógica de logout duplicada em JavaScript

| Item | Detalhe |
|---|---|
| **Arquivos** | `index.html`, `directive_details.html`, `user_management.html`, `master_directives.html`, `master_directive_edit.html` |
| **O que está errado** | O mesmo bloco `addEventListener('click', async function() {...})` é copiado 5 vezes. |
| **Correção** | Extrair para `static/js/app.js` incluído via `base.html`. |

### M3. `alembic.ini` aponta para SQLite, não PostgreSQL

| Item | Detalhe |
|---|---|
| **Arquivo** | `alembic.ini` (linha 87) |
| **O que está errado** | `sqlalchemy.url = sqlite:///sigdt.db` — hardcoded para SQLite. Em produção usa PostgreSQL via `DATABASE_URL`. Migrações rodadas fora do Docker falharão contra o banco errado. |
| **Correção** | Ler `DATABASE_URL` do ambiente em `migrations/env.py` (já parcialmente feito), mas o `alembic.ini` prevalece se não sobrescrito. Adicionar override no `env.py`. |

### M4. Testes com cobertura mínima e sem isolamento

| Item | Detalhe |
|---|---|
| **Arquivos** | `tests/test_main.py` (2 testes), `tests/test_new_features.py` (4 testes) |
| **O que está errado** | Apenas 6 testes automatizados. Usam banco de produção/desenvolvimento (sem banco separado). `integrity_check.py` usa senha hardcoded (`asdf1234`) que não é a senha real. Nenhum teste de CSV, PDF, export, ou validações de segurança. |
| **Correção** | Configurar `conftest.py` com banco SQLite in-memory, fixtures isoladas. Adicionar testes para CSV importado, exportação XLSX, upload PDF, rate limiting. |

### M5. `integrity_check.py` com senha de teste hardcoded

| Item | Detalhe |
|---|---|
| **Arquivo** | `tests/integrity_check.py` (linha 28) |
| **O que está errado** | `data={"password": "asdf1234"}` — senha fixa que pode não corresponder ao `.env`. |
| **Correção** | Ler do ambiente ou mockar o gatekeeper. |

### M6. `csv_service.py` carrega TODOS os dados na memória

| Item | Detalhe |
|---|---|
| **Arquivo** | `app/services/csv_service.py` (linhas 29-36) |
| **O que está errado** | `todas_aeronaves`, `todas_diretivas`, `todos_links` carrega o banco inteiro na RAM antes de processar. Com crescimento dos dados, isso causa OOM. |
| **Correção** | Usar dicionários incrementais ou fazer consultas sob demanda com cache parcial. |

### M7. Função `sanitize_formula` duplicada

| Item | Detalhe |
|---|---|
| **Arquivos** | `app/main.py` (linha 434), `app/services/csv_service.py` (linha 8) |
| **O que está errado** | Mesma função definida em dois lugares. |
| **Correção** | Mover para `app/utils.py` e importar nos dois locais. |

### M8. Sem logging estruturado

| Item | Detalhe |
|---|---|
| **Arquivos** | Todo o projeto |
| **O que está errado** | Nenhum uso de `logging` do Python. Erros silenciados em vários blocos `except`. Sem auditoria de ações (quem alterou o quê). |
| **Correção** | Configurar `logging` com nível adequado. Loggar ações críticas (login, upload, alteração de diretivas). |

---

## 🟢 PRIORIDADE BAIXA

### B1. Tailwind CSS via CDN — Inadequado para produção

| Item | Detalhe |
|---|---|
| **Arquivos** | Todos os templates |
| **O que está errado** | `<script src="https://cdn.tailwindcss.com">` é um script de desenvolvimento. Carrega ~300KB de JS a cada request. |
| **Correção** | Usar build Tailwind CLI para gerar CSS otimizado (arquivo estático). |

### B2. HTMX via unpkg — Sem controle de integridade

| Item | Detalhe |
|---|---|
| **Arquivos** | `index.html`, `directive_details.html` |
| **O que está errado** | `<script src="https://unpkg.com/htmx.org@1.9.10">` sem atributo `integrity` (SRI). Supply-chain attack possível. |
| **Correção** | Adicionar hash SRI ou servir HTMX como arquivo estático local. |

### B3. Dockerfile sem `.dockerignore`

| Item | Detalhe |
|---|---|
| **Arquivo** | Raiz do projeto |
| **O que está errado** | O `COPY . .` copia `.git/`, `__pycache__/`, testes e documentação para a imagem. Aumenta tamanho e superfície de ataque. |
| **Correção** | Criar `.dockerignore` excluindo `.git`, `tests`, `doc`, `__pycache__`, `*.db`. |

### B4. Modelo `User` expõe `hashed_password` na resposta da API

| Item | Detalhe |
|---|---|
| **Arquivo** | `app/users/routes.py` (linhas 131-133) |
| **O que está errado** | `GET /users/me` retorna `response_model=models.User`, que inclui `hashed_password`. |
| **Correção** | Criar `UserRead` schema sem `hashed_password` e usar como `response_model`. |

### B5. `BATCH_SIZE = 500` declarado mas nunca ajustado documentadamente

| Item | Detalhe |
|---|---|
| **Arquivo** | `app/services/csv_service.py` (linha 26) |
| **O que está errado** | O doc de segurança (`10_REVISAO_SEGURANCA.txt`) diz "lotes de 100", mas o código usa 500. Inconsistência documentação × código. |
| **Correção** | Alinhar documentação com código. |

### B6. `.gitignore` lista `.env` mas `.env` já está no repositório

| Item | Detalhe |
|---|---|
| **Arquivo** | `.gitignore` e `.env` |
| **O que está errado** | Se `.env` foi rastreado antes de ser adicionado ao `.gitignore`, continua no histórico do Git com todas as senhas. |
| **Correção** | Verificar com `git log -- .env`. Se confirmado, rotacionar todas as credenciais. |

---

## Plano de Ação em Fases

### Fase 1 — Estabilização e Segurança (Correções urgentes)
1. **C1** — Pinar dependências no `requirements.txt`
2. **C2** — Corrigir `datetime.now(timezone.utc)` 
3. **C3** — Adicionar `logs.txt` ao `.gitignore`
4. **A2** — Comparação segura no Gatekeeper (`hmac.compare_digest`)
5. **A3** — Assinar cookie do Gatekeeper
6. **A6** — Validar inputs nos schemas Pydantic
7. **A7** — Criar Enum de status e validar no backend
8. **B4** — Criar `UserRead` schema sem `hashed_password`
9. **B3** — Criar `.dockerignore`

### Fase 2 — Refatoração Estrutural
10. **A4** — Modularizar `main.py` em routers separados
11. **M1/M2** — Criar `base.html` e script compartilhado
12. **M7** — Extrair `sanitize_formula` para `app/utils.py`
13. **M3** — Corrigir Alembic para ler `DATABASE_URL` do ambiente
14. **M8** — Implementar logging estruturado

### Fase 3 — Otimização e Acabamento
15. **M4/M5** — Melhorar infraestrutura de testes
16. **M6** — Otimizar carregamento em massa no CSV service
17. **B1/B2** — Servir assets estáticos localmente (Tailwind build, HTMX local)
18. **B5** — Alinhar documentação com código
19. **B6** — Auditar histórico Git do `.env`

---

## Top 10 — Ações Imediatas

| # | ID | Ação | Severidade |
|---|---|---|---|
| 1 | C1 | Pinar todas as dependências no `requirements.txt` | Crítica |
| 2 | C2 | Corrigir bug `datetime.now(timezone.utc)` | Crítica |
| 3 | A3 | Assinar cookie do Gatekeeper com `SECRET_KEY` | Alta |
| 4 | A2 | Usar `hmac.compare_digest` na comparação do Gatekeeper | Alta |
| 5 | A6 | Validar username/email/senha nos schemas Pydantic | Alta |
| 6 | A7 | Criar Enum de status e bloquear valores arbitrários | Alta |
| 7 | B4 | Ocultar `hashed_password` na resposta de `/users/me` | Baixa |
| 8 | B3 | Criar `.dockerignore` para otimizar build | Baixa |
| 9 | C3 | Adicionar `logs.txt` e arquivos temporários ao `.gitignore` | Crítica |
| 10 | M7 | Eliminar duplicação da função `sanitize_formula` | Média |

---

## Estratégia de Verificação

### Testes Automatizados
```powershell
# Rodar testes existentes dentro do container
docker exec sigdt_web_test pytest tests/ -v
```

### Verificação Manual
1. Acessar `http://localhost:8000/gatekeeper` → verificar que o sistema carrega
2. Fazer login como admin → verificar acesso ao Dashboard com dados
3. Verificar que `GET /users/me` não retorna `hashed_password`  
4. Tentar submeter formulário com status inválido → verificar rejeição

---

> **CONCLUSÃO:** A Fase 1 é executável imediatamente e resolve os problemas que podem causar indisponibilidade ou vulnerabilidades exploráveis. As Fases 2 e 3 são melhorias evolutivas que podem ser implementadas incrementalmente.

---
*Revisão gerada em 26/03/2026 — SIGDT v3.0.0-dev*
