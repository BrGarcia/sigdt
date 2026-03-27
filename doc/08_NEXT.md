# Próximos Passos e Bugs (V3.5.0 - Em Desenvolvimento)

Este documento consolida as metas para a Versão 3.5.0, focando em correções de segurança e estabilidade identificadas na revisão técnica (`revisao.md`).

---

## 🎯 Sprint Atual: Versão 3.5.0 (Estabilização e Segurança — Revisão Técnica)

### ✅ Itens Concluídos (V3.5.0)
*   **[A2] Segurança Gatekeeper:** Substituída comparação `==` por `hmac.compare_digest()` contra timing attacks.
*   **[A3] Cookies Assinados:** Cookie do Gatekeeper agora é um JWT assinado com `SECRET_KEY`.
*   **[A6] Validação de Usuários:** Schemas Pydantic reforçados com regex, EmailStr e limites de tamanho.
*   **[A7] Integridade de Status:** Implementado `Enum StatusDiretiva` bloqueando estados inválidos.
*   **[T1] Suíte de Testes:** Criada bateria de testes de integridade e segurança (`pytest`).
*   **Exportação Inteligente:** XLSX vinculado aos filtros do dashboard com nomenclatura dinâmica.
*   **[C1] Build Reprodutível:** `requirements.txt` reescrito com dependências pinadas.
*   **[C2] Bug datetime:** `AttributeError` corrigido em `app/main.py`.
*   **[C3] Logs ignorados:** `logs.txt` no `.gitignore`.

### 1. Fase 2 — Refatoração Estrutural (v3.5.0 posterior)
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
