# PLANO DE IMPLEMENTAÇÃO: REFATORAÇÃO DO MODELO DE BANCO

## 1. Objetivo da refatoração

Adequar o projeto à regra de negócio real:

- A `Diretiva Técnica` é o artefato mestre e único.
- `FADT` e `Tarefa` são artefatos derivados, internos e subordinados à diretiva.
- O sistema deve continuar controlando pendências por aeronave, mas sem tratar `FADT` como identidade principal da diretiva.
- A refatoração deve preservar histórico, evitar duplicidade e permitir evolução futura sem quebrar o fluxo atual.

Essa refatoração é justificável porque o modelo atual ancora a entidade `Diretiva` em `fadt`, o que distorce o domínio e força regras de unicidade inadequadas.

---

## 2. Diagnóstico do estado atual

## 2.1 Problema central

Hoje a tabela `Diretiva` mistura:

- identidade da diretiva técnica;
- atributos operacionais internos;
- identificadores subordinados como `FADT`;
- vínculo implícito com o que deveria ser um item executável.

No código atual:

- `Diretiva.fadt` é `UNIQUE`;
- o importador CSV usa `fadt` como chave de upsert;
- telas e exportações leem `fadt` diretamente da tabela mestre;
- a regra de snapshot não encerra itens ausentes;
- a estrutura atual não permite representar corretamente uma diretiva com múltiplos `FADT` e/ou múltiplas tarefas.

## 2.2 Consequências

- perda de aderência ao domínio;
- dificuldade para deduplicar corretamente;
- risco de sobrescrever dados mestre por dados de item;
- limitação para auditoria e rastreabilidade;
- acoplamento excessivo entre importação CSV e entidade principal.

---

## 3. Princípio de modelagem a adotar

## 3.1 Regra mestre

A identidade principal deve ser a `Diretiva Técnica`.

## 3.2 Regra subordinada

`FADT`, `Tarefa` e demais marcadores operacionais devem ser modelados como itens internos vinculados à diretiva, nunca como identidade da entidade mestre.

## 3.3 Regra operacional

O que fica pendente por aeronave não é a diretiva abstrata isoladamente, mas sim um item operacional aplicável daquela diretiva para aquela aeronave.

---

## 4. Modelo alvo

## 4.1 Entidades principais

### 4.1.1 `aeronave`

Mantém a estrutura atual com pequenos ajustes de consistência.

Campos:

- `id` PK
- `matricula` UNIQUE NOT NULL
- `numero_serie` UNIQUE NOT NULL
- timestamps opcionais de auditoria

### 4.1.2 `diretiva_tecnica`

Nova entidade mestre do domínio.

Responsabilidade:

- representar o documento técnico principal;
- armazenar atributos globais e estáveis da diretiva.

Campos sugeridos:

- `id` PK
- `codigo` UNIQUE NOT NULL
- `objetivo` NULL
- `classe` NULL
- `categoria` NULL
- `tipo` NULL
- `natureza` NULL
- `especialidade` NULL
- `ativa` BOOLEAN NOT NULL DEFAULT TRUE
- `created_at`
- `updated_at`

Observações:

- `codigo` substitui `codigo_diretiva` como nome preferencial de domínio.
- Se for desejável menor impacto inicial, pode-se manter `codigo_diretiva` no ORM e migrar nomenclatura depois.

### 4.1.3 `diretiva_item`

Nova entidade subordinada à diretiva técnica.

Responsabilidade:

- representar um item operacional interno da diretiva;
- conter `FADT`, `Tarefa`, `Ordem` e outros marcadores específicos do item.

Campos sugeridos:

- `id` PK
- `diretiva_tecnica_id` FK NOT NULL
- `fadt` NULL
- `tarefa` NULL
- `ordem_referencia` NULL
- `codigo_item_externo` NULL
- `descricao_item` NULL
- `ativo` BOOLEAN NOT NULL DEFAULT TRUE
- `created_at`
- `updated_at`

Observações:

- `FADT` não deve mais ser `UNIQUE` global.
- O item pode existir sem `fadt`, desde que a chave de negócio seja atendida por outros campos.
- O nome final da tabela pode ser `diretiva_item` ou `item_diretiva`; manter consistência em todo o projeto.

