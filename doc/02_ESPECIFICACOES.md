# Especificações do Projeto: Sistema de Gestão de Diretivas Técnicas (DT) - Versão 2.0

## 1. Visão Geral
O objetivo deste projeto é transpor a gestão de diretivas técnicas de manutenção aeronáutica para uma aplicação web robusta, segura e extremamente leve. O sistema prioriza a velocidade de acesso à informação, especialmente em hardware limitado, utilizando uma arquitetura moderna de processamento no servidor.

A versão 2.0 introduz um sistema de controle de acesso baseado em três níveis de usuário, garantindo que a informação correta esteja acessível às pessoas certas.

---

## 2. Arquitetura Técnica
*   **Backend:** Python 3.11+ com **FastAPI**.
*   **Frontend:** **HTMX** com **Tailwind CSS**. A renderização é feita no lado do servidor para garantir performance máxima em clientes com hardware limitado.
*   **Banco de Dados:** PostgreSQL (Produção) e SQLite (Desenvolvimento).
*   **Containerização:** Docker e Docker Compose.

---

## 3. Controle de Acesso Baseado em Funções (RBAC)
O sistema agora opera com três níveis de acesso distintos:

### 3.1 Usuário Básico (Acesso Público)
*   **Acesso:** Não requer login.
*   **Permissões:**
    *   Visualizar a lista completa de diretivas.
    *   Buscar e filtrar diretivas.
    *   Visualizar os detalhes de uma diretiva específica.
    *   **Nenhuma** permissão de escrita ou modificação.

### 3.2 Usuário Inspetor (`inspector`)
*   **Acesso:** Requer login.
*   **Permissões:**
    *   Todas as permissões do Usuário Básico.
    *   Adicionar e editar observações em uma diretiva.
    *   Modificar o status de uma diretiva (ex: "Pendente", "Em andamento", "Concluída").

### 3.3 Usuário Administrador (`admin`)
*   **Acesso:** Requer login.
*   **Permissões:**
    *   Todas as permissões do Usuário Inspetor.
    *   Fazer o upload de novos arquivos `*.csv` para ingestão de dados.
    *   Editar o valor de "Tendência" (T) de uma diretiva.
    *   Gerenciar contas de usuários (criar, visualizar, deletar inspetores).

---

## 4. Funcionalidades Principais

### 4.1 Ingestão de Dados (Admin)
*   Upload de arquivo `*.csv` através de uma interface administrativa segura.
*   Lógica de **Upsert**: O sistema atualiza registros existentes (chave: `SN/CJM` + `Diretiva Técnica`) e insere novos.

### 4.2 Visualização e Filtros (Público)
*   Dashboard principal como landing page, acessível publicamente.
*   Busca global instantânea por SN, Matrícula ou Diretiva.
*   Toda a tabela é "clicável", levando à página de detalhes da diretiva.

### 4.3 Edição e Detalhes (Inspetor/Admin)
*   Página de detalhes para cada diretiva.
*   Formulário para que inspetores e administradores atualizem o **status** e as **observações**.
*   Formulário para que administradores atualizem a **tendência**.

### 4.4 Gerenciamento de Usuários (Admin)
*   Interface para administradores criarem novas contas de inspetores.

---

## 5. Regras de Negócio: Matriz GUT
O cálculo de prioridade permanece o mesmo:

**Fórmula:** `GUT = G * U * T`

*   **Gravidade (G):** Baseado na coluna "CLA" (M=5, R=4, O=2, I=1).
*   **Urgência (U):** Baseado na coluna "CAT" (I=5, U=4, R=2).
*   **Tendência (T):** Valor padrão `3`, editável apenas por administradores.

A lista de diretivas é ordenada por padrão de forma decrescente pelo valor de GUT.

---

## 6. Requisitos de Segurança (Implementados)
*   **Acesso Restrito:** Funcionalidades de escrita e gerenciamento são protegidas por login e nível de acesso.
*   **Prevenção de SQL Injection:** As consultas ao banco de dados são parametrizadas através do ORM (SQLModel).
*   **Segredos:** Credenciais do banco de dados são gerenciadas via variáveis de ambiente (`.env`) e não estão hardcoded no código.
*   **Criação de Usuário Padrão:** Um usuário `admin` com senha `admin` é criado no primeiro boot da aplicação para acesso inicial.

---

## 7. Entregáveis
1. Código-fonte completo no repositório Git.
2. `Dockerfile` e `docker-compose.yml` para deploy simplificado.
3. Documentação da API (Swagger/OpenAPI gerado pelo FastAPI).
4. Script de migração e criação de usuário inicial automatizado.
