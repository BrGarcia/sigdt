# PROGRESSO DO PROJETO SIGDT

## Versão 3.5.0 (branch: `v3.5.0-dev`)

### Status Atual: Fase 1 — Estabilização e Segurança (CONCLUÍDO)

#### 📅 27/03/2026 — Correções Críticas (revisao.md Fase 1)
- [x] **C1** — `requirements.txt` reescrito com 22 dependências pinadas via `pip freeze` (build reprodutível).
- [x] **C2** — Corrigido `AttributeError` em `app/main.py` (linhas 292 e 310): `datetime.now(datetime.timezone.utc)` → `datetime.now(timezone.utc)`.
- [x] **C3** — `logs.txt` adicionado ao `.gitignore` (evitar commit de stack traces sensíveis).
- [x] **A2** — Comparação segura no Gatekeeper (`hmac.compare_digest`)
- [x] **A3** — Assinar cookie do Gatekeeper com SECRET_KEY (JWT)
- [x] **A6** — Validar inputs nos schemas Pydantic (UserCreate com validações robustas)
- [x] **A7** — Criar Enum de status e validar no backend (StatusDiretiva)
- [x] **T1** — Suíte de testes automatizados (Pytest + Integrity Check)


#### 📅 Observaçoes feitas pelo usuario:
- [x] Sincronização de especialidades (Carreira vs. Área Técnica).
- [x] Mapeamento de permissões implementado (Baseado na tabela de carreiras).



---

## Versão 3.0.0-dev (concluída)

#### 📅 26/03/2026
- [x] Refatoração da lógica de filtragem para reuso (`apply_filters`).
- [x] Atualização da rota `/export/xlsx` para aceitar parâmetros de busca e especialidade.
- [x] Sincronização em tempo real do link de exportação no frontend via JavaScript.
- [x] Implementação de nomes de arquivos dinâmicos baseados no termo de busca.
- [x] Adição da coluna `OBJETIVO` (descrição técnica) no relatório exportado.
- [x] Implementação de proteção Anti-CSRF global (`CSRFMiddleware`).
- [x] Rate Limiting in-memory com janela deslizante (5 tentativas / 60s).

---

## Versão 4.3.0 (branch: `v4.3.0-performance`)

### Status Atual: Fase 3 — Performance e Validação (CONCLUÍDO)

#### 📅 01/04/2026 — Otimização e Eager Loading (RELATORIO_FINAL.MD Fase 3)
- [x] **Eliminação de N+1 no CSV** — Implementação de Lookups em memória (`item_cache`, `link_cache`) no `csv_service.py`.
- [x] **Eager Loading no Dashboard** — Utilização de `selectinload` para carregar Aeronaves e Diretivas em uma única query.
- [x] **Redução de I/O de Banco** — Remoção de `session.exec` dentro do loop principal de importação.
- [x] **Validação de Performance** — Criação de `tests/test_performance.py` validando importação de 1000+ linhas em sub-segundos.
- [x] **Suíte de Testes Integrada** — Todos os 14 testes (incluindo performance) passando com sucesso.

---

## Versão 4.2.0 (branch: `v4.2.0-refactor`)

### Status Atual: Fase 2 — Integridade Arquitetural e Refatoração (CONCLUÍDO)

#### 📅 01/04/2026 — Modularização e Unificação (RELATORIO_FINAL.MD Fase 2)
- [x] **Modularização do Backend** — `main.py` decomposto em `app/core/` (config/templates) e `app/routers/` (auth/directives/admin).
- [x] **Unificação do Frontend** — Implementação de `base.html` com herança Jinja2, eliminando duplicação de Navbar e Scripts.
- [x] **Gestão de Banco de Dados** — Remoção de `create_all()` do startup flow, delegando gestão de schema exclusivamente ao Alembic.
- [x] **Dependências Locais** — HTMX internalizado em `app/static/js/` para suporte a ambientes offline.
- [x] **Resolução de Dependências Circulares** — Refatoração de `app/users/routes.py` para usar módulos `core`.

---

## Versão 4.1.0 (branch: `v4.1.0-security`)

### Status Atual: Fase 1 — Estabilização e Segurança Crítica (CONCLUÍDO)

#### 📅 01/04/2026 — Sanitização e Proteção (RELATORIO_FINAL.MD Fase 1)
- [x] **Sanitização de Segredos** — Remoção de fallbacks de `SECRET_KEY`, rotação de senhas e limpeza de docs.
- [x] **Proteção Anti-CSRF** — Implementação de `CSRFMiddleware` global e integração em todos os formulários/HTMX.
- [x] **Bootstrap Idempotente** — Criação do usuário `admin` não reseta mais a senha a cada boot.
- [x] **Proteção de Anexos** — Uploads movidos para `app/uploads` e servidos via rota autenticada.
- [x] **Depuração de Histórico** — `.env` removido do rastreamento (recomenda-se purge de histórico se exposto publicamente).

---

## Versão 4.0.0-dev (branch: `v4.0.0-dev`)

### Status Atual: Refatoração de Banco de Dados Relacional (CONCLUÍDO)

#### 📅 31/03/2026 — Refatoração Estrutural (REFATORACAO_DB_V2.MD)
- [x] **Modelo Relacional** — Implementação de `DiretivaTecnica`, `DiretivaItem` e `DiretivaItemAeronave`.
- [x] **Snapshot Logic** — Criação da tabela `Snapshot` e integração formal no `csv_service.py`.
- [x] **Migração de Dados Robusta** — ETL reescrito para deduplicação e consolidação segura de dados mestres.
- [x] **Runtime Migration** — Aplicação migrada para consumir exclusivamente o novo modelo.
- [x] **Remoção de Legado** — Tabelas e modelos antigos removidos/depreciados.
- [x] **Simplified PKs** — Implementação de `codigo_simplificado` como Chave Primária String para `DiretivaTecnica`.
- [x] **Sanitização de Códigos** — Lógica para limpar espaços e símbolos de códigos de diretivas durante a importação.
- [x] **Testes de Integridade** — Suíte de testes atualizada para o novo modelo relacional e PKs simplificadas.

