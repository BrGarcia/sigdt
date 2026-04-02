# RELATORIO TECNICO DE REVISAO - SIGDT

## Diagnostico geral

O repositorio tem uma base funcional e uma intencao correta de separar autenticacao, servicos, modelos e migracoes, mas o estado atual ainda nao esta pronto para producao. Os principais problemas estao concentrados em quatro areas: seguranca de sessao/formularios, consistencia de schema e migracoes, bootstrap operacional do banco, e confiabilidade dos testes/documentacao.

Os riscos mais relevantes observados foram:

- alteracoes autenticadas sem protecao CSRF;
- fallback inseguro para `SECRET_KEY`;
- schema atual divergente da cadeia de migracoes;
- uso simultaneo de Alembic e `create_all()` no startup;
- credenciais reais expostas na documentacao de deploy;
- testes fracos e nao executaveis neste ambiente.

## Problemas por prioridade

### Critica

#### 1. Ausencia de protecao CSRF em rotas state-changing autenticadas por cookie

- O que esta errado:
  As rotas `POST` e `DELETE` dependem de cookies HttpOnly e aceitam alteracoes sensiveis sem qualquer token CSRF ou middleware de verificacao. Isso afeta, no minimo, `/users/`, `/users/{id}`, `/directives/{id}`, `/directives/{id}/attachment`, `/upload`, `/update-tendencia/{id}` e `/master-directives/{codigo}`.
- Evidencias:
  `app/users/routes.py:74-101`, `app/users/routes.py:108-149`, `app/main.py:209-233`, `app/main.py:306-427`, `app/main.py:429-609`.
  Nao existe implementacao de CSRF no codigo da app.
- Risco:
  Um usuario autenticado pode ser induzido por um site externo a criar usuarios, excluir usuarios, alterar diretivas, remover anexos ou subir arquivos sem perceber.
- Impacto:
  Compromete integridade operacional e administrativa do sistema.
- Correcao recomendada:
  Implementar CSRF real para requests baseados em cookie. Opcoes pragmaticas:
  1. token CSRF por formulario/HTMX com validacao no backend;
  2. middleware dedicado;
  3. separar autenticacao browser e API com estrategia coerente.
- Ordem sugerida:
  1

#### 2. `SECRET_KEY` com fallback inseguro

- O que esta errado:
  O gatekeeper usa `SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key_change_in_production")`.
- Evidencias:
  `app/main.py:109-119`.
  Em contraste, o modulo de usuarios falha corretamente se a chave nao existir em `app/users/security.py`.
- Risco:
  Em ambiente mal configurado, tokens do gatekeeper podem ser forjados facilmente.
- Impacto:
  Bypass da primeira camada de acesso.
- Correcao recomendada:
  Remover o fallback e falhar no startup quando `SECRET_KEY` nao estiver definido, centralizando configuracao em um modulo unico de settings.
- Ordem sugerida:
  2

#### 3. Credenciais reais expostas na documentacao de deploy

- O que esta errado:
  O guia de deploy publica valores concretos para `ADMIN_PASSWORD` e `GATEKEEPER_PASSWORD`.
- Evidencias:
  `doc/09_DEPLOY_RAILWAY.md:11-17`.
- Risco:
  Se esses valores tiverem sido reutilizados em qualquer ambiente, ha comprometimento imediato.
- Impacto:
  Acesso administrativo indevido.
- Correcao recomendada:
  Revogar as credenciais atuais, gerar novos segredos, remover os valores do repositorio e substituir por placeholders e orientacao de geracao segura.
- Ordem sugerida:
  3

#### 4. Migracoes inconsistentes com os modelos atuais

- O que esta errado:
  O modelo atual usa `DiretivaTecnica.codigo_simplificado` como PK string e `DiretivaItem.diretiva_tecnica_id` como FK string, mas a migracao principal cria `diretiva_tecnica.id` inteiro e FK inteira em `diretiva_item`.
- Evidencias:
  Modelo atual em `app/models.py:35-67`.
  Migracao divergente em `migrations/versions/e6ca8f306a0d_feat_add_new_relational_model_for_.py:25-67`.
  Migracao de dados ainda depende de `last_insert_rowid()` e IDs inteiros em `migrations/versions/1d3fc7e34187_data_migrate_legacy_data_to_new_model.py:50-66`, `:78-104`.
- Risco:
  Banco criado por migracao nao corresponde ao banco criado por metadata; deploy limpo pode quebrar, e restauracoes/rebuilds ficam nao deterministicas.
