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

## Versão 4.0.0-dev (branch: `v4.0.0-dev`)

### Status Atual: Refatoração de Banco de Dados Relacional (CONCLUÍDO)

#### 📅 31/03/2026 — Refatoração Estrutural (REFATORACAO_DB_V2.MD)
- [x] **Modelo Relacional** — Implementação de `DiretivaTecnica`, `DiretivaItem` e `DiretivaItemAeronave`.
- [x] **Snapshot Logic** — Criação da tabela `Snapshot` e integração formal no `csv_service.py`.
- [x] **Migração de Dados Robusta** — ETL reescrito para deduplicação e consolidação segura de dados mestres.
- [x] **Runtime Migration** — Aplicação migrada para consumir exclusivamente o novo modelo.
- [x] **Remoção de Legado** — Tabelas e modelos antigos removidos/depreciados.
- [x] **Testes de Integridade** — Suíte de testes atualizada para o novo modelo relacional.

