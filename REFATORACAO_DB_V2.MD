# REFATORACAO_DB_V2

## Objetivo

Este documento registra as falhas observadas na refatoração descrita em `RESUMO_REFATORACAO_V4.md` e define o que precisa ser feito para que a correção do banco seja implementada de forma adequada no projeto.

O problema principal não é conceitual. A direção da refatoração está correta:

- `Diretiva Técnica` como entidade mestre;
- `FADT` e `Tarefa` como itens subordinados;
- estado operacional por aeronave em nível separado.

O problema está na execução parcial e na ausência de fechamento técnico da migração.

---

## 1. Resumo executivo

A implementação atual introduziu o novo schema, mas não concluiu a transição do sistema para esse schema.

Em termos práticos:

- o banco novo foi parcialmente modelado;
- a migração de dados foi iniciada;
- a infraestrutura Alembic foi parcialmente corrigida;
- porém a aplicação continua operando no modelo legado;
- o importador CSV continua reforçando a modelagem antiga;
- a migração de dados ainda tem risco de inconsistência e falha por duplicidade.

Conclusão:

- a refatoração atual não pode ser considerada adequada nem concluída;
- ela deve ser tratada como uma etapa intermediária de preparação.

---

## 2. Falhas observadas

## 2.1 O sistema principal ainda usa o modelo legado

Embora `DiretivaTecnica`, `DiretivaItem` e `DiretivaItemAeronave` tenham sido adicionadas ao ORM, a aplicação principal continua operando com:

- `Diretiva`
- `DiretivaAeronave`

Impacto:

- dashboard continua listado a partir do vínculo antigo;
- detalhes da diretiva continuam lendo o modelo antigo;
- exportação XLSX continua puxando `fadt` da entidade errada;
- edição de master directive continua alterando `Diretiva` legada;
- nenhuma funcionalidade principal consome o novo modelo.

Consequência:

- o comportamento real do sistema ainda está baseado na regra antiga;
- a regra de negócio correta ainda não passou a vigorar.

O que deve ser feito:

1. Refatorar todas as consultas de leitura para usar `DiretivaItemAeronave`.
2. Refatorar telas e templates para separar:
   - dados da diretiva técnica;
   - dados do item da diretiva;
   - dados operacionais da aeronave.
3. Refatorar a tela `/master-directives` para operar sobre `DiretivaTecnica`.
4. Eliminar dependência funcional de `Diretiva` e `DiretivaAeronave`.

---

## 2.2 O importador CSV continua errado do ponto de vista de negócio

O arquivo `app/services/csv_service.py` continua:

- fazendo upsert da diretiva por `fadt`;
- tratando `fadt` como chave de identidade;
- criando/atualizando `Diretiva` legada;
- criando/atualizando `DiretivaAeronave` legada.

Impacto:

- a refatoração não atinge o fluxo mais importante do sistema;
- novos dados continuam entrando no modelo errado;
- mesmo com schema novo, a base continua sendo alimentada pela lógica antiga.

Consequência:

- a distorção do domínio permanece;
- a migração nunca se estabiliza, porque o legado continua sendo a origem viva.

O que deve ser feito:

1. Reescrever completamente `process_csv`.
2. Passar a resolver a diretiva mestre por `codigo_diretiva`.
3. Criar ou localizar `DiretivaItem` por uma chave técnica determinística.
4. Criar ou atualizar `DiretivaItemAeronave` por `(aeronave_id, diretiva_item_id)`.
5. Parar de usar `fadt` como chave principal do fluxo.

---

## 2.3 Não houve implementação da lógica de snapshot

O plano de negócio exige:

- tratar o CSV como fotografia do estado atual;
- marcar itens ausentes como concluídos ou encerrados automaticamente;
- manter rastreabilidade dessa decisão.

A implementação atual apenas faz upsert.

Impacto:

- itens que somem do CSV continuam indefinidamente ativos no banco;
- o sistema não reflete o estado operacional real;
- os campos novos `origem_status`, `ultima_referencia_snapshot` e `concluida_automaticamente` existem, mas ainda não são usados de forma funcional.

Consequência:

- a principal melhoria prometida pela nova modelagem não foi entregue.

O que deve ser feito:

