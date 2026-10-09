"""
Factory para instanciação dinâmica e desacoplada do Repositório de Palavras (IWordRepository).
Permite alternar entre Grafo (Neo4j), Documental (NoSQL) ou Arquivos Locais (.txt).
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Optional

from interfaces.word_repository import IWordRepository
from core.mongo_word_repository import MongoWordRepository
from core.neo4j_word_repository import Neo4jWordRepository
from core.file_word_repository import FileWordRepository


class WordRepositoryFactory:
    """Fábrica para criação de instâncias de IWordRepository baseada em configuração."""

    @staticmethod
    def create(
        backend_type: Optional[str] = None, 
        project_root: Optional[Path] = None
    ) -> IWordRepository:
        if project_root is None:
            project_root = Path(__file__).parent.parent

        tipo = (backend_type or os.getenv("WORD_BACKEND", "mongo")).strip().lower()

        if tipo in ("mongo", "mongodb", "doc", "document", "documento"):
            mongo_repo = MongoWordRepository()
            if mongo_repo.is_available():
                return mongo_repo
            return FileWordRepository(project_root=project_root)

        elif tipo in ("graph", "grapho", "grafo", "neo4j"):
            uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
            user = os.getenv("NEO4J_USER", "neo4j")
            password = os.getenv("NEO4J_PASS", "forcasecret")
            return Neo4jWordRepository(uri=uri, auth=(user, password))

        elif tipo in ("file", "arquivo", "local", "txt"):
            return FileWordRepository(project_root=project_root)

        # Fallback de segurança para arquivo se backend informado for inválido
        return FileWordRepository(project_root=project_root)
