# Próximos Passos e Bugs (V3.5.0 - Em Desenvolvimento)

Este documento consolida as metas para a Versão 3.5.0, focando em correções de segurança e estabilidade identificadas na revisão técnica (`revisao.md`).

---

## 🎯 Sprint Atual: Versão 3.5.0 (Estabilização e Segurança — Revisão Técnica)

### ✅ Itens Concluídos
*   **Exportação Inteligente:** Implementada a exportação XLSX vinculada aos filtros do dashboard.
*   **Nomenclatura Dinâmica:** Arquivos gerados agora herdam o nome do termo de busca aplicado.
*   **Enriquecimento de Dados:** Adicionado o campo `Objetivo` (descrição técnica) no relatório exportado.
*   **[C1] Build Reprodutível:** `requirements.txt` reescrito com 22 dependências pinadas (`pip freeze`).
*   **[C2] Bug datetime corrigido:** `AttributeError` em runtime ao salvar diretivas eliminado (`timezone.utc`).
*   **[C3] Logs ignorados:** `logs.txt` adicionado ao `.gitignore`.

### 🔴 Fase 1 — Segurança (pendente)
*   [ ] **[A2]** Gatekeeper: substituir comparação `==` por `hmac.compare_digest()`.
*   [ ] **[A3]** Cookie do Gatekeeper: assinar com `SECRET_KEY` via `itsdangerous`.
*   [ ] **[A6]** Schemas Pydantic: validar `min_length`, `EmailStr`, regex para username e complexidade de senha.
*   [ ] **[A7]** Campo `status`: criar `Enum StatusDiretiva` e bloquear valores arbitrários no backend.


### 2. Fase 2 — Refatoração Estrutural (v3.5.0 posterior)
*   [ ] **[A4]** Modularizar `main.py` em routers separados (`routes/directives.py`, `routes/gatekeeper.py`).
*   [ ] **[M1/M2]** Criar `base.html` com herança Jinja2 e script compartilhado.
*   [ ] **[M7]** Extrair `sanitize_formula` duplicada para `app/utils.py`.
*   [ ] **[M3]** Corrigir `alembic.ini` para ler `DATABASE_URL` do ambiente.
*   [ ] **[M8]** Implementar logging estruturado com auditoria de ações.

---

## 🚀 Novas Funcionalidades & Casos de Uso (Roadmap V3.x)

- [ ] **Dashboards Visuais:** Integração com Chart.js ou Plotly para gráficos de conformidade e Matriz GUT da frota.
- [ ] **Multi-Tenancy (Bases Operacionais):** Separação lógica de dados por Hangar ou Localização.
- [ ] **Real-Time Locks:** Notificação via WebSocket se dois usuários tentarem editar a mesma diretiva simultaneamente.

---

## 🐛 Bugs Conhecidos & Débitos Técnicos
- [ ] **Performance de Importação:** Otimizar o Upsert de CSV para lotes muito grandes (> 5000 linhas).
- [ ] **Feedback de Erro no Parser:** Melhorar a mensagem de erro quando o PDF não segue o padrão esperado (ex: PDF escaneado sem OCR).
