# Guia de Operação - SIGDT

Este documento orienta sobre o uso das funcionalidades do sistema SIGDT.

---

## 🔐 1. Acesso Inicial (Gatekeeper)
Para proteger os dados, o primeiro acesso ao site requer uma senha global.
*   **Senha:** `asdf1234`
*   Esta camada protege o site mesmo antes do login individual.

---

## 📊 2. Dashboard e Navegação
Ao entrar, você verá a lista de diretivas vinculadas às aeronaves.
*   **Busca:** Use a barra lateral para filtrar por Matrícula, SN ou Código da DT.
*   **Tooltip:** Passe o mouse sobre uma linha para ler o objetivo da diretiva sem precisar abrir os detalhes.
*   **Paginação:** Use os botões no rodapé para navegar entre os registros (50 por página).
*   **Exportar:** O botão no topo da tabela gera um arquivo Excel com a situação atual da frota.

---

## ✈️ 3. Detalhes e Cumprimento
Clique em qualquer linha para abrir a janela de detalhes.
*   **Visualização (Público):** Todos podem ver o status e baixar arquivos PDF anexos.
*   **Execução (Inspetor/Admin):** 
    *   Altere o Status (Pendente, Concluída, etc).
    *   Escreva observações técnicas da execução naquela aeronave.
    *   Anexe comprovantes em PDF.
*   **Restrição:** Um inspetor só pode salvar alterações se a especialidade da DT coincidir com a sua (ex: Elétrica).

---

## 📜 4. Menu "Diretivas" (Gestão Global)
Acessível apenas por Inspetores e Admins.
*   Nesta tela, você edita a **norma mestre**.
*   Alterar o Objetivo ou a Prioridade (GUT) aqui mudará esses dados para **todas as aeronaves** simultaneamente.
*   Aqui você define quais especialidades são responsáveis por cada DT.

---

## 👥 5. Menu "Usuários" (Administrador)
Acessível apenas por Administradores.
*   **Cadastro:** Crie novos inspetores definindo seu e-mail e especialidade técnica.
*   **Gestão:** Visualize todos os usuários cadastrados no sistema.

---

## 📥 6. Importação de Dados
*   **Múltiplos Arquivos:** No menu lateral do dashboard, admins podem selecionar vários arquivos CSV de uma vez.
*   **Lógica de Proteção:** O sistema verifica se a aeronave e a DT já existem. Se existirem, ele apenas atualiza os dados, evitando duplicidade de registros.
