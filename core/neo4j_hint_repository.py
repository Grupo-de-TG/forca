"""
Implementação do repositório de dicas usando Neo4j Graph Database.
Executa consultas e travessias no grafo (ex: [:LOCATED_IN], [:BELONGS_TO])
para construir pistas progressivas em linguagem natural e fluida.
"""

from __future__ import annotations
import os
from typing import List, Optional
from neo4j import GraphDatabase, Driver

from interfaces.hint_repository import IHintRepository


class Neo4jHintRepository(IHintRepository):
    """Provedor de dicas contextuais baseado no Grafo de Conhecimento do Neo4j."""

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None
    ):
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASS", "forcasecret")
        self._driver: Optional[Driver] = None

    def _get_driver(self) -> Driver:
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                notifications_min_severity="OFF"
            )
        return self._driver

    def is_available(self) -> bool:
        try:
            driver = self._get_driver()
            driver.verify_connectivity()
            return True
        except Exception:
            return False

    def close(self) -> None:
        if self._driver:
            self._driver.close()
            self._driver = None

    def get_hints(self, word_normalized: str, theme_name: Optional[str] = None) -> List[str]:
        """
        Gera uma lista progressiva de dicas em linguagem natural,
        navegando pelos nós e relacionamentos do grafo geográfico.
        """
        if not self.is_available():
            return self._fallback_hints(word_normalized, theme_name)

        hints: List[str] = []
        try:
            with self._get_driver().session() as session:
                query = """
                MATCH (w:Word {normalized: $norm})
                OPTIONAL MATCH (w)-[:BELONGS_TO]->(t:Theme)
                OPTIONAL MATCH path = (w)-[:LOCATED_IN*1..4]->(ancestor:Word)
                OPTIONAL MATCH (child:Word)-[:LOCATED_IN]->(w)
                RETURN w.text AS text,
                       w.type AS tipo,
                       w.uf AS uf,
                       w.regiao AS regiao,
                       w.continente AS continente,
                       w.is_estado AS is_estado,
                       w.is_municipio AS is_municipio,
                       w.length AS length,
                       t.name AS theme_name,
                       [a IN collect(DISTINCT ancestor.text) WHERE a IS NOT NULL] AS ancestrais,
                       [c IN collect(DISTINCT child.text) WHERE c IS NOT NULL][0..3] AS filhos_amostra,
                       count(DISTINCT child) AS total_filhos
                LIMIT 1
                """
                result = session.run(query, norm=word_normalized).single()

                if not result or result["text"] is None:
                    return self._fallback_hints(word_normalized, theme_name)

                text = result["text"]
                tipo = result["tipo"]
                uf = result["uf"]
                regiao = result["regiao"]
                continente = result["continente"]
                is_estado = bool(result["is_estado"])
                length = result["length"] or len(word_normalized)
                ancestrais = result["ancestrais"] or []
                filhos = result["filhos_amostra"] or []
                theme_clean = (theme_name or "").lower()

                # 1. TEMA MUNICÍPIOS (ou tipo município)
                if ("municip" in theme_clean) or (tipo == "municipio" and "estado" not in theme_clean and not is_estado):
                    hints.append("É uma cidade do Brasil")
                    if uf and uf != "--":
                        hints.append(f"Fica no estado com a sigla {uf}")
                    if regiao:
                        hints.append(f"Fica localizada na região {regiao}")
                    hints.append("Fica no continente América")
                    hints.append(f"A palavra possui {length} letras")
                    hints.append(f"Começa com a letra '{text[0].upper()}'")

                # 2. TEMA ESTADOS (ou nó de estado)
                elif ("estado" in theme_clean) or is_estado or tipo == "estado":
                    uf_str = f" com a sigla {uf}" if uf and uf != "--" else ""
                    hints.append(f"É um estado do Brasil{uf_str}")
                    if regiao:
                        hints.append(f"Fica localizado na região {regiao}")
                    hints.append("Fica no continente América")
                    hints.append(f"A palavra possui {length} letras")
                    hints.append(f"Começa com a letra '{text[0].upper()}'")

                # 3. TEMA PAÍSES
                elif ("pais" in theme_clean) or tipo == "pais":
                    hints.append("É um país do mundo")
                    cont_alvo = continente or (ancestrais[0] if ancestrais else "América")
                    hints.append(f"Fica situado no continente {cont_alvo}")
                    hints.append(f"A palavra possui {length} letras")
                    hints.append(f"Começa com a letra '{text[0].upper()}'")

                # 4. TEMA CONTINENTES
                elif ("continente" in theme_clean) or tipo == "continente":
                    hints.append("É um continente do planeta Terra")
                    if filhos:
                        hints.append(f"Abrange países como {', '.join(filhos)}")
                    hints.append(f"A palavra possui {length} letras")
                    hints.append(f"Começa com a letra '{text[0].upper()}'")

                # 5. REGIÃO
                elif tipo == "regiao":
                    hints.append("É uma das 5 grandes regiões geográficas do Brasil")
                    hints.append("Agrupa vários estados no território nacional")
                    hints.append(f"A palavra possui {length} letras")
                    hints.append(f"Começa com a letra '{text[0].upper()}'")

                # 6. CONJUGAÇÃO VERBAL / GERAL
                else:
                    return self._fallback_hints(word_normalized, theme_name)

        except Exception:
            return self._fallback_hints(word_normalized, theme_name)

        return hints if hints else self._fallback_hints(word_normalized, theme_name)

    def _fallback_hints(self, word_normalized: str, theme_name: Optional[str] = None) -> List[str]:
        length = len(word_normalized)
        hints: List[str] = []
        theme_clean = (theme_name or "").lower()

        if "conjug" in theme_clean:
            hints.append("É uma conjugação verbal da língua portuguesa")
        elif theme_name:
            hints.append(f"Pertence ao grupo de {theme_name}")

        hints.append(f"A palavra possui {length} letras.")
        if length > 0:
            hints.append(f"Começa com a letra '{word_normalized[0].upper()}'.")
        return hints