- Impacto:
  Alto risco de falha de deploy, corrupcao de dados ou impossibilidade de evolucao segura do schema.
- Correcao recomendada:
  Regerar a cadeia de migracoes para refletir exatamente o schema atual, revisar a migracao de dados para ser agnostica ao banco e validar upgrade em base vazia e base legada.
- Ordem sugerida:
  4

### Alta

#### 5. Uso de `SQLModel.metadata.create_all()` no startup junto com Alembic

- O que esta errado:
  O sistema cria schema automaticamente no startup, ao mesmo tempo em que mantem pasta de migracoes Alembic.
- Evidencias:
  `app/database.py:17-18`, chamado por `app/main.py:121-125`.
- Risco:
  Mascara problemas de migracao, gera schema parcial fora do fluxo versionado e impede confianca no estado real do banco.
- Impacto:
  Operacao e deploy ficam imprevisiveis.
- Correcao recomendada:
  Remover `create_all()` do caminho de execucao normal e aplicar somente Alembic no startup/deploy.
- Ordem sugerida:
  5

#### 6. Rotina de startup reseta a senha do admin a cada inicializacao

- O que esta errado:
  Se o usuario `admin` ja existe, a senha hash e o papel sao reescritos em todo startup.
- Evidencias:
  `app/main.py:125-139`.
- Risco:
  Perda de rastreabilidade, surpresa operacional, impossibilidade de gestao normal de credenciais e acoplamento do ambiente a uma conta fixa.
- Impacto:
  Fragilidade operacional e de seguranca.
- Correcao recomendada:
  Fazer bootstrap idempotente apenas na primeira execucao, ou criar comando administrativo explicito para rotacao/reset de senha.
- Ordem sugerida:
  6

#### 7. Uploads servidos diretamente de `static`

- O que esta errado:
  PDFs enviados por usuarios sao gravados em `app/static/uploads` e expostos por URL publica previsivel.
- Evidencias:
  Escrita em `app/main.py:347-357`; exibicao via iframe em `app/templates/directive_details.html`.
- Risco:
  Exposicao nao controlada de documentos, enumeracao simples de arquivos e ausencia de camada de autorizacao no download.
- Impacto:
  Vazamento de anexos e dados tecnicos.
- Correcao recomendada:
  Mover anexos para storage fora de `static`, armazenar metadados no banco e servir download por rota autenticada/autorizada.
- Ordem sugerida:
  7

#### 8. Rate limit em memoria nao escalavel e facilmente contornavel

- O que esta errado:
  O limitador usa `defaultdict(list)` em memoria por processo.
- Evidencias:
  `app/main.py:95-107`, uso em `app/main.py:152-171` e `app/users/routes.py:74-80`.
- Risco:
  Em multiplos workers/instancias, o controle deixa de funcionar; reinicio limpa o historico.
- Impacto:
  Protecao fraca contra brute force.
- Correcao recomendada:
  Mover para Redis ou outra store compartilhada; registrar tentativas por IP e por identificador sensivel.
- Ordem sugerida:
  8

#### 9. Documentacao de seguranca afirma correcoes que nao existem ou nao foram verificadas

- O que esta errado:
  O documento diz que ha protecao anti-CSRF global e batch processing do CSV, mas o codigo nao confirma isso.
- Evidencias:
  Afirmações em `doc/07_RELATORIO.MD:29`, `doc/08_NEXT.md:28`, `doc/10_REVISAO_SEGURANCA.txt:27-30`.
  O importador le o CSV inteiro em memoria em `app/services/csv_service.py:29-31`.
- Risco:
  A equipe pode tomar decisoes baseada em premissas falsas.
- Impacto:
  Falhas de seguranca e capacidade passam despercebidas.
- Correcao recomendada:
  Revisar a documentacao para refletir somente o que esta implementado e comprovado.
- Ordem sugerida:
  9

### Media

#### 10. Importacao CSV com alto custo de memoria e I/O

- O que esta errado:
  O upload carrega todo arquivo em memoria; depois o servico carrega tudo novamente em DataFrame e ainda monta caches completos de aeronaves e diretivas.
- Evidencias:
  `app/main.py:215-232`, `app/services/csv_service.py:29-34`, `:47-50`.
- Risco:
  Consumo elevado de RAM e degradacao com crescimento de volume.
- Impacto:
  Gargalo de performance e risco de indisponibilidade por arquivos maiores.
- Correcao recomendada:
  Processamento em stream/chunks, prevalidacao incremental e estrategia de upsert em lote.