### 4.1.4 `diretiva_item_aeronave`

Nova entidade de estado operacional por aeronave.

Responsabilidade:

- representar a pendência ou execução de um item operacional em uma aeronave;
- armazenar status, observações, anexos e cálculo GUT.

Campos sugeridos:

- `id` PK
- `aeronave_id` FK NOT NULL
- `diretiva_item_id` FK NOT NULL
- `status` NOT NULL
- `data_aplicacao` NULL
- `data_status` NOT NULL
- `ordem_aplicada` NULL
- `observacao` NULL
- `pdf_path` NULL
- `tendencia` NOT NULL DEFAULT 3
- `gut` NOT NULL DEFAULT 0
- `origem_status` NOT NULL DEFAULT 'csv'
- `ultima_referencia_snapshot` NULL
- `concluida_automaticamente` BOOLEAN NOT NULL DEFAULT FALSE
- `created_at`
- `updated_at`

Constraint principal:

- `UNIQUE (aeronave_id, diretiva_item_id)`

---

## 5. Regras de unicidade

## 5.1 Diretiva técnica

Deve ser única por `codigo`.

Constraint:

- `UNIQUE(diretiva_tecnica.codigo)`

## 5.2 Item da diretiva

A unicidade do item deve ser definida por chave composta subordinada à diretiva, nunca global por `fadt`.

Sugestão inicial:

- `UNIQUE(diretiva_tecnica_id, fadt, tarefa, ordem_referencia)`

Como `NULL` em constraints compostas pode variar por banco, a implementação precisa normalizar antes de persistir:

- converter strings vazias para `NULL`;
- opcionalmente usar colunas normalizadas auxiliares;
- ou criar uma chave técnica derivada `chave_item`.

## 5.3 Vínculo operacional

Um item operacional não pode existir duplicado para a mesma aeronave.

Constraint:

- `UNIQUE(aeronave_id, diretiva_item_id)`

---

## 6. Chave de negócio recomendada para o item

Como `FADT` não é essencial, a chave do item não deve depender exclusivamente dele.

Recomendação:

1. Criar uma chave técnica de deduplicação chamada `chave_item`.
2. Montar essa chave a partir dos campos operacionais disponíveis no CSV.
3. Sempre vincular a `chave_item` à diretiva técnica mestre.

Fórmula sugerida:

- `chave_item = normalizar(codigo_diretiva, fadt, tarefa, ordem_referencia)`

Regras:

- remover espaços excedentes;
- upper-case;
- converter vazio para marcador estável;
- manter a chave determinística;
- armazenar `chave_item` no banco com `UNIQUE(diretiva_tecnica_id, chave_item)`.

Isso reduz risco de ambiguidade quando `fadt` vier ausente, repetido ou inconsistente.

---

## 7. Estratégia de migração de dados

## 7.1 Premissa

Não fazer substituição abrupta do modelo atual em uma única etapa lógica no código.

## 7.2 Fase 1: preparar schema

Criar novas tabelas sem remover imediatamente as antigas:

- `diretiva_tecnica`
- `diretiva_item`
- `diretiva_item_aeronave`

Objetivo:

- permitir migração assistida;
- evitar quebra imediata de telas e rotas;
- permitir validação incremental.

## 7.3 Fase 2: migrar dados atuais

Para cada registro da tabela `diretiva` atual:

1. Criar ou localizar `diretiva_tecnica` por `codigo_diretiva`.
2. Criar `diretiva_item` com `fadt`, `ordem` e eventual `tarefa` se existir legado.
3. Mapear o vínculo antigo `DiretivaAeronave` para `diretiva_item_aeronave`.
4. Preservar `status`, `observacao`, `pdf_path`, `gut`, `tendencia`, datas e anexos.

## 7.4 Fase 3: compatibilidade temporária

Atualizar o ORM e o serviço de importação para ler e gravar apenas no modelo novo.

Durante essa fase:

- a tabela antiga pode permanecer apenas para conferência;
- as rotas não devem mais depender de `Diretiva.fadt`;
- consultas de listagem devem passar a usar joins com o item.

## 7.5 Fase 4: remoção do legado

Somente após validação:

- remover tabela antiga `diretiva` ou congelá-la;
- remover código que use `fadt` como chave primária de negócio;
- limpar migrations transitórias.

