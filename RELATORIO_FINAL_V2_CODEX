# RELATORIO_FINAL_V2_CODEX

Data: 2026-04-01

Objetivo: definir um plano detalhado de correção para as inconsistências identificadas em `RELATORIO_FINAL_CHECK.MD`, com foco em implementação segura, rastreável e verificável.

Escopo deste plano:

- Corrigir pendências das Fases 1, 2 e 3.
- Priorizar integridade do banco, segurança operacional e confiabilidade de deploy.
- Definir critérios de aceite, testes, verificações e sequência de execução.

Princípio geral:

- Nenhuma correção estrutural deve ser considerada concluída apenas por “funcionar localmente”.
- Toda correção deve ser validada por:
  - consistência entre código, migrations e banco criado do zero
  - testes automatizados
  - verificação manual mínima dos fluxos críticos

---

## 1. RESUMO DAS INCONSISTÊNCIAS A CORRIGIR

### 1.1 Segurança e segredos

Pendências:

- Não há evidência de rotação efetiva de `SECRET_KEY`, `ADMIN_PASSWORD` e `GATEKEEPER_PASSWORD`.
- Não há evidência de expurgo histórico de segredos já versionados.
- A proteção de anexos está baseada em gatekeeper, mas o requisito do relatório fala em rota autenticada; é necessário definir formalmente o nível de autorização exigido.

### 1.2 Banco de dados e migrations

Pendência crítica:

- Os models atuais usam `DiretivaTecnica.codigo_simplificado` como chave primária string, mas a cadeia Alembic ainda descreve `diretiva_tecnica.id` inteiro.
- A migration de dados também foi escrita para o modelo antigo com PK/FK inteiras.
- Isso pode quebrar ambientes recriados do zero e invalida a alegação de reconciliação concluída.

### 1.3 Frontend e infraestrutura

Pendência:

- `base.html` ainda carrega Tailwind via CDN externa.
- Isso viola o objetivo de independência de rede/CDN em ambiente restrito.

### 1.4 Performance de CSV

Pendência:

- O CSV ainda é lido integralmente em memória.
- Já existe cache para reduzir N+1, mas ainda não existe processamento em chunks/lotes.

### 1.5 Testes

Pendências:

- Os testes não usam banco efêmero isolado por caso.
- Há dependência de estado compartilhado via `init_db()` e engine global.
- Não existe evidência suficiente de testes dedicados para:
  - reconciliação model/migration
  - snapshot e auto-conclusão
  - deduplicação real em múltiplas importações
  - controle de acesso exato em anexos

---

## 2. ORDEM DE EXECUÇÃO RECOMENDADA

Ordem obrigatória:

1. Corrigir estratégia de banco e migrations.
2. Corrigir isolamento de testes.
3. Corrigir segurança residual de segredos e política de anexos.
4. Internalizar frontend.
5. Implementar chunks no CSV.
6. Validar tudo em ambiente recriado do zero.

Justificativa:

- Sem resolver migrations primeiro, qualquer ambiente novo pode nascer incorreto.
- Sem testes isolados, o restante das mudanças pode parecer estável sem ser reproduzível.

---

## 3. PLANO DE CORREÇÃO DETALHADO

## 3.1 CORREÇÃO CRÍTICA: RECONCILIAÇÃO ENTRE MODELS E MIGRATIONS

Status atual:

- Models:
  - `DiretivaTecnica.codigo_simplificado` = PK string
  - `DiretivaItem.diretiva_tecnica_id` = FK string
- Migrations:
  - `diretiva_tecnica.id` = PK inteira
  - `diretiva_item.diretiva_tecnica_id` = FK inteira

Objetivo:

- Fazer a cadeia Alembic representar exatamente o schema que o código usa hoje.

Decisão arquitetural recomendada:

- Adotar definitivamente `codigo_simplificado` como PK canônica de `diretiva_tecnica`.
- Remover a ambiguidade histórica de `id` inteiro nesse agregado.

### Implementação proposta

#### Etapa 1: congelar o schema alvo

Produzir uma definição explícita do schema canônico atual:

- `aeronave`
- `snapshot`
- `diretiva_tecnica`
  - PK: `codigo_simplificado`
  - `codigo` unique
- `diretiva_item`
  - FK string para `diretiva_tecnica.codigo_simplificado`
- `diretiva_item_aeronave`
- `user`

Entregável:

- Documento curto em `doc/` ou comentário de arquitetura explicando o schema final suportado.

#### Etapa 2: escolher a estratégia de migration

Há duas opções válidas:

Opção A, recomendada se o projeto ainda está em fase controlada:

- Substituir a cadeia atual por uma baseline nova e limpa.
- Criar uma migration inicial única coerente com o schema atual.
- Criar migrations posteriores apenas para dados legados se ainda forem necessárias.

