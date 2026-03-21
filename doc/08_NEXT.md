# Próximos Passos e Bugs (V3.0.0 e Versões Futuras)

Este documento consolida as falhas não sanadas na Versão 2.0.0 em virtude de requererem implementações de middlewares extras pesados, e propõe o Roadmap claro para o prosseguimento futuro do projeto.

---

## Auditoria de Segurança - Remanescentes

### 1. Sem proteção CSRF (global)
**Ameaça (Alto):** O projeto depende de cookies para autenticação (JWT + Gatekeeper), mas não implementa proteção CSRF nativa robusta a um nível global. Formulários POST podem ser forjados se rodando em subdomínios expostos ou cliques maliciosos.
**Correção Planejada (V3.0.0):** Implementar um middleware padrão CSRF (ex: `Starlette CSRFMiddleware`) e despachar tokens no Front-End dentro do escopo HTMX (`hx-headers`).

### 2. Dicionário `login_attempts` em Memória Volátil
**Ameaça (Médio):** A mitigação de Força Bruta atual zera contagens caso o container sofra restart, permitindo ataques intercalados com desligamentos.
**Correção Planejada (V3.0.0):** Trocar em-memória (Dict Python) por armazenamento persistente (Redis cache ou SQLite atrelado).

### 3. Ausência de logging centralizado estruturado
**Ameaça (Baixo):** Erros no parser (PyMuPDF) e no importador CSV caem inertes, exigindo busca cega via console (stdout) para depuração.
**Correção Planejada:** Aplicar o framework de Logging standard (`import logging`) injetando arquivos de texto rotativos no servidor de produção.

---

## Novos Casos de Uso Esperados

- [ ] **Integração Real-Time:** WebSocket para aviso se dois inspetores estão editando a mesma aeronave simultaneamente.
- [ ] **Multi-Ambientes (Hangar X / Y):** Dividir a base de dados em instâncias para bases operacionais independentes sem cruzar dados de aviões de hangares ou localizações distintas.
- [ ] **Camada Visual:** Gráficos e Analytics unificados gerados sobre as tendências e GUT da frota.
