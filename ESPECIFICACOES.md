# Especificações do Projeto: Sistema de Gestão de Diretivas Técnicas (DT)

## 1. Visão Geral
O objetivo deste projeto é transpor a gestão de diretivas técnicas de manutenção aeronáutica (atualmente em Excel) para uma aplicação web robusta, segura e extremamente leve. O sistema deve priorizar a velocidade de acesso à informação, especialmente em hardware limitado, utilizando uma arquitetura moderna de processamento no servidor.

---

---

## 3. Arquitetura Técnica (Stack Sugerida)
Para atender ao requisito de "computadores lentos" e "segurança robusta":

*   **Backend:** Python 3.10+ com **FastAPI** (Alta performance e tipagem).
*   **Frontend:** **HTMX** com **Tailwind CSS**. 
    *   *Por que:* O HTMX envia fragmentos de HTML prontos do servidor, reduzindo drasticamente o processamento de JavaScript no navegador do cliente (ideal para máquinas antigas).
*   **Banco de Dados:** PostgreSQL (Produção) ou SQLite (Desenvolvimento/Local).
*   **Segurança:** Autenticação via JWT ou Sessão Segura com RBAC (Controle de Acesso Baseado em Funções).

---

## 4. Funcionalidades Principais
### 4.1 Ingestão de Dados (User-Admin)
*   Upload de arquivo `*.csv` via interface administrativa.
*   O sistema deve seguir rigorosamente o `modelo.csv`.
*   Lógica de **Upsert**: Atualizar registros existentes (chave: SN/CJM) e inserir novos.
*   Validação de esquema e tipos de dados no momento do upload.

### 4.2 Visualização e Filtros (Dashboard)
*   Listagem principal com paginação do lado do servidor (Server-side pagination).
*   Abas dinâmicas por especialidade (Ex: ELT, MOT, HID, CEL, etc.).
*   Busca global instantânea (SN, Matrícula, Diretiva).
*   Exportação de relatórios filtrados.

---

## 5. Regras de Negócio: Matriz GUT
O sistema deve calcular automaticamente a prioridade das diretivas com base nos pesos abaixo:

### 5.1 Gravidade (G) - Coluna "CLA" (Classe)
| Classe | Peso |
| :--- | :--- |
| **MANDATORIA** | 5 |
| **RECOMENDADA** | 4 |
| **OPCIONAL** | 2 |
| **INFORMATIVA** | 1 |

### 5.2 Urgência (U) - Coluna "CAT" (Categoria)
| Categoria | Peso |
| :--- | :--- |
| **IMEDIATA** | 5 |
| **URGENTE** | 4 |
| **ROTINA** | 2 |

### 5.3 Tendência (T)
*   Valor padrão inicial: **3**.
*   Deve ser editável individualmente por registro através da interface.

### 5.4 Cálculo de Prioridade
**Fórmula:** `GUT = G * U * T`
*   A listagem principal deve ser ordenada por padrão de forma decrescente pelo valor de GUT.

---

## 6. Requisitos de Segurança
*   Dados sensíveis: O acesso deve ser restrito a usuários autenticados.
*   Sanitização completa de inputs para evitar SQL Injection e XSS.
*   Logs de auditoria para uploads de novos arquivos CSV (quem subiu e quando).

---

## 7. Entregáveis Esperados
1. Código-fonte em repositório Git.
2. `Dockerfile` e `docker-compose.yml` para deploy simplificado.
3. Documentação da API (Swagger/OpenAPI gerado pelo FastAPI).
4. Script de migração inicial do banco de dados.
