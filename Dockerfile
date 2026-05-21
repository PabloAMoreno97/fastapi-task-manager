FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends dos2unix \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Normalize line endings (CRLF → LF) in case the file was created on Windows
RUN dos2unix scripts/start.sh && chmod +x scripts/start.sh

EXPOSE 8000

CMD ["./scripts/start.sh"]
