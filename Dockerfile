FROM python:3.11-slim

# Configuração de TTY e saída não-bufferizada para a interface Textual
ENV PYTHONUNBUFFERED=1 \
    TERM=xterm-256color \
    COLORTERM=truecolor \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

WORKDIR /app

# Instala bibliotecas do sistema essenciais
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia código-fonte e listas
COPY . .

# Comando padrão
CMD ["python", "forca_app.py"]
