# Sugestões para Próximos Passos: Projeto SIGDT

O sistema atingiu o estado de MVP (v1.0.0-pre). Abaixo estão as recomendações para as próximas versões:

## 1. Auditoria e Conformidade (Alta Prioridade)
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
*   **Gestão de Componentes:** Expandir o sistema para controlar não apenas a aeronave, mas seus componentes (motores, APU, hélice) de forma independente.