- Ordem sugerida:
  10

#### 11. Integridade relacional incompleta para exclusoes e governanca do dado

- O que esta errado:
  Os modelos usam FKs, mas nao definem comportamento de `ondelete`, nem estrategia de soft delete, nem restricoes mais fortes para `status`/`origem_status`.
- Evidencias:
  `app/models.py:24-33`, `:55-103`.
- Risco:
  Exclusoes futuras podem gerar lixo logico ou falhar de forma inconsistente; campos textuais aceitam valores arbitrarios no banco.
- Impacto:
  Menor confianca no dado e manutencao mais cara.
- Correcao recomendada:
  Definir politica de delete/cascade/restrict, enums no schema quando adequado, constraints e indices adicionais para consultas frequentes.
- Ordem sugerida:
  11

#### 12. Controle de permissao muito acoplado e espalhado

- O que esta errado:
  A regra de especialidade fica hardcoded em `main.py`, misturando regra de negocio com camada web.
- Evidencias:
  `app/main.py:60-86`.
- Risco:
  Regras ficam dificeis de evoluir, testar e reaproveitar.
- Impacto:
  Aumento de acoplamento e risco de regressao.
- Correcao recomendada:
  Extrair politica de autorizacao para modulo de dominio/servico com testes dedicados.
- Ordem sugerida:
  12

#### 13. Testes exercem pouco comportamento critico

- O que esta errado:
  Existem poucos testes cobrindo cenarios negativos e varios asserts sao permissivos demais. Exemplo: um teste aceita `200`, `401` ou `403`, o que praticamente nao valida comportamento.
- Evidencias:
  `tests/test_new_features.py:35-37`.
  Os testes dependem do banco real local e de estado compartilhado.
- Risco:
  Regressao passa sem deteccao.
- Impacto:
  Baixa confiabilidade para refatoracao.
- Correcao recomendada:
  Criar fixtures isoladas, banco efemero de teste, testes de autorizacao/CSRF/upload/migracao e asserts deterministas.
- Ordem sugerida:
  13

#### 14. Testes nao sao facilmente executaveis no ambiente atual

- O que esta errado:
  Nao ha virtualenv local no repositorio e `pytest` nao esta disponivel no PATH deste ambiente.
- Evidencias:
  Falha de execucao ao rodar `pytest -q`; tambem nao existem `.venv/` ou `env/` na raiz.
- Risco:
  A validacao automatizada nao e reproduzivel por padrao.
- Impacto:
  Menor previsibilidade para CI/CD e manutencao.
- Correcao recomendada:
  Documentar setup minimo, adicionar Makefile/script de bootstrap ou container de testes, e configurar CI.
- Ordem sugerida:
  14

#### 15. Dependencias frontend carregadas por CDN em runtime

- O que esta errado:
  HTMX e Tailwind sao carregados de CDNs diretamente nos templates.
- Evidencias:
  `app/templates/index.html`, `app/templates/directive_details.html`, `app/templates/user_management.html`, `app/templates/login.html`, `app/templates/master_directives.html`, `app/templates/master_directive_edit.html`, `app/templates/gatekeeper.html`.
- Risco:
  Dependencia externa em runtime, risco de indisponibilidade e cadeia de suprimentos mais fraca.
- Impacto:
  Menor confiabilidade e previsibilidade do front.
- Correcao recomendada:
  Empacotar assets estaticos versionados localmente ou via pipeline de frontend.
- Ordem sugerida:
  15

### Baixa

#### 16. Dockerfile e compose estao funcionais, mas pouco endurecidos para producao

- O que esta errado:
  A imagem roda como root, sem multi-stage, sem healthcheck, sem pinagem por digest e com `--forwarded-allow-ips='*'`. O compose de desenvolvimento expoe Postgres e embute credencial fixa no `DATABASE_URL`.
- Evidencias:
  `Dockerfile:1-23`, `docker-compose.yml:4-27`.
- Risco:
  Superficie de ataque maior e menor portabilidade entre ambientes.
- Impacto:
  Hardening insuficiente.
- Correcao recomendada:
  Usuario nao-root, imagem menor/endurecida, healthcheck, separacao clara entre compose dev e prod, e remocao de credenciais fixas do arquivo.
- Ordem sugerida:
  16

#### 17. Logging e observabilidade ainda rudimentares

- O que esta errado:
  Nao ha estrategia clara de logs estruturados, correlacao, auditoria ou metricas.
- Evidencias:
  Ausencia de configuracao dedicada; `engine` ainda usa `echo=True` em SQLite em `app/database.py:11`.
