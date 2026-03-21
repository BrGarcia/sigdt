# Roadmap de Evolução: Projeto SIGDT

O sistema atingiu o estado de MVP estável (v1.0.0). O desenvolvimento agora foca em automatizar a entrada de dados e elevar o nível de controle e integridade das Diretivas Técnicas.

## 🚀 Versão 2.0.0 (Foco: Automação e UX de Diretivas) - ATUAL
*   **AT Parser Inteligente:** Integração do extrator de PDFs (PyMuPDF) para preencher automaticamente os registros de manutenção (Ficha AT, Serviço e Parecer) diretamente na página de detalhes.
*   **Migrações de Banco (Alembic):** Configuração do Alembic para gerenciar o esquema do PostgreSQL de forma profissional, permitindo evoluir a estrutura das DTs sem risco.
*   **Visualização de PDF Integrada:** Exibição do anexo técnico em um modal interno ao lado dos dados extraídos para conferência imediata.
*   **Filtros de Gestão:** Busca avançada por Especialidade e Status no Dashboard para facilitar o controle da frota.
*   **Melhoria na Importação:** Refinamento da lógica de "Upsert" para garantir que a atualização em massa de DTs via CSV seja rápida e à prova de erros.

## 🏗️ Versão 3.0.0 (Foco: Governança e Integridade das DTs)
*   **Histórico de Revisão de DTs:** Implementação de controle de revisões (ex: REV 01, REV 02) para as normas técnicas globais, permitindo ver o que mudou na diretiva ao longo do tempo.
*   **Logs de Auditoria:** Registro detalhado de quem alterou o status ou os dados de uma DT, criando uma trilha de responsabilidade técnica.
*   **Assinatura Digital / Validação:** Sistema de confirmação de identidade (senha ou token) para validar formalmente a conclusão de uma diretiva no sistema.
*   **Dashboard de Conformidade:** Relatórios visuais focados no percentual de cumprimento das DTs por aeronave e por especialidade.
*   **Gestão de Acesso Individual:** Substituição da senha global por contas individuais para cada militar, com níveis de permissão específicos para cada DT.
*   **Backup e Segurança:** Rotinas automatizadas de preservação dos dados e anexos técnicos em ambiente de nuvem.

---
*Última atualização: Março de 2026*
