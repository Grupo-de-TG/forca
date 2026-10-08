"""
Script de Ingestão e Estruturação do Grafo Geográfico no Neo4j.
Cria a taxonomia hierárquica (Geografia -> Continentes, Países, Estados, Municípios)
e as relações de pertencimento [:BELONGS_TO] e localização [:LOCATED_IN].
"""

from __future__ import annotations
from pathlib import Path
import sys
import time
from typing import Dict, List, Optional

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from neo4j import GraphDatabase
from core.normalizer import normalizar_texto


ESTADOS_METADATA = {
    "Acre": {"uf": "AC", "regiao": "Norte"},
    "Alagoas": {"uf": "AL", "regiao": "Nordeste"},
    "Amapá": {"uf": "AP", "regiao": "Norte"},
    "Amazonas": {"uf": "AM", "regiao": "Norte"},
    "Bahia": {"uf": "BA", "regiao": "Nordeste"},
    "Ceará": {"uf": "CE", "regiao": "Nordeste"},
    "Distrito Federal": {"uf": "DF", "regiao": "Centro-Oeste"},
    "Espírito Santo": {"uf": "ES", "regiao": "Sudeste"},
    "Goiás": {"uf": "GO", "regiao": "Centro-Oeste"},
    "Maranhão": {"uf": "MA", "regiao": "Nordeste"},
    "Mato Grosso": {"uf": "MT", "regiao": "Centro-Oeste"},
    "Mato Grosso do Sul": {"uf": "MS", "regiao": "Centro-Oeste"},
    "Minas Gerais": {"uf": "MG", "regiao": "Sudeste"},
    "Pará": {"uf": "PA", "regiao": "Norte"},
    "Paraíba": {"uf": "PB", "regiao": "Nordeste"},
    "Paraná": {"uf": "PR", "regiao": "Sul"},
    "Pernambuco": {"uf": "PE", "regiao": "Nordeste"},
    "Piauí": {"uf": "PI", "regiao": "Nordeste"},
    "Rio de Janeiro": {"uf": "RJ", "regiao": "Sudeste"},
    "Rio Grande do Norte": {"uf": "RN", "regiao": "Nordeste"},
    "Rio Grande do Sul": {"uf": "RS", "regiao": "Sul"},
    "Rondônia": {"uf": "RO", "regiao": "Norte"},
    "Roraima": {"uf": "RR", "regiao": "Norte"},
    "Santa Catarina": {"uf": "SC", "regiao": "Sul"},
    "São Paulo": {"uf": "SP", "regiao": "Sudeste"},
    "Sergipe": {"uf": "SE", "regiao": "Nordeste"},
    "Tocantins": {"uf": "TO", "regiao": "Norte"},
}

PAIS_CONTINENTE_MAP = {
    "Brasil": "América", "Argentina": "América", "Chile": "América", "Colômbia": "América",
    "Uruguai": "América", "Paraguai": "América", "Peru": "América", "Bolívia": "América",
    "Equador": "América", "Venezuela": "América", "Estados Unidos": "América", "Canadá": "América",
    "México": "América", "Cuba": "América", "Alemanha": "Europa", "França": "Europa",
    "Itália": "Europa", "Espanha": "Europa", "Portugal": "Europa", "Reino Unido": "Europa",
    "Rússia": "Europa", "Holanda": "Europa", "Suíça": "Europa", "Grécia": "Europa",
    "China": "Ásia", "Japão": "Ásia", "Índia": "Ásia", "Coreia do Sul": "Ásia",
    "Coreia do Norte": "Ásia", "Israel": "Ásia", "Arábia Saudita": "Ásia", "Turquia": "Ásia",
    "Egito": "África", "África do Sul": "África", "Nigéria": "África", "Angola": "África",
    "Moçambique": "África", "Marrocos": "África", "Austrália": "Oceania", "Nova Zelândia": "Oceania",
}


import os

