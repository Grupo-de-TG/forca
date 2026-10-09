"""
Implementação do repositório de dicas usando Neo4j Graph Database.
Executa consultas e travessias no grafo (ex: [:LOCATED_IN], [:BELONGS_TO])
para construir pistas progressivas em tempo real.
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

    def get_hints(self, word_normalized: str) -> List[str]:
        """
        Gera uma lista progressiva de dicas navegando pelos nós e relacionamentos do grafo.
        """
        if not self.is_available():
            return self._fallback_hints(word_normalized)

        hints: List[str] = []
        try:
            with self._get_driver().session() as session:
                query = """
                MATCH (w:Word {normalized: $norm})
                OPTIONAL MATCH (w)-[:BELONGS_TO]->(t:Theme)
                OPTIONAL MATCH path = (w)-[:LOCATED_IN*1..3]->(ancestor:Word)
                OPTIONAL MATCH (child:Word)-[:LOCATED_IN]->(w)
                RETURN w.text AS text,
                       w.type AS tipo,
                       w.uf AS uf,
                       w.regiao AS regiao,
                       w.length AS length,
                       t.name AS theme_name,
                       [a IN collect(DISTINCT ancestor.text) WHERE a IS NOT NULL] AS ancestrais,
                       [c IN collect(DISTINCT child.text) WHERE c IS NOT NULL][0..3] AS filhos_amostra,
                       count(DISTINCT child) AS total_filhos
                LIMIT 1
                """
                result = session.run(query, norm=word_normalized).single()

                if not result or result["text"] is None:
                    return self._fallback_hints(word_normalized)

                text = result["text"]
                tipo = result["tipo"]
                uf = result["uf"]
                regiao = result["regiao"]
                length = result["length"] or len(word_normalized)
                theme_name = result["theme_name"]
                ancestrais = result["ancestrais"] or []
                filhos = result["filhos_amostra"] or []
                total_filhos = result["total_filhos"] or 0

                # Dica 1: Classificação no Grafo
                if tipo == "municipio":
                    hints.append("Classificação: Município Brasileiro")
                elif tipo == "estado":
                    hints.append("Classificação: Unidade Federativa / Estado do Brasil")
                elif tipo == "pais":
                    hints.append("Classificação: País do mundo")
                elif tipo == "continente":
                    hints.append("Classificação: Continente da Terra")
                elif theme_name:
                    hints.append(f"Categoria no Grafo: {theme_name}")

                # Dica 2: Relacionamentos diretos / Metadados Geográficos
                if uf and regiao:
                    hints.append(f"Região: {regiao} (Sigla: {uf})")
                elif ancestrais:
                    hints.append(f"Localização: Situado em {ancestrais[0]}")
                elif tipo == "continente" and filhos:
                    hints.append(f"Abrange países como: {', '.join(filhos)}")

                # Dica 3: Ancestrais em saltos maiores (N-hops) ou Conexões descendentes
                if len(ancestrais) > 1:
                    hints.append(f"Continente / Bloco: {ancestrais[-1]}")
                elif total_filhos > 3:
                    hints.append(f"Possui {total_filhos} localidades subordinadas no mapa")

                # Dica 4: Característica morfológica
                hints.append(f"Estrutura: A palavra possui {length} letras")

                # Dica 5: Pista de letra inicial
                if text:
                    hints.append(f"Pista: A primeira letra é '{text[0].upper()}'")

        except Exception as e:
            return self._fallback_hints(word_normalized)

        return hints if hints else self._fallback_hints(word_normalized)

    def _fallback_hints(self, word_normalized: str) -> List[str]:
        length = len(word_normalized)
        hints = [
            f"Estrutura: Palavra com {length} letras.",
        ]
        if length > 0:
            hints.append(f"Pista: Começa com a letra '{word_normalized[0].upper()}'.")
        return hints
