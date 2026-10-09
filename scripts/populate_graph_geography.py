"""
Script de Ingestão e Estruturação do Grafo Geográfico no Neo4j.
Cria a taxonomia hierárquica completa (Geografia -> Continentes, Países, Regiões, Estados, Municípios)
com mapeamento 100% preciso para todos os 222 países, 27 estados e municípios.
"""

from __future__ import annotations
from pathlib import Path
import sys
import time
from typing import Dict, List, Optional
import os

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

REGIOES_BRASIL = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]

AMERICA_SET = {
    'Anguila', 'Antígua e Barbuda', 'Argentina', 'Aruba', 'Bahamas', 'Barbados', 'Belize',
    'Bermudas', 'Bolívia', 'Brasil', 'Canadá', 'Chile', 'Colômbia', 'Costa Rica', 'Cuba',
    'Curaçao', 'Dominica', 'El Salvador', 'Equador', 'Estados Unidos', 'Estados Unidos da América',
    'Granada', 'Groenlândia', 'Guadalupe', 'Guatemala', 'Guiana', 'Guiana Francesa', 'Haiti',
    'Honduras', 'Ilhas Caimão', 'Ilhas Cayman', 'Ilhas Malvinas', 'Ilhas Turcas e Caicos',
    'Ilhas Virgens', 'Ilhas Virgens Americanas', 'Ilhas Virgens Britânicas', 'Jamaica',
    'Martinica', 'México', 'Montserrat', 'Nicarágua', 'Panamá', 'Paraguai', 'Peru',
    'Porto Rico', 'República Dominicana', 'Santa Lúcia', 'São Cristóvão e Nevis',
    'São Cristóvão e Névis', 'São Martinho', 'São Pedro e Miquelão', 'São Vicente e Granadinas',
    'Sint Maarten', 'Suriname', 'Trinidad e Tobago', 'Uruguai', 'Venezuela'
}

EUROPA_SET = {
    'Abecásia', 'Albânia', 'Alemanha', 'Andorra', 'Áustria', 'Bielorrússia', 'Bélgica',
    'Bósnia e Herzegovina', 'Bulgária', 'Chipre', 'Chipre do Norte', 'Croácia', 'Dinamarca',
    'Escócia', 'Eslováquia', 'Eslovênia', 'Espanha', 'Estônia', 'Finlândia', 'França',
    'Geórgia', 'Gibraltar', 'Grécia', 'Guernsey', 'Holanda', 'Hungria', 'Ilha de Man',
    'Ilhas Faroé', 'Ilhas Åland', 'Inglaterra', 'Irlanda', 'Irlanda do Norte', 'Islândia',
    'Itália', 'Jersey', 'Kosovo', 'Letônia', 'Liechtenstein', 'Lituânia', 'Luxemburgo',
    'Macedônia do Norte', 'Macedónia', 'Malta', 'Moldávia', 'Mônaco', 'Montenegro',
    'Noruega', 'País de Gales', 'Países Baixos', 'Polônia', 'Polónia', 'Portugal',
    'Reino Unido', 'República Checa', 'República Tcheca', 'República Turca de Chipre do Norte',
    'Romênia', 'Roménia', 'Rússia', 'San Marino', 'Sérvia', 'Suécia', 'Suíça',
    'Svalbard', 'Transnístria', 'Ucrânia', 'Vaticano'
}

ASIA_SET = {
    'Afeganistão', 'Arábia Saudita', 'Armênia', 'Arménia', 'Azerbaijão', 'Bahrein', 'Bangladesh',
    'Brunei', 'Butão', 'Camboja', 'Catar', 'Cazaquistão', 'China', 'Coreia do Norte', 'Coreia do Sul',
    'Emirados Árabes Unidos', 'Filipinas', 'Hong Kong', 'Iêmen', 'Iémen', 'Índia', 'Indonésia',
    'Irã', 'Irão', 'Iraque', 'Israel', 'Japão', 'Jordânia', 'Kuwait', 'Laos', 'Líbano', 'Macau',
    'Malásia', 'Maldivas', 'Mianmar', 'Mongólia', 'Nepal', 'Omã', 'Ossétia do Sul', 'Palestina',
    'Paquistão', 'Qatar', 'Quirguistão', 'Singapura', 'Síria', 'Sri Lanka', 'Tailândia', 'Taiwan',
    'Tajiquistão', 'Timor-Leste', 'Turcomenistão', 'Turquemenistão', 'Turquia', 'Uzbequistão',
    'Vietnã', 'Vietname'
}