def populate_geography_graph(
    uri: Optional[str] = None, 
    auth: Optional[tuple] = None
):
    if uri is None:
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    if auth is None:
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASS", "forcasecret")
        auth = (user, password)

    listas_dir = project_root / "listas"

    print(f"🚀 Conectando ao Neo4j em {uri} para estruturação do Grafo Geográfico...")
    with GraphDatabase.driver(uri, auth=auth) as driver:
        driver.verify_connectivity()
        with driver.session() as session:
            # 1. Limpar e criar constraints
            print("⚙️ Configurando Constraints e Índices...")
            session.run("CREATE CONSTRAINT theme_id_unique IF NOT EXISTS FOR (t:Theme) REQUIRE t.id IS UNIQUE")
            session.run("CREATE CONSTRAINT word_normalized_unique IF NOT EXISTS FOR (w:Word) REQUIRE w.normalized IS UNIQUE")

            # 2. Criar Hierarquia Taxonômica de Temas
            print("🗺️ Criando Árvore Taxonômica de Temas...")
            session.run("""
                MERGE (geo:Theme {id: 'geografia'})
                SET geo.name = 'Geografia Geral', geo.group = 'Geografia'

                MERGE (cont:Theme {id: 'continentes'})
                SET cont.name = 'Continentes', cont.group = 'Geografia'

                MERGE (pais:Theme {id: 'paises'})
                SET pais.name = 'Países', pais.group = 'Geografia'

                MERGE (est:Theme {id: 'estados_br'})
                SET est.name = 'Estados do Brasil', est.group = 'Geografia'

                MERGE (mun:Theme {id: 'municipios_br'})
                SET mun.name = 'Municípios Brasileiros', mun.group = 'Geografia'

                MERGE (cont)-[:SUBTHEME_OF]->(geo)
                MERGE (pais)-[:SUBTHEME_OF]->(geo)
                MERGE (est)-[:SUBTHEME_OF]->(geo)
                MERGE (mun)-[:SUBTHEME_OF]->(est)
            """)

            # 3. Importar Continentes
            print("🌐 Importando Continentes...")
            with open(listas_dir / "continentes.txt", "r", encoding="utf-8") as f:
                for line in f:
                    nome = line.strip()
                    if not nome:
                        continue
                    session.run("""
                        MERGE (w:Word {normalized: $norm})
                        SET w.text = $text, w.length = size($norm), w.type = 'continente'
                        WITH w
                        MATCH (t:Theme {id: 'continentes'})
                        MERGE (w)-[:BELONGS_TO {weight: 1.0}]->(t)
                    """, text=nome, norm=normalizar_texto(nome))

            # 4. Importar Países e Ligar a Continentes
            print("🏳️ Importando Países e relacionando a Continentes...")
            with open(listas_dir / "paises.txt", "r", encoding="utf-8") as f:
                for line in f:
                    nome = line.strip()
                    if not nome:
                        continue
                    continente_alvo = PAIS_CONTINENTE_MAP.get(nome, "América")  # Fallback default
                    session.run("""
                        MERGE (w:Word {normalized: $norm})
                        SET w.text = $text, w.length = size($norm), w.type = 'pais'
                        WITH w
                        MATCH (t:Theme {id: 'paises'})
                        MERGE (w)-[:BELONGS_TO {weight: 1.0}]->(t)
                        WITH w
                        OPTIONAL MATCH (c:Word {normalized: $cont_norm, type: 'continente'})
                        FOREACH (_ IN CASE WHEN c IS NOT NULL THEN [1] ELSE [] END |
                            MERGE (w)-[:LOCATED_IN]->(c)
                        )
                    """, text=nome, norm=normalizar_texto(nome), cont_norm=normalizar_texto(continente_alvo))

            # 5. Importar Estados do Brasil e Ligar ao Brasil
            print("🗺️ Importando Estados do Brasil e relacionando ao Brasil...")
            with open(listas_dir / "estados-br.txt", "r", encoding="utf-8") as f:
                for line in f:
                    nome = line.strip()
                    if not nome:
                        continue
                    meta = ESTADOS_METADATA.get(nome, {"uf": "--", "regiao": "Brasil"})
                    session.run("""
                        MERGE (w:Word {normalized: $norm})
                        SET w.text = $text, w.length = size($norm), w.type = 'estado',
                            w.uf = $uf, w.regiao = $regiao
                        WITH w
                        MATCH (t:Theme {id: 'estados_br'})
                        MERGE (w)-[:BELONGS_TO {weight: 1.0}]->(t)
                        WITH w
                        OPTIONAL MATCH (br:Word {normalized: 'brasil'})
                        FOREACH (_ IN CASE WHEN br IS NOT NULL THEN [1] ELSE [] END |
                            MERGE (w)-[:LOCATED_IN]->(br)
                        )
                    """, text=nome, norm=normalizar_texto(nome), uf=meta["uf"], regiao=meta["regiao"])

            # 6. Importar Municípios Brasileiros em Lote
            print("🏙️ Importando Municípios Brasileiros...")
            municipios = []
            seen = set()
            with open(listas_dir / "municipios-br.txt", "r", encoding="utf-8") as f:
                for line in f:
                    nome = line.strip()
                    if not nome:
                        continue
                    norm = normalizar_texto(nome)
                    if norm not in seen:
                        seen.add(norm)
                        municipios.append({"text": nome, "norm": norm, "len": len(norm)})

            batch_size = 1000
            total_batches = (len(municipios) + batch_size - 1) // batch_size
            for b_idx in range(total_batches):
                batch = municipios[b_idx * batch_size : (b_idx + 1) * batch_size]
                session.run("""
                    UNWIND $batch AS item
                    MERGE (w:Word {normalized: item.norm})
                    SET w.text = item.text, w.length = item.len, w.type = 'municipio'
                    WITH w
                    MATCH (t:Theme {id: 'municipios_br'})
                    MERGE (w)-[:BELONGS_TO {weight: 1.0}]->(t)
                    WITH w
                    OPTIONAL MATCH (br:Word {normalized: 'brasil'})
                    FOREACH (_ IN CASE WHEN br IS NOT NULL THEN [1] ELSE [] END |
                        MERGE (w)-[:LOCATED_IN]->(br)
                    )
                """, batch=batch)

            # 7. Resumo Final
            print("\n✅ Grafo Geográfico populado com sucesso!")
            res_words = session.run("MATCH (w:Word) RETURN count(w) as total").single()["total"]
            res_themes = session.run("MATCH (t:Theme) RETURN count(t) as total").single()["total"]
            res_located = session.run("MATCH ()-[r:LOCATED_IN]->() RETURN count(r) as total").single()["total"]
            res_belongs = session.run("MATCH ()-[r:BELONGS_TO]->() RETURN count(r) as total").single()["total"]

            print(f"📊 Estatísticas:")
            print(f"   • Nós de Palavras: {res_words:,}")
            print(f"   • Nós de Temas:    {res_themes}")
            print(f"   • Relações [:BELONGS_TO]: {res_belongs:,}")
            print(f"   • Relações [:LOCATED_IN]: {res_located:,}")


if __name__ == "__main__":
    populate_geography_graph()
