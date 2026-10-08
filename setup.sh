#!/bin/bash
set -e

BACKEND="graph"

# Processamento de flags
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --grapho|--grafo|--graph)
            BACKEND="graph"
            shift
            ;;
        --arquivo|--file|--local)
            BACKEND="file"
            shift
            ;;
        -h|--help)
            echo "Uso: ./setup.sh [--grafo | --arquivo]"
            echo ""
            echo "Opções:"
            echo "  --grafo    Configura ambiente com container Neo4j e popula grafo geográfico (Padrão)"
            echo "  --arquivo  Configura ambiente usando arquivos locais listas/*.txt"
            exit 0
            ;;
        *)
            echo "Opção desconhecida: $1"
            echo "Execute ./setup.sh --help para ver as opções disponíveis."
            exit 1
            ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================="
echo "🎮 JOGO DA FORCA - SETUP DO AMBIENTE DOCKER"
echo "============================================="
echo "📦 Backend de Vocabulário selecionado: $BACKEND"
echo ""

# 1. Configura arquivo .env
echo "WORD_BACKEND=$BACKEND" > .env
echo "NEO4J_URI=bolt://forca-neo4j:7687" >> .env
echo "NEO4J_USER=neo4j" >> .env
echo "NEO4J_PASS=forcasecret" >> .env

# 2. Build da imagem Docker da aplicação
echo "🔨 Construindo imagem Docker do forca-app..."
docker compose build forca-app

# 3. Provisionamento e população de acordo com o backend
if [ "$BACKEND" == "graph" ]; then
    echo "🌐 Iniciando container do Neo4j Graph Database..."
    docker compose up -d forca-neo4j

    echo "⏳ Aguardando Neo4j inicializar..."
    until docker compose exec forca-neo4j cypher-shell -u neo4j -p forcasecret "RETURN 1;" > /dev/null 2>&1; do
        sleep 2
        echo -n "."
    done
    echo " Pronto!"

    echo "📊 Populando Grafo Geográfico no Neo4j..."
    docker compose run --rm forca-app python scripts/populate_graph_geography.py
fi

echo ""
echo "============================================="
echo "✅ Setup concluído com sucesso!"
echo "Para iniciar o jogo no terminal, execute: ./run.sh"
echo "============================================="
