# Guia de Operação - SIGDT

Este documento orienta sobre o uso das funcionalidades do sistema SIGDT.

---

## 🔐 1. Acesso Inicial (Gatekeeper)
Para proteger os dados, o primeiro acesso ao site requer uma senha global definida no contêiner ou no arquivo `.env` seguro.
*   Esta camada protege o site mesmo antes do login individual e impede vazamentos.

---

## 📊 2. Dashboard e Navegação
Ao entrar, você verá a lista de diretivas vinculadas às aeronaves.
*   **Filtros Inteligentes:** Clicando nos dropdowns (apenas usuários logados), é possível filtrar e sobrepor Especialidades e Status de andamento atuais.
*   **Especialidades Gráficas:** Cada Diretiva apresenta as especialidades (ELE, MEC, etc) atreladas formatadas em pílulas num Grid responsivo.
*   **Busca:** Use a barra lateral para filtrar por Matrícula, SN ou Código da DT.
*   **Tooltip:** Passe o mouse sobre uma linha para ler o objetivo da diretiva sem precisar abrir os detalhes.
*   **Paginação Otimizada:** Use os botões no rodapé para navegar perfeitamente entre milhares de registros sem travar o servidor.
*   **Exportar:** O botão (só visível para login) gera um arquivo Excel com a situação atual da frota.

---

## ✈️ 3. Detalhes, Anexos e Extrator Inteligente
Clique em qualquer linha para abrir a janela de detalhes.
*   **Visualização Nativa:** Todos podem ver os comprovantes em PDF que abrem num prático pop-up flutuante interno (Modal).
*   **Extração Automática:** Admins ou Inspetores, ao enviarem o PDF, terão o arquivo inteiramente lido pela IA (AT Parser). Campos como Serviço e Parecer serão dissecados e transcritos instantaneamente na tela!
*   **Execução (Inspetor/Admin):** 
    *   Altere o Status (Pendente, Concluída, etc).
    *   Com a ajuda do Parser, escreva ativamente notas corretas para relatar a DT.
*   **Restrição:** Um inspetor só pode salvar alterações se a especialidade da DT o permitir.

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
