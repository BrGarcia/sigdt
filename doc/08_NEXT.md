# Roadmap de Evolução (SIGDT)

Este documento consolida as metas alcançadas e os próximos passos para o SIGDT.

---

## ✅ Versão 3.0.0 (Segurança & Infraestrutura) - CONCLUÍDA
Foco em robustez, segurança e persistência de dados administrativos.

- [x] **Blindagem Global (Anti-CSRF):** Middleware CSRF implementado com tokens integrados em HTMX e formulários tradicionais.
- [x] **Persistência de Segurança:** Rate limiting de login e gatekeeper migrado para banco de dados (`SecurityLog`).
- [x] **Centralização de Especialidades:** Criada classe `Especialidade` (fonte da verdade) e filtros dinâmicos em todos os templates.
- [x] **Observabilidade (Logging Estruturado):** Implementado logging com rotação de arquivos e auditoria de eventos críticos.
- [x] **Inserção Manual:** Funcionalidade de cadastro individual de diretivas com lógica de Upsert.

---

## 🎯 Sprint Atual: Versão 3.1.0 (Usabilidade & Performance)

### 1. Performance de Dados
- [ ] **Otimização de Importação:** Implementar processamento em background (ou lotes maiores) para CSVs com > 5000 linhas.
- [ ] **Cache de Dashboard:** Implementar cache simples para a contagem de páginas e estatísticas do dashboard.

### 2. Interface e UX
- [ ] **Feedback de Erro no Parser:** Melhorar a mensagem de erro quando o PDF não segue o padrão (ex: sem OCR ou formato inválido).
- [ ] **Confirmação de Ações:** Adicionar modais de confirmação via HTMX para exclusão de anexos e usuários.
- [ ] **Busca Avançada:** Adicionar filtros por intervalo de datas e range de GUT.

---

## 🚀 Próximas Fases (Roadmap de Longo Prazo)

- [ ] **Dashboards Visuais:** Integração com Chart.js para visualização da Matriz GUT da frota.
- [ ] **Multi-Tenancy:** Separação lógica de dados por Base Operacional (Hangar).
- [ ] **Notificações:** Alertas de diretivas críticas (GUT > 15) via E-mail ou Telegram.

---

## 🐛 Bugs Conhecidos & Débitos Técnicos
- [ ] **Refactor Templates:** Criar um `base.html` para evitar repetição de scripts (CSRF, Logout) em todos os templates.
- [ ] **Testes de Unidade:** Expandir a cobertura de testes para os novos serviços de log e constantes.
