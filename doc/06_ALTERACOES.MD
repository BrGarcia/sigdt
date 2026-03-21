ALTERACOES NA VERSAO 2.0.0 (CONCLUÍDO):
	[NOVA FUNCIONALIDADE] AT PARSER:
		Implementação da biblioteca PyMuPDF para ler automaticamente arquivos PDF de Assessoramento Técnico.
		Extração automática dos campos: Ficha A.T., Serviço Solicitado e Parecer da Engenharia.
		Exibição desses textos diretamente na página de Detalhamento da Diretiva para facilitar a consulta rápida sem abrir o anexo.
	[DASHBOARD UI] Coluna ESPECIALIDADE:
		Exibir uma nova coluna com pequenos boxes (badges) coloridos contendo os trigramas:
		- ELT (Eletrônica)
		- ELE (Elétrica)
		- CEL (Célula)
		- MOT (Motores)
		- EQV (Equipamento de Voo)
		- TODAS (Caso a DT se aplique a todas as especialidades)
	[BANCO DE DADOS] Atualização da tabela DiretivaAeronave para incluir campos de texto para os dados extraídos (at_numero, at_servico, at_parecer).
	[INFRAESTRUTURA E SEGURANÇA] Migrações e Blindagem:
		Adoção do Alembic para gerir evolução de esquemas de Banco (SQLite/PostgreSQL).
		Remoção de todas as senhas hardcoded via fallback, exigindo obrigatoriamente variáveis de ambiente (.env).
		Proteção total das rotas de extração de relatórios e requisições assíncronas (HTMX) bloqueando visitantes anônimos.

ALTERACOES NA TELA DASHBOARD (CONCLUÍDO v1.0):
	REMOVER COLUNA PN/CFF E MANTER COLUNA "MATRICULA"
	RENOMEAR COLUNA "DT / TAREFA" PARA APENAS "DIRETIVA TECNICA"
	ADICIONAR ICONE/BOTAO PARA PASSAR AS PAGINAS CASO A QUANTIDADE DE REGISTROS SEJA ALTA.
	ADICIONAR O OBJETIVO DA DIRETIVA TECNICA QUANDO PASSAR COM O MOUSE POR CIMA (MOUSEOVER)
	INSERIR BOTAO PARA EXPORTAR TABELA EM XLSX

ALTERAÇÕES NA CAMADA INSPETOR (CONCLUÍDO v1.0):
	INSERIR BOTAO PARA ANEXAR DOCUMENTACAO PERTINIENTE (EM PDF) NA PAGINA DE EDICAO
	NO CAMPO DE EDICAO SO PERMITIR ALTERAÇÕES CASO O INSPETOR SEJA DA MESMA ESPECIALIDADE DA DIRETIVA (ELETRÔNICA;ELÉTRICA;CÉLULA;HIDRÁULICA;MOTORES;EQV)

ALTERACOES NA CAMADA ADMINISTRADOR (CONCLUÍDO v1.0):
	NA JANELA EDICAO INSERIR UM CAMPO PARA ESPECIALIDADE RESPONSAVEL PELO DT (ELETRÔNICA;ELÉTRICA;CÉLULA;HIDRÁULICA;MOTORES;EQV)
	PERMITIR A ADICAO DE MAIS DE UM ARQUIVO *.CSV POR VEZ
	ANTES DE ADICIONAR AO BANCO DE DADOS, VERIFICAR SE AS INFORMACOES CONTIDAS CSV NO ARQUIVO JA  NAO ESTAO PRESENTES NO BANCO DE DADOS PARA EVITAR ENTRADAS DUPLICADAS.