# Próximos Passos e Bugs (V3.0.0 - Em Desenvolvimento)

Este documento consolida as metas para a Versão 3.0.0, focando em robustez, segurança e persistência de dados administrativos.

---

## 🎯 Sprint Atual: Versão 3.0.0 (Segurança & Infraestrutura)

### 1. Blindagem Global (Anti-CSRF)
*   [ ] **Implementação:** Adicionar `Starlette CSRFMiddleware` ao FastAPI.
*   [ ] **Integração HTMX:** Configurar `hx-headers` em todas as requisições AJAX para incluir o token CSRF.
*   [ ] **Validação:** Garantir que todos os formulários POST (Login, Gatekeeper, Edição, Importação) exijam o token.

### 2. Persistência de Segurança (Rate Limiting)
*   [ ] **Migração:** Substituir o dicionário `login_attempts` em memória por uma tabela no banco de dados (`security_logs`) ou Redis.
*   [ ] **Resiliência:** Garantir que tentativas de força bruta não sejam zeradas após o restart do container.

### 3. Observabilidade (Logging Estruturado)
*   [ ] **Framework:** Implementar `logging` padrão do Python com rotação de arquivos (`TimedRotatingFileHandler`).
*   [ ] **Auditoria:** Registrar eventos críticos: Falhas de login, Ingestão de CSV (sucesso/erro), Erros no AT Parser e Alterações de status por inspetores.

---

## 🚀 Novas Funcionalidades & Casos de Uso (Roadmap V3.x)

- [ ] **Dashboards Visuais:** Integração com Chart.js ou Plotly para gráficos de conformidade e Matriz GUT da frota.
- [ ] **Multi-Tenancy (Bases Operacionais):** Separação lógica de dados por Hangar ou Localização.
- [ ] **Real-Time Locks:** Notificação via WebSocket se dois usuários tentarem editar a mesma diretiva simultaneamente.

---

## 🐛 Bugs Conhecidos & Débitos Técnicos
- [ ] **Performance de Importação:** Otimizar o Upsert de CSV para lotes muito grandes (> 5000 linhas).
- [ ] **Feedback de Erro no Parser:** Melhorar a mensagem de erro quando o PDF não segue o padrão esperado (ex: PDF escaneado sem OCR).