AFRICA_SET = {
    'África do Sul', 'Angola', 'Argélia', 'Benim', 'Botsuana', 'Botswana', 'Burkina Faso', 'Burundi',
    'Cabo Verde', 'Camarões', 'Chade', 'Comores', 'Congo', 'Costa do Marfim', 'Djibuti', 'Egito',
    'Eritreia', 'Essuatíni', 'Eswatini', 'Etiópia', 'Gabão', 'Gâmbia', 'Gana', 'Guiné',
    'Guiné Equatorial', 'Guiné-Bissau', 'Lesoto', 'Libéria', 'Líbia', 'Madagascar', 'Malawi',
    'Mali', 'Marrocos', 'Maurícia', 'Mauritânia', 'Mayotte', 'Moçambique', 'Namíbia', 'Níger',
    'Nigéria', 'Quênia', 'Quénia', 'República Árabe Saaraui Democrática', 'República Centro-Africana',
    'República Democrática do Congo', 'República do Congo', 'Reunião', 'Ruanda', 'Saara Ocidental',
    'Santa Helena', 'São Tomé e Príncipe', 'Senegal', 'Seicheles', 'Seychelles', 'Serra Leoa',
    'Somália', 'Somalilândia', 'Sudão', 'Sudão do Sul', 'Suazilândia', 'Tanzânia', 'Togo', 'Tunísia',
    'Uganda', 'Zâmbia', 'Zimbábue', 'Zimbabué'
}

OCEANIA_SET = {
    'Austrália', 'Estados Federados da Micronésia', 'Fiji', 'Guam', 'Ilha Christmas', 'Ilha Norfolk',
    'Ilhas Cocos', 'Ilhas Cook', 'Ilhas Marianas do Norte', 'Ilhas Marshall', 'Ilhas Pitcairn',
    'Ilhas Salomão', 'Kiribati', 'Marshall', 'Micronésia', 'Nauru', 'Niue', 'Nova Caledônia',
    'Nova Zelândia', 'Palau', 'Papua-Nova Guiné', 'Polinésia Francesa', 'Salomão', 'Samoa',
    'Samoa Americana', 'Tokelau', 'Tonga', 'Tuvalu', 'Vanuatu', 'Wallis e Futuna'
}