---

## 8. Ajustes de ORM e código

## 8.1 `app/models.py`

Substituir o modelo atual por um modelo com quatro entidades claras:

- `Aeronave`
- `DiretivaTecnica`
- `DiretivaItem`
- `DiretivaItemAeronave`

Relacionamentos esperados:

- `DiretivaTecnica` 1:N `DiretivaItem`
- `DiretivaItem` 1:N `DiretivaItemAeronave`
- `Aeronave` 1:N `DiretivaItemAeronave`

## 8.2 `calculate_gut`

Mover o cálculo para o vínculo operacional:

- `DiretivaItemAeronave.calculate_gut()`

Fonte de dados:

- `classe` e `categoria` da `DiretivaTecnica`;
- `tendencia` do vínculo operacional.

## 8.3 `app/database.py`

Ajustes necessários:

- importar os novos modelos;
- remover dependência de `create_all` como mecanismo principal de evolução de schema;
- manter `init_db()` apenas para cenários de teste controlados, se necessário.

Recomendação:

- produção e desenvolvimento devem usar `alembic upgrade head`;
- `create_all` deve deixar de ser fonte primária de schema.

---

## 9. Estratégia de importação CSV

## 9.1 Objetivo

O CSV deve alimentar o estado operacional atual sem redefinir a identidade da diretiva técnica.

## 9.2 Novo fluxo

Para cada linha do CSV:

1. Normalizar colunas.
2. Resolver ou criar `Aeronave`.
3. Resolver ou criar `DiretivaTecnica` por `codigo_diretiva`.
4. Resolver ou criar `DiretivaItem` por `diretiva_tecnica_id + chave_item`.
5. Resolver ou criar `DiretivaItemAeronave` por `aeronave_id + diretiva_item_id`.
6. Atualizar status operacional.
7. Recalcular GUT.
8. Marcar o item como presente no snapshot corrente.

## 9.3 Regras de atualização

### Dados mestre da diretiva técnica

Atualizar apenas campos globais:

- `objetivo`
- `classe`
- `categoria`
- `tipo`
- `natureza`
- `especialidade`

### Dados do item

Atualizar apenas campos subordinados:

- `fadt`
- `tarefa`
- `ordem_referencia`

### Dados operacionais por aeronave

Atualizar:

- `status`
- `ordem_aplicada`
- `observacao`
- `data_status`

## 9.4 Snapshot

Implementar controle explícito de lote de importação.

Recomendação:

- criar uma tabela `importacao_snapshot` ou ao menos um identificador de execução;
- registrar `snapshot_id`, data, arquivo e contagem processada;
- associar `ultima_referencia_snapshot` em `diretiva_item_aeronave`.

Fluxo:

1. Iniciar snapshot.
2. Processar todas as linhas e marcar vínculos encontrados.
3. Ao final, localizar vínculos ativos da mesma aeronave que não apareceram no snapshot.
4. Marcar esses vínculos como concluídos automaticamente.

Status sugerido:

- `Concluída`

Campos auxiliares:

- `concluida_automaticamente = true`
- `origem_status = 'snapshot_absente'`

## 9.5 Escopo do snapshot

Definir explicitamente:

- se cada CSV representa uma aeronave única;
- se o upload múltiplo representa um lote de snapshots por aeronave;
- se a ausência só pode ser avaliada dentro do escopo da aeronave do arquivo.

Recomendação para este projeto:

- tratar cada arquivo como snapshot de uma única aeronave;
- encerrar ausentes somente daquela aeronave.

---

## 10. Rotas e telas afetadas

## 10.1 Dashboard `/`

Hoje lista vínculos por `DiretivaAeronave`.

Passará a listar `DiretivaItemAeronave`, exibindo:

- matrícula;
- número de série;
- código da diretiva técnica;
- `FADT` do item, quando houver;
- status;
- GUT.

## 10.2 Detalhe `/directives/{id}`

Deve exibir separação visual entre:

- dados da diretiva técnica;
- dados do item interno;
- dados operacionais da aeronave.

## 10.3 Master directives `/master-directives`

Essa tela deve passar a editar apenas a diretiva técnica mestre.

