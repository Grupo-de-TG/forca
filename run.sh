#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Verifica se o usuário pediu execução local sem Docker
if [[ "$1" == "--local" ]]; then
    echo "🎮 Executando Forca em modo Python Local..."
    if [ ! -d ".venv" ]; then
        python3 -m venv .venv
        .venv/bin/pip install -r requirements.txt
    fi
    source .venv/bin/activate
    python forca_app.py
    exit 0
fi

# Verifica se o setup foi executado previamente
if [ ! -f ".env" ]; then
    echo "⚠️ Arquivo de configuração .env não encontrado."
    echo "Executando setup padrão com Neo4j..."
    ./setup.sh --grafo
fi

# Carrega variáveis
export $(cat .env | xargs)

# Garante que o container do Neo4j (Knowledge Graph de Dicas) está rodando
if ! docker compose ps forca-neo4j | grep -q "Up"; then
    echo "🌐 Iniciando container do Neo4j (Grafo de Dicas)..."
    docker compose up -d forca-neo4j
    sleep 2
fi

# Inicia o jogo conectado ao TTY do terminal
docker compose run --rm forca-app
