# Sugestões para Próximos Passos: Projeto SIGDT (v2.0.0)

O sistema atingiu o estado de MVP estável (v1.0.0). Agora, o foco é na automação e inteligência de dados.

## 1. Automação de Dados (Foco v2.0)
*   **AT Parser Inteligente:** Finalizar a integração do extrator de PDFs para preencher automaticamente os registros de manutenção.
*   **Deduplicação Inteligente:** Refinar o algoritmo para garantir que textos repetidos em PDFs multipáginas não sujem o banco de dados.
*   **Migrações de Banco (Alembic):** Configurar migrações para suportar os novos campos de Assessoramento Técnico sem perda de dados históricos.

## 2. Auditoria e Conformidade (Alta Prioridade)
*   **Logs de Auditoria:** Registrar o histórico de quem alterou o status de uma diretiva e quando.
*   **Assinatura Digital:** Implementar uma confirmação de senha ou assinatura digital simples ao concluir uma DT.
*   **Dashboard de Conformidade:** Gráficos mostrando a porcentagem de diretivas concluídas por aeronave.

## 2. Melhorias de Interface (UX/UI)
*   **Filtros Avançados:** Filtros por Especialidade e por Status no Dashboard principal.
*   **Notificações:** Alertas visuais para diretivas que estão próximas do prazo de vencimento.
*   **Visualização de PDF Integrada:** Abrir o PDF em um modal/janela interna em vez de uma nova aba.

## 3. Qualidade Técnica
*   **Migrações de Banco (Alembic):** Configurar migrações automáticas para facilitar futuras mudanças na estrutura do banco de dados sem perder dados.
*   **Backup Automático:** Script para backup diário do banco de dados PostgreSQL.
*   **Testes de Carga:** Validar a performance com uma base de dados de 10.000+ registros.

## 4. Evolução do Negócio
*   **Versionamento de DTs:** Controle de revisões (REV) das diretivas técnicas.
*   **Cadastro de Usuários (Self-Registration):** Permitir que novos usuários se cadastrem no sistema para que suas senhas sejam pessoais e seguras, eliminando a necessidade de o administrador criar senhas iniciais.
*   **Gestão de Componentes:** Expandir o sistema para controlar não apenas a aeronave, mas seus componentes (motores, APU, hélice) de forma independente.