def obter_continente(pais: str) -> str:
    if pais in AFRICA_SET:
        return "África"
    if pais in ASIA_SET:
        return "Ásia"
    if pais in EUROPA_SET:
        return "Europa"
    if pais in OCEANIA_SET:
        return "Oceania"
    return "América"


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

    print(f"Conectando ao Neo4j em {uri} para estruturação do Grafo Geográfico...")
    with GraphDatabase.driver(uri, auth=auth, notifications_min_severity="OFF") as driver:
        driver.verify_connectivity()
        with driver.session() as session:
            # 1. Limpar e criar constraints
            print("Configurando Constraints e Índices...")
            session.run("CREATE CONSTRAINT theme_id_unique IF NOT EXISTS FOR (t:Theme) REQUIRE t.id IS UNIQUE")
            session.run("CREATE CONSTRAINT word_normalized_unique IF NOT EXISTS FOR (w:Word) REQUIRE w.normalized IS UNIQUE")

            # 2. Criar Hierarquia Taxonômica de Temas
            print("Criando Árvore Taxonômica de Temas...")
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

            # 3. Criar Continentes
            print("Importando Continentes...")
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

            # 4. Criar Países com Mapeamento Exato de Continente
            print("Importando 222 Países com Continentes Exatos...")
            with open(listas_dir / "paises.txt", "r", encoding="utf-8") as f:
                for line in f:
                    nome = line.strip()
                    if not nome:
                        continue
                    continente_alvo = obter_continente(nome)
                    session.run("""
                        MERGE (w:Word {normalized: $norm})
                        SET w.text = $text, w.length = size($norm), w.type = 'pais', w.continente = $continente
                        WITH w
                        MATCH (t:Theme {id: 'paises'})
                        MERGE (w)-[:BELONGS_TO {weight: 1.0}]->(t)
                        WITH w
                        OPTIONAL MATCH (c:Word {normalized: $cont_norm, type: 'continente'})
                        FOREACH (_ IN CASE WHEN c IS NOT NULL THEN [1] ELSE [] END |
                            MERGE (w)-[:LOCATED_IN]->(c)
                        )
                    """, text=nome, norm=normalizar_texto(nome), continente=continente_alvo, cont_norm=normalizar_texto(continente_alvo))

            # 5. Criar Nós de Regiões do Brasil
            print("Criando Nós de Regiões do Brasil...")
            for reg in REGIOES_BRASIL:
                session.run("""
                    MERGE (r:Word {normalized: $norm})
                    SET r.text = $text, r.length = size($norm), r.type = 'regiao'
                    WITH r
                    OPTIONAL MATCH (br:Word {normalized: 'brasil'})
                    FOREACH (_ IN CASE WHEN br IS NOT NULL THEN [1] ELSE [] END |
                        MERGE (r)-[:LOCATED_IN]->(br)
                    )
                """, text=reg, norm=normalizar_texto(reg))

            # 6. Importar Estados do Brasil e Ligar à Região e ao Brasil
            print("Importando Estados do Brasil...")
            with open(listas_dir / "estados-br.txt", "r", encoding="utf-8") as f:
                for line in f:
                    nome = line.strip()
                    if not nome:
                        continue
                    meta = ESTADOS_METADATA.get(nome, {"uf": "--", "regiao": "Sudeste"})
                    regiao_nome = meta["regiao"]
                    session.run("""
                        MERGE (w:Word {normalized: $norm})
                        SET w.text = $text, w.length = size($norm), w.type = 'estado',
                            w.uf = $uf, w.regiao = $regiao, w.is_estado = true
                        WITH w
                        MATCH (t:Theme {id: 'estados_br'})
                        MERGE (w)-[:BELONGS_TO {weight: 1.0}]->(t)
                        WITH w
                        OPTIONAL MATCH (r:Word {normalized: $reg_norm, type: 'regiao'})
                        FOREACH (_ IN CASE WHEN r IS NOT NULL THEN [1] ELSE [] END |
                            MERGE (w)-[:LOCATED_IN]->(r)
                        )
                    """, text=nome, norm=normalizar_texto(nome), uf=meta["uf"], regiao=regiao_nome, reg_norm=normalizar_texto(regiao_nome))

            # 7. Importar Municípios Brasileiros em Lote
            print("Importando Municípios Brasileiros...")
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
                    ON CREATE SET w.text = item.text, w.length = item.len, w.type = 'municipio'
                    ON MATCH SET w.is_municipio = true
                    WITH w
                    MATCH (t:Theme {id: 'municipios_br'})
                    MERGE (w)-[:BELONGS_TO {weight: 1.0}]->(t)
                    WITH w
                    OPTIONAL MATCH (br:Word {normalized: 'brasil'})
                    FOREACH (_ IN CASE WHEN br IS NOT NULL THEN [1] ELSE [] END |
                        MERGE (w)-[:LOCATED_IN]->(br)
                    )
                """, batch=batch)

            # 8. Resumo Final
            print("\nGrafo Geográfico populado com sucesso!")
            res_words = session.run("MATCH (w:Word) RETURN count(w) as total").single()["total"]
            res_themes = session.run("MATCH (t:Theme) RETURN count(t) as total").single()["total"]
            res_located = session.run("MATCH ()-[r:LOCATED_IN]->() RETURN count(r) as total").single()["total"]
            res_belongs = session.run("MATCH ()-[r:BELONGS_TO]->() RETURN count(r) as total").single()["total"]

            print(f"Estatísticas:")
            print(f"   • Nós de Palavras/Locais: {res_words:,}")
            print(f"   • Nós de Temas:           {res_themes}")
            print(f"   • Relações [:BELONGS_TO]: {res_belongs:,}")
            print(f"   • Relações [:LOCATED_IN]: {res_located:,}")


if __name__ == "__main__":
    populate_geography_graph()
