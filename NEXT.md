# Sugestões para Próximos Passos: Projeto SIGDT

O núcleo funcional do sistema (ingestão CSV, Matriz GUT, HTMX) está operacional. Abaixo estão as recomendações para evoluir o sistema para um ambiente de produção:

## 1. Segurança e Acesso (Alta Prioridade)
*   **RBAC (Role-Based Access Control):** Diferenciar usuários comuns (apenas visualização) de administradores (podem fazer upload de CSV e editar Tendência).
*   **Autenticação JWT:** Implementar um sistema de login robusto com tokens expirantes.
*   **Auditoria de Logs:** Registrar quem realizou o upload de cada arquivo CSV e quais mudanças na Matriz GUT foram feitas, com timestamp.

## 2. Experiência do Usuário (UX/UI)
*   **Paginação Server-side:** Atualmente, o sistema carrega os primeiros 100 registros. Para milhares de diretivas, é essencial implementar paginação real no banco de dados para manter a velocidade em máquinas lentas.
*   **Gráficos de Dashboard:** Visualizar a distribuição da frota por classe de gravidade (MANDATÓRIA vs OPCIONAL) usando Chart.js ou similar.
*   **Feedback de Upload:** Mostrar uma barra de progresso ou resumo detalhado (Ex: "100 novos registros inseridos, 24 atualizados").

## 3. Qualidade Técnica
*   **Validação de Esquema Pydantic:** Refinar a validação de dados no momento do upload para garantir que campos críticos não contenham dados inconsistentes.
*   **Suporte a PostgreSQL em Produção:** Garantir que o `docker-compose.yml` esteja 100% configurado para usar o banco de dados oficial fora do ambiente de desenvolvimento.
*   **Testes Unitários:** Aumentar a cobertura de testes para cobrir casos de erro (ex: CSV malformado).

## 4. Funcionalidades de Negócio
*   **Agrupamento por ATA:** Criar abas automáticas ou filtros por especialidade (Capítulos ATA) baseados no PN ou na descrição da tarefa.
*   **Exportação de Relatórios:** Gerar arquivos PDF ou Excel filtrados baseados na prioridade GUT para as equipes de manutenção no hangar.
