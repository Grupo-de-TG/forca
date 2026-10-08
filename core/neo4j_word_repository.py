"""
Implementação do repositório de palavras utilizando o Neo4j Graph Database.
Retorna as categorias jogáveis e sorteia palavras por tema especificado.
"""

from __future__ import annotations
from typing import List, Optional
from neo4j import GraphDatabase, Driver

from interfaces.word_repository import IWordRepository
from core.models import Categoria, WordData


class Neo4jWordRepository(IWordRepository):
    """Repositório de palavras conectado ao grafo Neo4j via Cypher."""

    def __init__(self, uri: str = "bolt://localhost:7687", auth: tuple = ("neo4j", "forcasecret")):
        self.uri = uri
        self.auth = auth
        self._driver: Optional[Driver] = None

    def _get_driver(self) -> Driver:
        if self._driver is None:
            self._driver = GraphDatabase.driver(self.uri, auth=self.auth)
        return self._driver

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def is_available(self) -> bool:
        """Verifica se o container Neo4j está acessível."""
        try:
            driver = self._get_driver()
            driver.verify_connectivity()
            return True
        except Exception:
            return False

    def list_themes(self) -> List[Categoria]:
        """Consulta todos os temas que possuem palavras associadas diretamente no grafo."""
        query = """
        MATCH (t:Theme)<-[:BELONGS_TO]-(w:Word)
        RETURN t.id AS id, t.name AS name, coalesce(t.group, 'Geral') AS group, count(w) AS total_words
        ORDER BY t.name
        """
        categorias = []
        try:
            with self._get_driver().session() as session:
                result = session.run(query)
                for record in result:
                    categorias.append(Categoria(
                        id=record["id"],
                        nome=record["name"],
                        group=record["group"],
                        total_palavras=record["total_words"]
                    ))
        except Exception:
            return []
        return categorias

    def get_random_word(
        self, 
        theme_id: Optional[str] = None, 
        exclude_words: Optional[List[str]] = None
    ) -> Optional[WordData]:
        """
        Sorteia uma palavra do grafo Neo4j para o tema selecionado.
        """
        exclude = exclude_words or []

        # Se theme_id foi informado, busca dentro do tema; caso contrário, seleciona de qualquer tema com palavras
        query = """
        MATCH (w:Word)-[:BELONGS_TO]->(t:Theme)
        WHERE ($theme_id IS NULL OR t.id = $theme_id)
          AND NOT w.normalized IN $exclude
        WITH collect({
            text: w.text,
            normalized: w.normalized,
            theme_id: t.id,
            theme_name: t.name
        }) AS pool
        WHERE size(pool) > 0
        RETURN pool[toInteger(rand() * size(pool))] AS selecionada
        """

        try:
            with self._get_driver().session() as session:
                result = session.run(query, theme_id=theme_id, exclude=exclude).single()

                if not result or not result["selecionada"]:
                    return None

                data = result["selecionada"]
                return WordData(
                    text=data["text"],
                    normalized=data["normalized"],
                    theme_id=data["theme_id"],
                    theme_name=data["theme_name"],
                )
        except Exception:
            return None