1. Definir formalmente que cada CSV representa um snapshot por aeronave.
2. Criar controle de execução de importação:
   - `snapshot_id`;
   - data/hora;
   - nome do arquivo;
   - aeronave correspondente.
3. Marcar cada `DiretivaItemAeronave` encontrada com o `snapshot_id` corrente.
4. Ao final da importação da aeronave, localizar itens não encontrados naquele snapshot.
5. Marcar esses itens como concluídos automaticamente, sem apagar histórico.

---

## 2.4 A migração de dados pode falhar por duplicidade de item

A migration `1d3fc7e34187` cria `DiretivaItem` com constraint de unicidade:

- `UNIQUE(diretiva_tecnica_id, chave_item)`

Mas o ETL atual insere um item para cada linha legada sem deduplicação prévia.

Impacto:

- se existirem dois registros legados com mesma chave lógica, a migração quebra;
- o banco pode ficar em estado parcialmente migrado, dependendo do ambiente e da forma de execução.

Consequência:

- a migration não é robusta para dados reais;
- ela pressupõe limpeza prévia que não está garantida.

O que deve ser feito:

1. Reescrever a migration de dados para deduplicar `DiretivaItem` antes do insert.
2. Agrupar por:
   - `codigo_diretiva`
   - chave lógica do item
3. Inserir apenas um registro por item único.
4. Criar relatório de colisões e conflitos encontrados.
5. Só depois reconstruir `DiretivaItemAeronave`.

---

## 2.5 A consolidação dos dados mestres está frágil

Na migration atual, a tabela `diretiva_tecnica` é populada por agrupamento em `codigo_diretiva`, usando `MAX(...)` para selecionar campos como:

- `objetivo`
- `classe`
- `categoria`
- `tipo`
- `natureza`
- `especialidade`

Impacto:

- `MAX(...)` não representa regra de negócio;
- em caso de divergência entre registros legados, a escolha do valor final é arbitrária;
- perde-se previsibilidade e auditabilidade.

Consequência:

- o registro mestre consolidado pode ficar semanticamente errado;
- diferenças históricas podem ser apagadas sem rastreio.

O que deve ser feito:

1. Definir critério explícito de consolidação do mestre.
2. Preferir uma destas abordagens:
   - escolher o registro mais recente, se houver metadado confiável;
   - escolher o registro mais completo;
   - bloquear a migração automática quando houver conflito crítico.
3. Gerar relatório de conflitos por `codigo_diretiva`.
4. Registrar os conflitos para revisão manual quando necessário.

---

## 2.6 O resumo de status da refatoração está otimista demais

O arquivo `RESUMO_REFATORACAO_V4.md` descreve a implementação como se a etapa de schema e migração de dados estivesse concluída de forma suficiente.

Isso não corresponde ao estado real porque:

- a aplicação não roda sobre o novo modelo;
- a importação ainda usa o legado;
- a lógica de snapshot não existe;
- a migração de dados ainda não é robusta contra duplicidade;
- não há evidência de validação completa fim a fim.

Impacto:

- falsa sensação de conclusão;
- risco de avançar para produção com um sistema híbrido inconsistente.

O que deve ser feito:

1. Reclassificar o status como:
   - schema novo introduzido;
   - migração de dados preliminar criada;
   - transição funcional ainda não concluída.
2. Atualizar a documentação para refletir o estado real.

---

## 2.7 O legado foi mantido, mas sem estratégia explícita de desativação

Hoje coexistem:

- modelo novo;
- modelo legado;
- fluxo principal ainda no legado.

Isso é aceitável como transição, mas só se houver plano explícito de retirada.

Impacto:

- alto risco de drift entre as duas estruturas;
- manutenção duplicada;
- futuras alterações podem atingir apenas metade do sistema.

Consequência:

- o projeto pode ficar preso em estado híbrido indefinidamente.

O que deve ser feito:

1. Definir uma fase formal de compatibilidade temporária.
2. Bloquear novas features no modelo legado.
3. Migrar fluxo principal para o modelo novo.
4. Remover o legado após validação.

---

## 2.8 Não há validação suficiente da implementação

Não há evidência, no estado observado, de que foram executados:

- testes de migração em base real ou semi-real;
- testes de múltiplos itens para mesma diretiva;
- testes de ausência em snapshot;
- testes de exportação e detalhe sobre o modelo novo;
- testes de consistência entre legado e novo modelo.

