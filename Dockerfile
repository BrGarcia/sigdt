# Usa uma imagem oficial e leve do Python 3.11
FROM python:3.11-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia o arquivo de requisitos primeiro para aproveitar o cache do Docker
COPY requirements.txt .

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código do projeto para o container
COPY . .

# A porta será definida pela variável de ambiente PORT do Railway
# Se não houver, o padrão é 8080 (Railway default)
ENV PORT=8080
EXPOSE 8080

# Usamos sh -c para garantir que as migrações rodem antes do app
# Adicionamos --proxy-headers e --forwarded-allow-ips para lidar com o proxy do Railway
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
