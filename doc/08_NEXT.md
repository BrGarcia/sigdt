# Roadmap de Evolução: Projeto SIGDT

O sistema atingiu o estado de MVP estável (v1.0.0). O desenvolvimento agora foca em automatizar a entrada de dados e elevar o nível de controle e integridade das Diretivas Técnicas.

## ✅ Versão 2.0.0 (Foco: Automação e UX de Diretivas) - CONCLUÍDA
*   **AT Parser Inteligente:** Integração do extrator de PDFs (PyMuPDF) para preencher automaticamente os registros de manutenção (Ficha AT, Serviço e Parecer) diretamente na página de detalhes.
*   **Migrações de Banco (Alembic):** Configuração do Alembic para gerenciar o esquema do banco de forma profissional, permitindo evoluir a estrutura das DTs sem risco.
*   **Visualização de PDF Integrada:** Exibição do anexo técnico em um modal interno ao lado dos dados extraídos para conferência imediata.
*   **Filtros de Gestão:** Busca avançada por Especialidade (checkbox múltipla escolha) no Dashboard, visível apenas para usuários logados (admin/inspector).
*   **Melhoria na Importação:** Refinamento da lógica de "Upsert" com cache em memória para garantir que a atualização em massa de DTs via CSV seja rápida e à prova de erros.
*   **Exclusão de Usuários:** Botão de exclusão rápida ("X") de inspetores diretamente na tela de Gerenciamento de Usuários, com proteção contra exclusão do admin.

---

## 🔴 Vulnerabilidades e Falhas Identificadas (Auditoria V2.0.0)

### CRÍTICO – Segurança

1.  **SECRET_KEY hardcoded no código-fonte** (`app/users/security.py:11`)
    O fallback `"a_very_secret_key_change_me_in_production"` é inseguro. Se o `.env` estiver vazio (como está agora), qualquer pessoa que leia o código consegue forjar tokens JWT e se autenticar como admin.
    *Correção:* Exigir a variável de ambiente `SECRET_KEY` no startup e abortar se não estiver definida.

2.  **GATEKEEPER_PASSWORD hardcoded** (`app/main.py:29`)
    O fallback `"asdf1234"` é trivial de adivinhar. A senha do Gatekeeper deveria ser obrigatoriamente fornecida via variável de ambiente.
    *Correção:* Remover o default e exigir `GATEKEEPER_PASSWORD` no `.env`.

3.  **ADMIN_PASSWORD com default fraco** (`app/main.py:56`)
    O fallback `"admin"` permite acesso com senha trivial. Além disso, o hash do admin é recalculado a cada startup, o que é ineficiente.
    *Correção:* Exigir `ADMIN_PASSWORD` via variável de ambiente, sem fallback.

4.  **Cookies sem `secure=True`** (`app/main.py:93`, `app/users/routes.py:98`)
    Os cookies de autenticação (`gatekeeper_access`, `access_token`) estão com `secure=False`. Se acessado via HTTP em rede, os tokens podem ser interceptados.
    *Correção:* Usar variável de ambiente `ENVIRONMENT` e setar `secure=True` automaticamente em produção.

5.  ~~**Rota `/export/xlsx` sem autenticação**~~ ✅ CORRIGIDO
    Adicionado `dependencies=[Depends(get_current_user)]` e o botão de exportar foi ocultado no HTML para visitantes.

6.  ~~**Rota `/directives` (HTMX) sem proteção gatekeeper**~~ ✅ CORRIGIDO
    Adicionado `check_gatekeeper(request)` retornando HTTP 403 caso o cookie não esteja presente.

### ALTO – Integridade de Dados

7.  **Rate limiter em memória não persiste entre reinícios** (`app/main.py:34`)
    O dicionário `login_attempts` é perdido quando o servidor reinicia, permitindo ataques de força bruta intermitentes.
    *Nota:* Aceitável para MVP em hardware limitado, mas deve migrar para Redis ou SQLite nas versões futuras.

8.  ~~**Upload de CSV sem validação de conteúdo**~~ ✅ CORRIGIDO
    Adicionada verificação de colunas obrigatórias (`MATR`, `SN`, `FADT`, `DIRETIVA TÉCNICA`) e limite de tamanho de 50MB antes do processamento.

9.  ~~**Extensão de arquivo PDF não validada contra whitelist**~~ ✅ CORRIGIDO
    Extensão do arquivo enviado pelo cliente agora é ignorada; o sistema sempre salva com extensão `.pdf` forçada.

