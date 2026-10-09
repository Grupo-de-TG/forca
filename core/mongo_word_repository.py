"""
Implementação do repositório de palavras utilizando MongoDB (Document Database).
Consome a coleção 'dicionario' para listagem de categorias e sorteio por agregação com $sample.
"""

from __future__ import annotations
import os
from typing import List, Optional
from pymongo import MongoClient
from pymongo.collection import Collection

from interfaces.word_repository import IWordRepository
from core.models import Categoria, WordData
from core.normalizer import normalizar_texto


class MongoWordRepository(IWordRepository):
    """Repositório de vocabulário e categorias baseado no MongoDB."""

    def __init__(
        self,
        mongo_uri: Optional[str] = None,
        database_name: Optional[str] = None,
        collection_name: str = "dicionario"
    ):
        self.mongo_uri = mongo_uri or os.getenv("MONGO_URI", "mongodb://localhost:27017/")
        self.database_name = database_name or os.getenv("MONGO_DATABASE", "forca_db")
        self.collection_name = collection_name
        self._client: Optional[MongoClient] = None

    def _get_client(self) -> MongoClient:
        if self._client is None:
            self._client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=3000)
        return self._client

    def _get_collection(self) -> Collection:
        return self._get_client()[self.database_name][self.collection_name]

    def is_available(self) -> bool:
        try:
            client = self._get_client()
            client.admin.command("ping")
            return True
        except Exception:
            return False

    def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None

    def list_themes(self) -> List[Categoria]:
        """Agrupa palavras ativas por categoria no MongoDB."""
        if not self.is_available():
            return []

        try:
            pipeline = [
                {
                    "$match": {
                        "palavra": {"$type": "string", "$ne": ""},
                        "categoria": {"$type": "string", "$ne": ""},
                        "ativo": {"$ne": False},
                    }
                },
                {
                    "$group": {
                        "_id": "$categoria",
                        "total_palavras": {"$sum": 1},
                    }
                },
                {"$sort": {"_id": 1}},
            ]
            resultado = list(self._get_collection().aggregate(pipeline))
            categorias: List[Categoria] = []
            for item in resultado:
                cat_nome = str(item["_id"])
                categorias.append(
                    Categoria(
                        id=cat_nome,
                        nome=cat_nome,
                        total_palavras=int(item["total_palavras"]),
                        group="Geral",
                    )
                )
            return categorias
        except Exception:
            return []

    def get_random_word(
        self,
        theme_id: Optional[str] = None,
        exclude_words: Optional[List[str]] = None
    ) -> Optional[WordData]:
        """Sorteia uma palavra aleatória no MongoDB usando $sample."""
        if not self.is_available():
            return None

        filtro: dict = {
            "palavra": {"$type": "string", "$ne": ""},
            "categoria": {"$type": "string", "$ne": ""},
            "ativo": {"$ne": False},
        }
        if theme_id:
            filtro["categoria"] = theme_id

        if exclude_words:
            filtro["palavra_normalizada"] = {"$nin": exclude_words}

        try:
            pipeline = [
                {"$match": filtro},
                {"$sample": {"size": 1}},
            ]
            docs = list(self._get_collection().aggregate(pipeline))
            if not docs:
                return None

            doc = docs[0]
            palavra_original = str(doc["palavra"]).strip()
            categoria_nome = str(doc["categoria"]).strip()
            palavra_normalizada = str(doc.get("palavra_normalizada") or normalizar_texto(palavra_original))

            return WordData(
                text=palavra_original,
                normalized=palavra_normalizada,
                theme_id=categoria_nome,
                theme_name=categoria_nome,
            )
        except Exception:
            return None
