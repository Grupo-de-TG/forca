"""Executa manualmente o carregamento limitado do dicionário no MongoDB.

Uso:
    python seed_dicionario.py
"""

from __future__ import annotations
import os
from pathlib import Path
from pymongo import MongoClient

from core.dictionary_seed import seed_dictionary


def main() -> None:
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    database_name = os.getenv("MONGO_DATABASE", "forca_db")
    max_per_category = int(os.getenv("DICIONARIO_MAX_POR_CATEGORIA", "500"))

    print(f"🍃 Conectando ao MongoDB em {mongo_uri}...")
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    try:
        client.admin.command("ping")
        database = client[database_name]
        listas_dir = Path(__file__).resolve().parent / "listas"
        print(f"📊 Populando dicionário a partir de {listas_dir} (máx {max_per_category} palavras/categoria)...")
        resumo = seed_dictionary(
            database["dicionario"],
            listas_dir,
            max_per_category=max_per_category,
        )
        print("✅ Carga do dicionário concluída:", resumo)
    finally:
        client.close()


if __name__ == "__main__":
    main()