Quando usar:

- Quando o sistema ainda não depende de uma longa história de versões em produção.
- Quando é aceitável reinicializar o encadeamento Alembic.

Opção B, recomendada se é obrigatório preservar a cadeia histórica:

- Criar uma migration corretiva que:
  - adiciona `codigo_simplificado`
  - migra os dados
  - converte as FKs de `diretiva_item`
  - remove dependência operacional de `id`

Quando usar:

- Quando já existem bancos reais em campo que dependem da cadeia atual.

Recomendação prática:

- Se o ambiente ainda não está em produção formal, usar Opção A.

#### Etapa 3: baseline limpa do Alembic

Se usar Opção A:

- Remover ou arquivar as migrations incoerentes atuais.
- Gerar nova migration inicial coerente com os models reais.
- Validar que `alembic upgrade head` em banco vazio produz tabelas idênticas aos models.

Entregáveis técnicos:

- Nova migration inicial.
- Eventual migration de seed/dados legados separada.

#### Etapa 4: revisão de `init_db()`

Objetivo:

- Evitar que `create_all()` esconda defeitos de migration.

Ação:

- Manter `init_db()` apenas para uso explícito em teste.
- Renomear para algo inequívoco, por exemplo:
  - `init_test_db_schema()`
- Garantir que produção e app normal não chamem essa função.

#### Etapa 5: teste obrigatório de paridade model x migration

Criar teste que:

- sobe banco vazio temporário
- executa `alembic upgrade head`
- inspeciona schema resultante
- compara com os campos/chaves esperados pelos models

Casos mínimos:

- `diretiva_tecnica` tem PK em `codigo_simplificado`
- `diretiva_item.diretiva_tecnica_id` referencia `diretiva_tecnica.codigo_simplificado`
- `codigo` é unique
- constraints únicas existentes permanecem válidas

### Critério de aceite

- Banco criado só por Alembic funciona com a aplicação sem `create_all()`.
- Não existe divergência entre models e migrations nas tabelas principais.

---

## 3.2 SEGURANÇA DE SEGREDOS E HIGIENE DE REPOSITÓRIO

Objetivo:

- Encerrar a pendência de segredos de forma operacional, não só no código.

### Implementação proposta

#### Etapa 1: rotação real de segredos

Rotacionar:

- `SECRET_KEY`
- `ADMIN_PASSWORD`
- `GATEKEEPER_PASSWORD`

Requisitos:

- Novo conjunto de segredos gerado com entropia forte.
- Atualização dos ambientes de desenvolvimento, homologação e produção.
- Invalidar tokens/sessões antigas após troca do `SECRET_KEY`.

#### Etapa 2: revisão do histórico Git

Executar expurgo do histórico caso tenha havido versionamento de segredos reais.

Ferramentas possíveis:

- `git filter-repo`
- BFG Repo-Cleaner

Passos:

1. Confirmar quais arquivos/commits continham segredos.
2. Reescrever histórico.
3. Forçar push coordenado.
4. Comunicar equipe para reclone.

#### Etapa 3: padronizar `.env.example`

Criar ou revisar arquivo de exemplo com:

- nomes das variáveis obrigatórias
- descrição curta
- nenhuma credencial real

### Testes e verificações

- Aplicação não sobe sem `SECRET_KEY`.
- Aplicação não sobe sem `ADMIN_PASSWORD`.
- Aplicação não sobe sem `GATEKEEPER_PASSWORD`.
- Token assinado com chave antiga deixa de ser aceito após rotação.

### Critério de aceite

- Nenhum segredo real no histórico ativo ou HEAD.
- Startup falha de forma explícita quando faltar variável obrigatória.

---

## 3.3 FORMALIZAÇÃO DA POLÍTICA DE ACESSO A ANEXOS

Problema:

- Hoje a rota de anexos exige gatekeeper, mas o relatório fala em “rota autenticada”.
- É necessário escolher o comportamento correto.

Decisão a ser tomada:

Opção 1:

- Qualquer usuário que passou pelo gatekeeper pode visualizar anexos.

Opção 2, mais segura:

- Apenas usuário autenticado no sistema pode visualizar anexos.

Opção 3, mais restritiva:

- Apenas usuário autenticado com perfil compatível pode visualizar anexos.

Recomendação:

- Usar Opção 2 como mínimo.
- Se houver sensibilidade operacional dos PDFs, usar Opção 3.

### Implementação proposta

- Ajustar `get_upload()` para depender de autenticação real do sistema, não só gatekeeper.
- Se necessário, validar papel e/ou especialidade.
- Registrar tentativa negada com contexto mínimo.