Impacto:

- a refatoração pode parecer correta no ORM, mas falhar em execução;
- problemas de dados só aparecerão quando o banco real for migrado.

O que deve ser feito:

1. Criar testes automatizados de migration.
2. Criar massa de dados com:
   - mesma diretiva com múltiplos FADTs;
   - múltiplos itens iguais;
   - conflitos de dados mestre;
   - itens ausentes entre snapshots.
3. Validar importação, consulta, exportação e telas com o modelo novo.

---

## 3. O que deve ser feito agora

## 3.1 Prioridade 1: corrigir a migração de dados

Antes de migrar a aplicação inteira, é necessário tornar a migration confiável.

Ações:

1. Reescrever a ETL de `Diretiva -> DiretivaTecnica`.
2. Definir regra segura de consolidação dos campos mestre.
3. Deduplicar `DiretivaItem` antes do insert.
4. Mapear corretamente os vínculos para `DiretivaItemAeronave`.
5. Gerar logs ou relatórios de conflitos.

Resultado esperado:

- migration executável em base real sem colidir com constraints.

---

## 3.2 Prioridade 2: reescrever o `csv_service.py`

Esse é o ponto central da correção de negócio.

Ações:

1. Resolver `DiretivaTecnica` por código.
2. Construir `chave_item`.
3. Persistir `DiretivaItem`.
4. Persistir `DiretivaItemAeronave`.
5. Implementar snapshot por aeronave.
6. Marcar ausentes automaticamente.
7. Preencher campos de auditoria.

Resultado esperado:

- novas importações deixam de alimentar o modelo errado.

---

## 3.3 Prioridade 3: migrar o runtime da aplicação

Enquanto a aplicação usar o legado, a refatoração permanece incompleta.

Ações:

1. Refatorar dashboard.
2. Refatorar rota de detalhe.
3. Refatorar edição operacional.
4. Refatorar exportação XLSX.
5. Refatorar `/master-directives`.
6. Atualizar templates.

Resultado esperado:

- toda a aplicação passa a depender exclusivamente do novo modelo.

---

## 3.4 Prioridade 4: revisar o modelo final

Após migrar o fluxo funcional, revisar se a modelagem está suficientemente limpa.

Pontos de revisão:

- manter ou remover `Diretiva` e `DiretivaAeronave`;
- padronizar nomenclatura (`codigo` vs `codigo_diretiva`);
- adicionar tabela formal de snapshot, se necessário;
- revisar índices e constraints finais.

Resultado esperado:

- schema final coerente e sem ambiguidade.

---

## 3.5 Prioridade 5: validar e remover o legado

Ações:

1. Executar testes completos.
2. Validar banco migrado.
3. Confirmar que nenhuma rota usa mais o legado.
4. Remover tabelas e classes antigas.
5. Atualizar documentação final.

Resultado esperado:

- sistema estabilizado no novo modelo.

---

## 4. Sequência recomendada de execução

1. Corrigir migration de dados.
2. Reescrever importador CSV.
3. Migrar consultas e rotas.
4. Migrar templates e exportações.
5. Criar testes de regressão e de migração.
6. Validar banco legado convertido.
7. Remover modelo antigo.

---

## 5. Critério de aceite da refatoração

A refatoração só deve ser considerada concluída quando todas as condições abaixo forem verdadeiras:

1. `Diretiva Técnica` for a identidade principal do sistema.
2. `FADT` e `Tarefa` forem tratados apenas como itens subordinados.
3. O CSV importar dados diretamente para o novo modelo.
4. A lógica de snapshot estiver implementada.
5. Dashboard, exportação, detalhe e edição usarem o novo modelo.
6. O legado não for mais necessário em produção.
7. As migrations forem seguras para dados reais.
8. Os testes cobrirem múltiplos itens por diretiva e ausência em snapshot.

---

## 6. Conclusão

A refatoração v4 acertou a direção arquitetural, mas não fechou a implementação.

O novo schema foi introduzido, porém o sistema continua funcionando com a lógica antiga. Isso significa que a correção ainda não foi efetivamente entregue do ponto de vista operacional.

O trabalho correto agora não é recomeçar do zero, mas concluir a transição com disciplina:

- corrigir a migration de dados;
- reescrever o importador;
- migrar o runtime;
- validar;
- remover o legado.