Não deve mais tratar `fadt` como identificador central.

## 10.4 Exportação XLSX

Deve continuar exportando `FADT`, mas como dado do item, não da entidade mestre.

Colunas sugeridas:

- `DIRETIVA_TECNICA`
- `FADT`
- `TAREFA`
- `STATUS`
- `MATRICULA`
- `NUMERO_SERIE`
- `GUT`

---

## 11. Migrações Alembic

## 11.1 Ordem recomendada

### Migration 1

Corrigir infraestrutura de migrations:

- `migrations/env.py` deve ler `DATABASE_URL`;
- parar de depender do valor fixo de `alembic.ini`.

### Migration 2

Criar novas tabelas:

- `diretiva_tecnica`
- `diretiva_item`
- `diretiva_item_aeronave`
- opcionalmente `importacao_snapshot`

### Migration 3

Migrar dados da tabela `diretiva` antiga para o novo modelo.

### Migration 4

Migrar dados da tabela `diretivaaeronave` antiga para `diretiva_item_aeronave`.

### Migration 5

Adicionar constraints finais, índices e validações após saneamento dos dados.

### Migration 6

Remover ou desativar estruturas legadas.

## 11.2 Cuidados

- tratar duplicidades antes de impor constraints finais;
- gerar relatório de colisões de `codigo_diretiva`;
- gerar relatório de colisões de `fadt` por diretiva;
- não apagar dados automaticamente em migrations sem log de auditoria.

---

## 12. Índices recomendados

### `diretiva_tecnica`

- índice único em `codigo`
- índice em `especialidade`

### `diretiva_item`

- índice em `diretiva_tecnica_id`
- índice em `fadt`
- índice único em `(diretiva_tecnica_id, chave_item)`

### `diretiva_item_aeronave`

- índice único em `(aeronave_id, diretiva_item_id)`
- índice em `status`
- índice em `data_status`
- índice em `ultima_referencia_snapshot`

### `aeronave`

- índice único em `matricula`
- índice único em `numero_serie`

---

## 13. Compatibilidade com regras atuais

## 13.1 O que permanece

- cálculo GUT por vínculo operacional;
- status por aeronave;
- upload e associação de PDF ao item operacional;
- filtro por especialidade;
- exportação para XLSX;
- autenticação e permissões.

## 13.2 O que muda

- `fadt` deixa de ser identidade da diretiva;
- listagens precisam fazer join com item;
- importador deixa de usar `fadt` como chave mestre;
- edição master passa a atingir apenas `DiretivaTecnica`.

---

## 14. Plano de execução em etapas

## Etapa 1. Saneamento e alinhamento técnico

Objetivo:

- preparar o terreno sem mudar regra de negócio visível.

Tarefas:

1. Corrigir `migrations/env.py` para usar `DATABASE_URL`.
2. Revisar `alembic.ini` para reduzir risco de drift.
3. Definir se `init_db()` continuará existindo apenas para testes.
4. Congelar o modelo atual para referência de migração.

Critério de saída:

- migrations executam no mesmo banco usado pelo app.

## Etapa 2. Introdução do novo schema

Objetivo:

- criar o modelo correto sem quebrar o sistema atual imediatamente.

Tarefas:

1. Criar classes ORM novas.
2. Gerar migration de criação das novas tabelas.
3. Adicionar constraints mínimas e índices iniciais.

Critério de saída:

- banco contém schema novo funcional.

## Etapa 3. Migração de dados legados

Objetivo:

- transportar dados atuais para o novo modelo.

Tarefas:

1. Mapear diretivas antigas para `diretiva_tecnica`.
2. Criar `diretiva_item` a partir de `fadt` e campos operacionais legados.
3. Migrar vínculos aeronave-diretiva para `diretiva_item_aeronave`.
4. Preservar PDFs, observações, status e datas.
5. Produzir relatório de colisões.

Critério de saída:

- todos os dados relevantes existem nas novas tabelas.

## Etapa 4. Refatoração do serviço de importação

Objetivo:

- alinhar o CSV ao novo domínio.

Tarefas:

1. Reescrever `process_csv`.
2. Introduzir `chave_item`.
3. Implementar snapshot por aeronave.
4. Marcar ausentes como concluídos automaticamente.
5. Proteger contra sobrescrita indevida de dados mestre.