### Testes obrigatórios

- Visitante sem gatekeeper: 403/redirect.
- Usuário com gatekeeper, mas sem login:
  - deve ser negado se a política escolhida for autenticação real.
- Usuário autenticado autorizado:
  - deve conseguir baixar.
- Usuário autenticado sem autorização:
  - deve receber 403.
- Arquivo inexistente:
  - deve retornar 404.

### Critério de aceite

- A política escolhida fica explícita no código e nos testes.

---

## 3.4 INTERNALIZAÇÃO TOTAL DO FRONTEND

Problema:

- Tailwind ainda depende de CDN.

Objetivo:

- Eliminar dependência de rede externa para renderização base.

### Implementação proposta

Opção recomendada:

- Compilar CSS local e servir via `app/static/`.

Estratégia:

1. Adicionar pipeline mínimo de build de CSS.
2. Gerar arquivo estático versionado, por exemplo:
   - `app/static/css/app.css`
3. Substituir script CDN por `<link rel="stylesheet">`.

Possíveis caminhos:

- Tailwind CLI local
- CSS pré-compilado committed no repositório

Recomendação pragmática:

- Se o projeto quer simplicidade operacional, commitar o CSS já compilado e documentar o comando de rebuild.

### Testes e verificações

- Abrir páginas principais sem internet e sem CDN.
- Confirmar que layout permanece funcional:
  - login
  - dashboard
  - detalhes de diretiva
  - administração

### Critério de aceite

- Nenhuma dependência crítica de UI é carregada de CDN externa.

---

## 3.5 PROCESSAMENTO DE CSV EM CHUNKS

Problema:

- `process_csv()` ainda usa leitura total em memória.

Objetivo:

- Permitir importação de CSV grande sem consumo explosivo de RAM.

### Implementação proposta

#### Estratégia recomendada

- Trocar a leitura única por `pd.read_csv(..., chunksize=N)`.

Estrutura desejada:

1. Normalizar cabeçalho uma vez.
2. Iterar por chunks.
3. Reusar caches em memória ao longo da importação.
4. Dar flush/commit por lote controlado.

#### Desenho técnico sugerido

Separar o serviço em camadas:

- `parse_csv_chunks(source)`
  - entrega DataFrames menores
- `process_csv_chunk(chunk, context)`
  - processa cada lote
- `finalize_snapshot_logic(context)`
  - trata auto-conclusão ao fim da importação

#### Ponto importante

O algoritmo atual de snapshot depende de saber:

- quais links foram processados
- quais matrículas apareceram no CSV inteiro

Portanto, o contexto da importação deve acumular:

- `matriculas_no_csv`
- `links_processados_ids`
- `content_hash`
- `aero_snapshots`
- caches de aeronave, diretiva, item e link

#### Tamanho de chunk sugerido

Começar com:

- 500 linhas
- ou 1000 linhas

Depois ajustar com benchmark.

#### Cuidados de implementação

- Não quebrar deduplicação entre chunks.
- Não recriar snapshot duplicado por chunk para a mesma aeronave.
- Não perder atualização de `numero_serie`.
- Não reprocessar item/link já visto no mesmo arquivo.

### Testes obrigatórios

- CSV pequeno continua funcionando.
- CSV grande processa em múltiplos chunks.
- Mesma DT em chunks diferentes continua deduplicada.
- Mesmo vínculo em chunks diferentes não gera duplicata.
- Snapshot final continua auto-concluindo ausentes corretamente.
- Importação de arquivo idêntico produz resultado consistente.

### Critério de aceite

- A importação passa a operar em lotes sem regressão funcional.

---

## 3.6 SUÍTE DE TESTES COM ISOLAMENTO REAL

Problema:

- Testes usam engine e banco compartilhados.

Objetivo:

- Tornar os testes determinísticos e independentes entre si.

### Implementação proposta

#### Etapa 1: criar fixtures centrais

Criar em `tests/conftest.py`:

- fixture de banco temporário por teste
- fixture de sessão isolada
- fixture de `TestClient` com overrides de dependência

Estratégia recomendada:

- SQLite temporário por teste ou por módulo
- `StaticPool` quando necessário
- override de `get_session`

#### Etapa 2: separar tipos de testes

Categorias:

- unitários
- integração de serviço
- integração HTTP
- performance/benchmark

#### Etapa 3: remover dependência de `init_db()` global

- Cada teste deve preparar seu próprio schema/contexto.
- `init_db()` não deve ser o mecanismo principal dos testes HTTP.

### Casos de teste que precisam existir

#### Banco e migrations

- banco vazio + Alembic head + app funcional
- constraints únicas mantidas
- PK/FK de diretivas coerentes com models

#### Segurança

