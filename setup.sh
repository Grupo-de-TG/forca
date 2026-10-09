#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================================="
echo "🎮 JOGO DA FORCA - PROVISIONAMENTO MULTI-BANCO (DOCKER)"
echo "=========================================================="
echo "🐬 MySQL 8.0:      Usuários, Autenticação e Ranking"
echo "🍃 MongoDB 6.0:    Vocabulário, Dicionário e Logs de Partidas"
echo "🌐 Neo4j 5.26:     Knowledge Graph de Dicas Contextuais"
echo "=========================================================="
echo ""

# 1. Configura arquivo .env
echo "Configurando variáveis de ambiente em .env..."
cat <<EOF > .env
MYSQL_HOST=forca-mysql
MYSQL_PORT=3306
MYSQL_USER=forca_user
MYSQL_PASSWORD=forca_password
MYSQL_DATABASE=forca_db
MONGO_URI=mongodb://forca-mongodb:27017/
MONGO_DATABASE=forca_db
DICIONARIO_MAX_POR_CATEGORIA=500
WORD_BACKEND=mongo
NEO4J_URI=bolt://forca-neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASS=forcasecret
EOF

# 2. Build da imagem Docker da aplicação
echo "🔨 Construindo imagem Docker do forca-app..."
docker compose build forca-app

# 3. Inicialização dos Containers de Banco de Dados
echo "🌐 Iniciando containers de banco de dados (MySQL, MongoDB, Neo4j)..."
docker compose up -d forca-mysql forca-mongodb forca-neo4j

# 4. Aguarda inicialização dos serviços
echo "⏳ Aguardando MySQL inicializar..."
until docker compose exec forca-mysql mysqladmin ping -h localhost -u root -prootpassword > /dev/null 2>&1; do
    sleep 2
    echo -n "."
done
echo " MySQL Pronto!"

echo "⏳ Aguardando MongoDB inicializar..."
until docker compose exec forca-mongodb mongosh --quiet --eval "db.adminCommand('ping').ok" > /dev/null 2>&1; do
    sleep 2
    echo -n "."
done
echo " MongoDB Pronto!"

echo "⏳ Aguardando Neo4j inicializar..."
until docker compose exec forca-neo4j cypher-shell -u neo4j -p forcasecret "RETURN 1;" > /dev/null 2>&1; do
    sleep 2
    echo -n "."
done
echo " Neo4j Pronto!"

# 5. População dos Bancos
echo ""
echo "🍃 [1/2] Populando Dicionário no MongoDB..."
docker compose run --rm forca-app python seed_dicionario.py

echo ""
echo "🌐 [2/2] Populando Knowledge Graph Geográfico no Neo4j..."
docker compose run --rm forca-app python scripts/populate_graph_geography.py

echo ""
echo "=========================================================="
echo "✅ Setup Multi-Banco concluído com sucesso!"
echo "Para iniciar o jogo no terminal, execute: ./run.sh"
echo "=========================================================="
