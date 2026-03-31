# Relatório de Status do Projeto SIGDT (V4.0)

## 📊 Visão Geral
O projeto SIGDT atingiu um marco crítico de estabilidade e maturidade arquitetural com a conclusão da **Refatoração Relacional V4**. O sistema deixou de operar em uma estrutura "flat" (baseada em uma única tabela de diretivas) para um modelo normalizado de alta performance.

## 🛠 Principais Implementações (Fase Atual)

### 1. Refatoração Relacional Completa
A base de dados foi dividida em entidades lógicas para eliminar redundâncias:
- **Aeronave:** Cadastro único de matrículas e números de série.
- **Snapshot:** Rastreabilidade por importação, permitindo auditoria de quando cada dado entrou no sistema.
- **Diretiva Técnica (Mestre):** Dados fixos da diretiva (Código, Objetivo, Classe, Categoria).
- **Item da Diretiva:** Subdivisão técnica da diretiva (FADT, Tarefa, Ordem de Referência).
- **Vínculo Operacional:** Tabela que cruza o Item com a Aeronave, armazenando o Status, GUT e Anexo PDF.

### 2. Identificação Alfanumérica Sanitizada (Simplified PK)
Implementada uma nova lógica de chaves primárias para Diretivas Técnicas:
- **PK:** `codigo_simplificado` (String sanitizada, ex: "BO31400224").
- **Benefício:** Elimina erros de busca e duplicidade causados por espaços, hifens ou variações de digitação no CSV original.
- **Transparência:** O usuário continua visualizando o código original (com espaços e pontuação) nos templates.

### 3. Lógica de Snapshot de Importação
O serviço de importação CSV foi robustecido:
- Cada importação gera um registro de Snapshot.
- **Auditoria Automática:** Itens que constavam no banco para uma aeronave, mas desapareceram do novo arquivo importado, são marcados automaticamente como "Concluídos" com a justificativa: `[AUTO] Concluída via snapshot... Motivo: Item ausente no CSV`.

### 4. Segurança e Permissões
- Refinamento do mapeamento de **Carreiras (Inspetor)** vs. **Áreas Técnicas (Diretiva)**.
- Proteção Anti-CSRF global implementada.
- Gatekeeper (acesso inicial) protegido por JWT assinado.

## 📈 Resultados Alcançados
- **Integridade Referencial:** Impossível existir um vínculo de aeronave sem uma diretiva mestre correspondente.
- **Deduplicação de Dados:** A alteração de um dado mestre (ex: Objetivo da DT) reflete instantaneamente em todas as aeronaves vinculadas.
- **Rastreabilidade:** Agora é possível saber exatamente qual arquivo CSV deu origem a cada registro no banco de dados.

## 📅 Próximos Passos (Próxima Sprint)
1. **Agrupamento no Dashboard:** Exibir diretivas mestras com sub-itens expansíveis para reduzir o ruído visual.
2. **Dashboard Gráfico:** Visualização percentual de conformidade por aeronave.
3. **Evolução do Parser PDF:** Extração automatizada de campos das Fichas AT.
