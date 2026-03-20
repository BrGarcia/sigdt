# Guia de Instalação e Hospedagem - SIGDT

Este guia foi criado para ajudar qualquer pessoa, mesmo com pouco conhecimento técnico, a colocar o **SIGDT** para funcionar, seja no próprio computador ou em um servidor na internet.

---

## 💻 1. Como rodar no seu computador (Localhost)

Você tem duas formas de fazer isso: a **Manual** (instalando o Python) ou a **Automática** (usando Docker).

### A. Forma Automática (Recomendado - "Estilo Docker")
O Docker funciona como um "pacote" que já vem com tudo dentro: o site, o banco de dados e as configurações. Você não precisa instalar o Python no seu PC.

1.  Instale o **Docker Desktop** no seu Windows.
2.  Abra uma pasta no seu computador com os arquivos do projeto.
3.  Abra o terminal (PowerShell) e digite:
    ```powershell
    docker-compose up --build
    ```
4.  Pronto! Abra seu navegador e acesse: `http://localhost:8000`

### B. Forma Manual (Instalando Python)
Se você preferir não usar Docker:
1.  Instale o **Python 3.11** (ou superior) no seu computador.
2.  Abra o terminal na pasta do projeto e instale as bibliotecas necessárias:
    ```powershell
    pip install -r requirements.txt
    ```
3.  Inicie o servidor do site:
    ```powershell
    uvicorn app.main:app --reload
    ```
4.  Acesse: `http://localhost:8000`

---

## 🌐 2. Posso usar XAMPP ou WAMPP?

**Resposta curta: Não diretamente.**

*   **XAMPP/WAMPP:** São ferramentas feitas especificamente para sites em **PHP** (como WordPress).
*   **SIGDT:** É feito em **Python (FastAPI)**.

Embora o XAMPP tenha um módulo para Python (CGI), ele não é recomendado para aplicações modernas como esta. O equivalente moderno e profissional ao XAMPP para este projeto é o **Docker**, que "compacta" tudo o que o site precisa para rodar em qualquer lugar.

---

## ☁️ 3. Como colocar o site na Internet (Hospedagem)

Sim, você pode hospedar o SIGDT na internet para que outras pessoas acessem de qualquer lugar.

### Onde hospedar?
1.  **PaaS (Fácil):** Serviços como **Render.com**, **Railway.app** ou **Fly.io**. Eles leem seu código no GitHub e colocam no ar automaticamente.
2.  **VPS (Profissional):** Servidores "vazios" (DigitalOcean, AWS, Google Cloud). Aqui você instala o Docker e roda o comando `docker-compose up`.

### Requisitos do Servidor:
O SIGDT foi feito para ser **extremamente leve**.
*   **Memória RAM:** 512MB ou 1GB (é o plano mais barato que existe).
*   **Processador:** 1 CPU (básico).
*   **Sistema:** Linux (Ubuntu) é o padrão de mercado para servidores.

---

## 📦 4. Como "compactar" para o servidor?

Em vez de compactar em um arquivo `.zip` comum, o padrão moderno é criar uma **Imagem Docker**.

1.  Você faz o código e o arquivo `Dockerfile` (já incluído no projeto).
2.  O servidor baixa esse código do seu GitHub.
3.  O servidor "constrói" o ambiente sozinho.

Se você quiser enviar manualmente sem GitHub:
1.  Compacte a pasta do projeto em um `.zip` (ignore as pastas `__pycache__` e o arquivo `sigdt.db`).
2.  Envie para o servidor via FTP ou SSH.
3.  No servidor, descompacte e rode o comando do Docker.

---

## 🛡️ Segurança Básica
Ao colocar na internet:
*   **Não use SQLite:** O arquivo `sigdt.db` é bom para testes. Para o site na internet com muitos acessos, use o **PostgreSQL** (configuração já incluída no nosso `docker-compose.yml`).
*   **HTTPS:** Sempre use um certificado de segurança (o Render.com, por exemplo, já dá isso de graça).
