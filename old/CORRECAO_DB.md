Analisei a modelagem de banco de dados fornecida (arquivo banco_de_dados.md) e proponha uma refatoração completa com foco em normalização, integridade referencial e aderência ao domínio.

Contexto do problema:

* O sistema controla diretivas técnicas aplicadas a aeronaves.
* Atualmente, a tabela "diretiva" contém informações como FADT e tarefas, porém essas informações não são únicas e pertencem a um nível inferior da entidade.
* Uma única diretiva pode possuir múltiplas tarefas e múltiplos FADT associados.
* Existe um CSV externo que representa um snapshot das pendências atuais (itens ativos). Quando um item não aparece no CSV, ele deve ser considerado concluído.
* O sistema precisa evitar duplicidade e garantir rastreabilidade histórica.

Problemas identificados:

* Violação de normalização (mistura de entidade principal com atributos multi-valorados).
* Ausência de separação entre diretiva (entidade mestre) e suas tarefas/FADT.
* Dificuldade de deduplicação e inconsistência na sincronização com o CSV.
* Falta de chave composta adequada para representar unicidade de uma pendência.

Objetivos da refatoração:

1. Separar corretamente as entidades:

   * Diretiva (nível mestre, única)
   * Itens da Diretiva (tarefas/FADT)
   * Relação com aeronave (estado operacional)
2. Garantir unicidade com constraints apropriadas.
3. Permitir sincronização correta com o CSV baseado em snapshot.
4. Preservar histórico (não deletar registros).
5. Preparar o modelo para escalabilidade e auditoria.

Entregáveis esperados:

* Novo modelo relacional completo (DDL SQL ou ORM)
* Definição clara de chaves primárias e constraints UNIQUE
* Relacionamentos (FKs) explicitados
* Justificativa técnica das decisões
* Fluxo de importação do CSV com estratégia de:

  * upsert
  * detecção de itens removidos (soft delete / conclusão)
* Sugestões de índices para performance
* Identificação de riscos e edge cases (ex: duplicidade de FADT, inconsistência de dados)

Requisitos adicionais:

* Aplicar princípios de 3ª forma normal (3NF)
* Evitar redundância de dados
* Utilizar nomenclatura consistente e sem ambiguidade
* Considerar boas práticas de sistemas críticos (auditabilidade e rastreabilidade)

Saída deve ser técnica, objetiva e estruturada.
