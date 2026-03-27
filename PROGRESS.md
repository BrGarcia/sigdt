# PROGRESSO DO PROJETO SIGDT

## Versão 3.5.0-dev (branch: `v3.5.0-dev`)

### Status Atual: Fase 1 — Estabilização e Segurança (em andamento)

#### 📅 27/03/2026 — Correções Críticas (revisao.md Fase 1)
- [x] **C1** — `requirements.txt` reescrito com 22 dependências pinadas via `pip freeze` (build reprodutível).
- [x] **C2** — Corrigido `AttributeError` em `app/main.py` (linhas 292 e 310): `datetime.now(datetime.timezone.utc)` → `datetime.now(timezone.utc)`.
- [x] **C3** — `logs.txt` adicionado ao `.gitignore` (evitar commit de stack traces sensíveis).
- [ ] **A2** — Comparação segura no Gatekeeper (`hmac.compare_digest`)
- [ ] **A3** — Assinar cookie do Gatekeeper com SECRET_KEY
- [ ] **A6** — Validar inputs nos schemas Pydantic
- [ ] **A7** — Criar Enum de status e validar no backend

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
**Referência:** Paramos no Passo 7 do ajuste fino (Projeto FAB).