10. **Sem proteção CSRF** (global)
    O projeto depende de cookies para autenticação (JWT + Gatekeeper), mas não implementa proteção CSRF. Formulários POST podem ser forjados por sites maliciosos.
    *Correção:* Implementar token CSRF em todos os formulários ou usar header customizado para requisições HTMX.

### MÉDIO – Qualidade de Código  

11. ~~**Campo `link.diretiva.pn` referenciado mas não existe no modelo**~~ ✅ CORRIGIDO
    Referência removida do export XLSX. A coluna `PN` foi excluída da planilha exportada.

12. ~~**Contagem ineficiente de registros para paginação**~~ ✅ CORRIGIDO
    Substituído `len(session.exec().all())` por `select(func.count()).select_from(statement.subquery())`.

13. ~~**`datetime.utcnow()` depreciado**~~ ✅ CORRIGIDO
    Migrado para `datetime.now(timezone.utc)` em `main.py`, `models.py` e `security.py`.

14. **Ausência de logging estruturado**
    Não há sistema de logging centralizado. Erros no PDF parser, CSV service e autenticação são silenciosos ou dependem do echo do SQLAlchemy.
    *Correção:* Implementar `logging` com rotação de arquivos.

---

## 🏗️ Versão 3.0.0 (Foco: Segurança e Robustez)

### Segurança
*   **Variáveis de Ambiente Obrigatórias:** Exigir `SECRET_KEY`, `GATEKEEPER_PASSWORD` e `ADMIN_PASSWORD` no startup. Abortar execução se ausentes.
*   **Cookies Seguros em Produção:** Flag `secure=True` e `httponly=True` automáticos via flag `ENVIRONMENT=production`.
*   **Proteção CSRF:** Implementar token anti-CSRF em todos os formulários POST/DELETE.
*   **Autenticação no Export XLSX:** Restringir exportação apenas a inspetores e admins autenticados.
*   **Whitelist de Extensões de Upload:** Forçar `.pdf` no salvamento, ignorando extensão do cliente.

### Integridade de Dados
*   **Validação de CSV:** Checar colunas obrigatórias, limitar tamanho do arquivo (ex: 50MB), e retornar relatório de erros por linha.
*   **Validação de Formulários (Backend):** Usar Pydantic models para validar todos os inputs de formulário (status, observações, etc.) com constraints explícitos.
*   **Transações Atômicas:** Garantir que falhas parciais no upload CSV façam rollback completo.

### Performance
*   **Paginação com COUNT otimizado:** Usar `func.count()` com subquery ao invés de carregar todos os registros.
*   **Índices de Banco:** Revisar e adicionar índices compostos para queries frequentes (aeronave_id + diretiva_id, status + especialidade).
*   **Cache de Sessão:** Avaliar cache de leitura (Redis ou lru_cache) para queries repetitivas do dashboard.

### UX e Funcionalidades
*   **Notificações Visuais (Toast):** Feedback visual ao salvar, deletar ou importar (ex: "Salvo com sucesso!" animado).
*   **Filtro por Status no Dashboard:** Re-implementar como checkboxes (similar às especialidades), visível apenas para usuários logados.
*   **Paginação HTMX:** Migrar paginação do dashboard para HTMX, evitando reload da página inteira.
*   **Edição Inline de Tendência:** Permitir alterar tendência GUT diretamente na tabela do dashboard sem abrir detalhes.

---

## 🔮 Versão 4.0.0 (Foco: Governança e Inteligência)
*   **Histórico de Revisão de DTs:** Implementação de controle de revisões (ex: REV 01, REV 02) para as normas técnicas globais, permitindo ver o que mudou na diretiva ao longo do tempo.
*   **Logs de Auditoria:** Registro detalhado de quem alterou o status ou os dados de uma DT, criando uma trilha de responsabilidade técnica.
*   **Assinatura Digital / Validação:** Sistema de confirmação de identidade (senha ou token) para validar formalmente a conclusão de uma diretiva no sistema.
*   **Dashboard de Conformidade:** Relatórios visuais focados no percentual de cumprimento das DTs por aeronave e por especialidade.
*   **Backup e Segurança:** Rotinas automatizadas de preservação dos dados e anexos técnicos em ambiente de nuvem.
*   **Parser Inteligente com IA:** Uso de LLM local para extrair campos de PDFs que não seguem o padrão AT esperado.
*   **Relatórios PDF Automáticos:** Geração de relatórios técnicos em PDF com os dados consolidados do sistema.

---
*Última atualização: 21 de Março de 2026 — Auditoria V2.0.0*