- Risco:
  Diagnostico operacional mais dificil e possivel vazamento de SQL em ambiente errado.
- Impacto:
  Operacao e troubleshooting piores.
- Correcao recomendada:
  Padronizar logging estruturado, niveis por ambiente e trilha minima de auditoria para alteracoes administrativas.
- Ordem sugerida:
  17

## Correcao urgente x melhoria evolutiva

### Urgente

- Implementar CSRF real para todas as rotas com cookie.
- Remover fallback de `SECRET_KEY`.
- Revogar e substituir credenciais divulgadas na documentacao.
- Corrigir a cadeia de migracoes e abandonar `create_all()` no startup.
- Parar de resetar a senha do admin a cada boot.
- Mover anexos para download autenticado fora de `static`.

### Evolutiva

- Refatorar autorizacao/especialidades para modulo proprio.
- Reestruturar importacao CSV para processamento incremental.
- Fortalecer schema com constraints e politica de exclusao.
- Trocar rate limit em memoria por store compartilhada.
- Empacotar assets frontend localmente.
- Implantar CI com testes isolados e checks de migracao.

## Plano de acao em fases

### Fase 1: estabilizacao e seguranca

1. Implementar CSRF.
2. Centralizar configuracao em settings tipados e remover fallbacks inseguros.
3. Rotacionar todos os segredos e limpar a documentacao.
4. Mover anexos para rota autenticada.
5. Corrigir bootstrap do admin.
6. Revisar e corrigir a documentacao de seguranca.

### Fase 2: refatoracao estrutural

1. Reconciliar modelos e migracoes.
2. Remover `create_all()` e validar apenas com Alembic.
3. Extrair regras de permissao/autorizacao do `main.py`.
4. Revisar schema, constraints, indices e estrategia de delete.

### Fase 3: otimizacao e acabamento

1. Reescrever importacao CSV para chunks/lotes.
2. Endurecer Docker e separar claramente dev/prod.
3. Melhorar logging, auditoria e observabilidade.
4. Consolidar pipeline de testes e CI.
5. Internalizar assets frontend.

## Arquivos e trechos que exigem revisao direta

- `app/main.py:95-171` - rate limit, gatekeeper, cookie, `SECRET_KEY`.
- `app/main.py:121-139` - bootstrap e reset de admin.
- `app/main.py:209-233` - upload CSV com leitura integral em memoria.
- `app/main.py:306-427` - alteracao de diretiva, upload PDF e remocao de anexo sem CSRF.
- `app/database.py:17-18` - `create_all()` fora do fluxo de migracoes.
- `app/models.py:35-103` - schema atual a ser reconciliado com Alembic.
- `app/services/csv_service.py:29-50` - carga integral em memoria e caches completos.
- `migrations/versions/e6ca8f306a0d_feat_add_new_relational_model_for_.py:25-95` - schema divergente.
- `migrations/versions/1d3fc7e34187_data_migrate_legacy_data_to_new_model.py:50-66` e `:89-101` - dependencia de `last_insert_rowid()`.
- `doc/09_DEPLOY_RAILWAY.md:11-17` - segredos expostos.
- `doc/10_REVISAO_SEGURANCA.txt:27-30` - batch processing nao encontrado no codigo.

## 10 acoes imediatas

1. Remover o fallback de `SECRET_KEY` e falhar no startup sem configuracao valida.
2. Implementar CSRF em todas as rotas state-changing autenticadas por cookie.
3. Revogar `ADMIN_PASSWORD` e `GATEKEEPER_PASSWORD` e limpar a documentacao.
4. Corrigir a cadeia de migracoes para refletir o schema real atual.
5. Remover `SQLModel.metadata.create_all()` do startup.
6. Tornar o bootstrap do admin idempotente sem reset automatico de senha.
7. Tirar anexos de `app/static/uploads` e servir por rota autenticada.
8. Reescrever a importacao CSV para processamento incremental.
9. Corrigir a documentacao tecnica e de seguranca para refletir o estado real do codigo.
10. Criar ambiente de testes reproduzivel e CI minima com execucao automatica.

## Limitacoes desta revisao

- A revisao foi estatica, baseada no codigo presente no repositorio.
- Nao foi possivel executar a suite com `pytest -q` neste ambiente porque `pytest` nao esta disponivel no PATH e nao ha virtualenv local na raiz do projeto.
- Nao houve validacao manual de deploy real, Railway ou banco PostgreSQL externo.
