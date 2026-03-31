# Relatório de Refatoração: Novo Modelo Relacional (v4.0.0)

Este documento detalha as mudanças estruturais e lógicas implementadas no banco de dados do SIGDT para adequá-lo às regras de negócio reais do domínio aeronáutico.

## 1. O Problema Anterior
No modelo legado (v3.5.0 e anteriores), a entidade `Diretiva` era identificada unicamente pelo campo `FADT`. Isso causava distorções, pois:
- Uma mesma **Diretiva Técnica** (ex: uma AD ou SB) poderia ter múltiplos FADTs ou tarefas.
- O sistema tratava cada FADT como uma diretiva independente, dificultando a visão consolidada.
- O vínculo com a aeronave era feito diretamente com o FADT, perdendo a hierarquia correta.

## 2. Nova Arquitetura de Dados
A refatoração introduziu uma hierarquia de três níveis, separando a identidade técnica da execução operacional.

### Nível 1: Diretiva Técnica (`diretiva_tecnica`)
Representa o documento mestre (AD, SB, etc.).
- **Chave Única:** `codigo` (ex: "AD 2024-01").
- **Atributos:** Objetivo, Classe (Gravidade), Categoria (Urgência), Especialidade.

### Nível 2: Item da Diretiva (`diretiva_item`)
Representa uma tarefa específica ou um FADT vinculado à diretiva mestre.
- **Chave Única:** Composta por `(diretiva_tecnica_id, chave_item)`.
- **Atributos:** FADT, Tarefa, Ordem de Referência.
- **Inovação:** Introdução da `chave_item`, uma string determinística que garante a deduplicação mesmo quando o FADT é ausente ou repetido.

### Nível 3: Estado por Aeronave (`diretiva_item_aeronave`)
Representa a pendência real em uma aeronave específica.
- **Chave Única:** `(aeronave_id, diretiva_item_id)`.
- **Atributos:** Status (Pendente, Ativo, Concluído), Cálculo GUT, Data de Aplicação, Observações e PDF vinculado.

## 3. Mudanças na Infraestrutura (Alembic)
- **Centralização da URL:** O arquivo `migrations/env.py` foi refatorado para priorizar a variável de ambiente `DATABASE_URL`, garantindo consistência entre o App e o sistema de migrações.
- **Suporte a SQLModel:** O template de migração (`script.py.mako`) foi ajustado para suportar automaticamente os tipos de dados do `SQLModel`.

## 4. Migração de Dados (ETL Interno)
Foi criada uma migração de dados automatizada (`1d3fc7e34187`) que realizou as seguintes etapas:
1. **Deduplicação de Mestres:** Agrupou todas as diretivas legadas pelo código e criou registros únicos em `diretiva_tecnica`.
2. **Preservação de Itens:** Cada registro antigo de FADT foi convertido em um `diretiva_item` vinculado ao seu mestre correto.
3. **Reconstrução de Vínculos:** Todos os status, notas, cálculos GUT e caminhos de PDF das aeronaves foram migrados para a nova tabela `diretiva_item_aeronave`.

## 5. Benefícios Alcançados
- **Escalabilidade:** O sistema agora suporta naturalmente diretivas que possuem múltiplas tarefas ou FADTs associados.
- **Integridade:** Uso de chaves compostas e `UniqueConstraints` para evitar duplicidade de pendências na mesma aeronave.
- **Rastreabilidade:** Adição de campos como `origem_status` e `concluida_automaticamente` para auditoria de importações via CSV (snapshot).
- **Normalização:** Aderência à 3ª Forma Normal (3NF), eliminando redundâncias de dados técnicos.

---
**Status:** Etapa de Schema e Migração de Dados concluída. 
**Próximos Passos:** Refatoração do `csv_service.py` e atualização dos Templates HTMX.