- ausência de env obrigatória falha no startup
- CSRF bloqueia submissão sem token
- CSRF aceita submissão com token válido
- gatekeeper com senha errada
- gatekeeper com senha correta
- rota protegida sem autenticação

#### Anexos

- upload de PDF válido
- rejeição de arquivo não PDF
- rejeição de arquivo acima do limite
- download autorizado
- download negado para perfil inadequado
- remoção de anexo

#### CSV e snapshot

- importação simples
- deduplicação na mesma carga
- deduplicação em cargas repetidas
- atualização de campos mestre
- criação de snapshots
- auto-conclusão de itens ausentes
- manutenção correta de `origem_status`

#### Dashboard

- paginação
- filtros por busca
- filtros por status
- filtros por especialidade
- renderização com relacionamentos carregados

#### Performance

- benchmark de importação com volume controlado
- comparação antes/depois de chunking

### Critério de aceite

- Testes podem rodar em qualquer máquina limpa e produzir o mesmo resultado.

---

## 3.7 VALIDAR O AMBIENTE RECRIADO DO ZERO

Objetivo:

- Garantir que o sistema nasce corretamente sem depender de resíduos locais.

### Procedimento obrigatório

Executar do zero:

1. criar banco vazio
2. rodar `alembic upgrade head`
3. subir aplicação
4. acessar `/health`
5. validar bootstrap do admin
6. validar login/gatekeeper
7. importar CSV mínimo
8. acessar dashboard

### Verificações mínimas

- Nenhuma tabela crítica faltando
- Nenhuma coluna divergente
- Nenhuma FK inconsistente
- Nenhuma necessidade oculta de `create_all()`

### Critério de aceite

- Ambiente limpo sobe e opera usando apenas migrations + app.

---

## 4. MATRIZ DE PRIORIDADE

### Prioridade P0

- Reconciliação de models e migrations
- Testes de paridade schema/model
- Isolamento de banco nos testes

### Prioridade P1

- Política definitiva de autorização para anexos
- Rotação de segredos
- Expurgo histórico de segredos

### Prioridade P2

- Internalização completa do frontend
- Chunking no CSV

### Prioridade P3

- Ampliação de benchmarks
- Melhorias de observabilidade e documentação operacional

---

## 5. CHECKLIST DE IMPLEMENTAÇÃO

### Banco

- Definir schema canônico final
- Escolher estratégia Alembic A ou B
- Corrigir cadeia de migrations
- Validar banco criado do zero

### Segurança

- Rotacionar segredos
- Criar `.env.example`
- Revisar política de anexos
- Testar bloqueios/autorização

### Frontend

- Remover Tailwind CDN
- Servir CSS local
- Validar páginas sem internet

### CSV

- Refatorar para chunks
- Preservar caches globais da importação
- Garantir snapshot e deduplicação corretos

### Testes

- Criar `conftest.py`
- Isolar banco por teste
- Adicionar testes de migration/schema
- Adicionar testes de snapshot/deduplicação
- Adicionar testes de anexo/autorização

---

## 6. CRITÉRIOS FINAIS DE ACEITE DO PROJETO

O conjunto de correções só deve ser considerado concluído quando todos os itens abaixo forem verdadeiros:

- O banco criado por Alembic está alinhado com os models reais.
- A aplicação sobe sem depender de `create_all()` no fluxo normal.
- Não existem segredos reais expostos no HEAD ou em histórico não tratado.
- Os anexos obedecem a uma política de autorização explícita e testada.
- O frontend principal não depende de CDN externa para funcionar.
- O CSV processa grandes volumes em chunks, sem regressão funcional.
- Os testes usam banco isolado e são reproduzíveis.
- Os fluxos críticos estão cobertos:
  - gatekeeper
  - login
  - upload CSV
  - snapshot
  - deduplicação
  - upload/download PDF
  - dashboard e filtros

---

## 7. ENTREGA RECOMENDADA EM LOTES

Lote 1:

- Reconciliação de migrations
- teste de paridade schema/model
- ambiente limpo funcionando

Lote 2:

- isolamento de testes
- cobertura de snapshot/deduplicação/anexos

Lote 3:

- autorização final de anexos
- rotação e higiene de segredos

Lote 4:

- internalização do frontend
- chunking do CSV
- benchmark final

---

## 8. OBSERVAÇÃO FINAL

O ponto mais perigoso hoje não é visual nem funcional; é estrutural. O projeto já tem sinais de evolução correta, mas ainda possui risco real de divergência entre “o banco que existe localmente” e “o banco que nasce de forma oficial”. A correção deve começar por essa base, porque qualquer melhoria de segurança, performance ou interface perde confiabilidade se o schema oficial continuar inconsistente.