Critério de saída:

- importação atualiza diretiva, item e vínculo operacional corretamente.

## Etapa 5. Refatoração das consultas e telas

Objetivo:

- migrar a aplicação para o novo modelo lógico.

Tarefas:

1. Atualizar dashboard.
2. Atualizar detalhe da diretiva.
3. Atualizar exportação.
4. Atualizar tela de diretivas mestre.
5. Ajustar filtros por busca e especialidade.

Critério de saída:

- interface opera integralmente sobre o modelo novo.

## Etapa 6. Testes e validação

Objetivo:

- garantir integridade funcional e de dados.

Tarefas:

1. Atualizar testes que assumem `Diretiva.fadt`.
2. Criar testes de múltiplos itens para uma mesma diretiva.
3. Criar testes de snapshot com ausência.
4. Criar testes de deduplicação.
5. Criar testes de exportação e filtros.

Critério de saída:

- suíte de testes cobre o novo domínio.

## Etapa 7. Desativação do legado

Objetivo:

- remover o modelo errado com segurança.

Tarefas:

1. Remover rotas, queries e joins legados.
2. Remover tabelas antigas após validação.
3. Limpar código morto e migrations transitórias.

Critério de saída:

- projeto sem dependência do modelo antigo.

---

## 15. Casos de borda que precisam ser tratados

1. Mesma diretiva técnica com múltiplos `FADT`.
2. Mesmo `FADT` reutilizado em itens distintos da mesma diretiva.
3. Linha de CSV sem `FADT`, mas com `código da diretiva`.
4. Diretiva com item já concluído manualmente que some do snapshot.
5. Mudança de número de série para mesma matrícula.
6. Colunas inconsistentes entre arquivos CSV.
7. Upload repetido do mesmo arquivo.
8. Dados de item que variam entre snapshots por erro da origem.

Recomendação:

- logar colisões e inconsistências em vez de corrigi-las silenciosamente.

---

## 16. Riscos

## 16.1 Risco de colisão de chave de item

Se os campos operacionais vierem incompletos no CSV, a deduplicação pode unir itens distintos.

Mitigação:

- adotar `chave_item` explícita;
- gerar relatório de ambiguidade;
- permitir ajuste manual posterior.

## 16.2 Risco de quebra de tela

As telas atuais acessam `fadt` direto da entidade mestre.

Mitigação:

- refatorar templates junto com a troca do ORM;
- manter camada de compatibilidade temporária se necessário.

## 16.3 Risco de drift entre app e migration

Hoje o app e o Alembic não estão perfeitamente alinhados.

Mitigação:

- corrigir infraestrutura de migration antes da mudança funcional.

## 16.4 Risco de marcar ausências incorretamente

Sem escopo claro de snapshot, o sistema pode concluir itens errados.

Mitigação:

- processar ausência apenas por aeronave do arquivo;
- registrar `snapshot_id`;
- evitar conclusão em lote sem contexto.

---

## 17. Entregáveis esperados da implementação

1. Novo modelo ORM completo.
2. Migrations Alembic para criação, migração de dados e limpeza do legado.
3. Novo importador CSV com snapshot por aeronave.
4. Rotas e templates adaptados.
5. Testes automatizados cobrindo múltiplos itens por diretiva.
6. Documento final de operação e rollback.

---

## 18. Ordem prática recomendada para execução neste repositório

1. Corrigir infraestrutura Alembic e alinhamento com `DATABASE_URL`.
2. Introduzir novo schema sem remover o antigo.
3. Migrar dados existentes.
4. Refatorar `process_csv`.
5. Refatorar consultas e templates.
6. Atualizar testes.
7. Validar em banco limpo e banco legado.
8. Remover legado.

---

## 19. Decisão final de arquitetura

A refatoração deve seguir esta hierarquia:

- `Diretiva Técnica` como entidade mestre de negócio;
- `Item da Diretiva` como representação operacional subordinada;
- `Item da Diretiva por Aeronave` como estado executável e auditável.

Essa abordagem preserva a centralidade da diretiva técnica, mantém controle sobre `FADT` e tarefa sem elevá-los indevidamente a identidade principal, e corrige a distorção atual do modelo.
