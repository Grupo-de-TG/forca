"""Carga automática e limitada do dicionário de palavras no MongoDB.

A cada inicialização, verifica o hash dos arquivos locais. Arquivos inalterados
não são importados novamente. Por padrão, mantém até 500 palavras distintas
por categoria, selecionadas de forma determinística para que o conjunto seja
reproduzível entre execuções.

Somente documentos gerenciados por este importador (origem_seed='listas')
podem ser substituídos quando um arquivo de origem mudar ou o limite mudar.
Documentos cadastrados manualmente são preservados.
"""

from __future__ import annotations

import hashlib
import os
import random
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pymongo import UpdateOne
from pymongo.collection import Collection

from core.normalizer import normalizar_texto

SEED_ORIGIN = "listas"
SEED_STATE_COLLECTION = "_dictionary_seed_state"
DEFAULT_MAX_PER_CATEGORY = 500
BATCH_SIZE = 500


def _decodificar_escape_unicode(texto: str) -> str:
    """Decodifica nomes de arquivo serializados no formato #Uhhhh."""
    return re.sub(
        r"#U([0-9a-fA-F]{4})",
        lambda match: chr(int(match.group(1), 16)),
        texto,
    )


def nome_categoria(arquivo: Path) -> str:
    """Converte o nome do arquivo em categoria, tolerando escapes #Uhhhh."""
    stem = _decodificar_escape_unicode(arquivo.stem)
    return stem.replace("-", " ").replace("_", " ").title()



def _checksum(arquivo: Path) -> str:
    digest = hashlib.sha256()
    with arquivo.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _ler_palavras_unicas(arquivo: Path) -> dict[str, str]:
    """Retém a primeira grafia de cada palavra normalizada do arquivo."""
    unicas: dict[str, str] = {}
    with arquivo.open("r", encoding="utf-8", errors="ignore") as source:
        for linha in source:
            palavra = linha.strip()
            normalizada = normalizar_texto(palavra) if palavra else ""
            if normalizada and normalizada not in unicas:
                unicas[normalizada] = palavra
    return unicas


def _selecionar_palavras(
    unicas: dict[str, str],
    limite: int,
    checksum: str,
) -> list[tuple[str, str]]:
    """Seleciona até N palavras com amostra estável para o arquivo."""
    chaves = list(unicas.keys())
    quantidade = min(limite, len(chaves))
    if quantidade == len(chaves):
        escolhidas = chaves
    else:
        rng = random.Random(int(checksum[:16], 16))
        escolhidas = rng.sample(chaves, quantidade)
    return [(normalizada, unicas[normalizada]) for normalizada in escolhidas]


def seed_dictionary(
    collection: Collection,
    listas_dir: Path,
    max_per_category: int | None = None,
) -> dict[str, Any]:
    """Importa automaticamente as listas para MongoDB de forma idempotente.

    Args:
        collection: coleção MongoDB `dicionario`.
        listas_dir: diretório que contém os arquivos `.txt`.
        max_per_category: máximo de palavras distintas por lista. Por padrão,
            usa `DICIONARIO_MAX_POR_CATEGORIA` ou 500.

    Returns:
        Resumo do número de categorias atualizadas e ignoradas.
    """
    if max_per_category is None:
        max_per_category = int(
            os.getenv(
                "DICIONARIO_MAX_POR_CATEGORIA",
                str(DEFAULT_MAX_PER_CATEGORY),
            )
        )
    if max_per_category < 1:
        raise ValueError("O limite de palavras por categoria deve ser positivo.")

    listas_dir = Path(listas_dir)
    if not listas_dir.is_dir():
        raise FileNotFoundError(f"Pasta de listas não encontrada: {listas_dir}")

    arquivos = sorted(listas_dir.rglob("*.txt"))
    if not arquivos:
        raise RuntimeError(f"Nenhum arquivo .txt encontrado em {listas_dir}")

    state_collection = collection.database[SEED_STATE_COLLECTION]

    # Remove documentos de categorias que foram removidas da pasta listas/
    current_categories = {nome_categoria(arquivo) for arquivo in arquivos}
    seeded_categories = state_collection.distinct("_id")
    for old_category in set(seeded_categories) - current_categories:
        collection.delete_many(
            {"categoria": old_category, "origem_seed": SEED_ORIGIN}
        )
        state_collection.delete_one({"_id": old_category})

    # Purga explícita de conjugações caso ainda existam no MongoDB
    collection.delete_many(
        {"categoria": {"$regex": "^conjug", "$options": "i"}, "origem_seed": SEED_ORIGIN}
    )

    # Índice único por categoria + palavra normalizada. Se já existir com as
    # mesmas chaves/opções, MongoDB mantém o índice existente.
    collection.create_index(
        [("categoria", 1), ("palavra_normalizada", 1)],
        unique=True,
        partialFilterExpression={"palavra_normalizada": {"$type": "string"}},
        name="uq_categoria_palavra_normalizada",
    )

    atualizadas = 0
    ignoradas = 0
    totais: dict[str, int] = {}

    print(f"Arquivos encontrados: {len(arquivos)}")

    for arquivo in arquivos:
        categoria = nome_categoria(arquivo)
        checksum = _checksum(arquivo)
        estado = state_collection.find_one({"_id": categoria})
        gerenciadas_agora = collection.count_documents(
            {"categoria": categoria, "origem_seed": SEED_ORIGIN}
        )

        if (
            estado is not None
            and estado.get("checksum") == checksum
            and estado.get("limite") == max_per_category
            and estado.get("documentos_gerenciados", -1) == gerenciadas_agora
        ):
            totais[categoria] = collection.count_documents(
                {"categoria": categoria, "palavra": {"$type": "string"}}
            )
            ignoradas += 1
            print(f"{categoria}: já atualizada ({totais[categoria]} documentos).")
            continue

        unicas = _ler_palavras_unicas(arquivo)
        selecionadas = _selecionar_palavras(
            unicas,
            max_per_category,
            checksum,
        )

        # Remove apenas os documentos que foram gerados pelo seed anterior
        # para essa categoria; preserva palavras cadastradas manualmente.
        collection.delete_many(
            {"categoria": categoria, "origem_seed": SEED_ORIGIN}
        )

        operacoes = []
        agora = datetime.now(timezone.utc)
        novas_candidatas = 0
        for normalizada, palavra in selecionadas:
            documento = {
                "palavra": palavra,
                "palavra_normalizada": normalizada,
                "tamanho": len(palavra),
                "categoria": categoria,
                "dicas": [],
                "ativo": True,
                "origem_seed": SEED_ORIGIN,
                "arquivo_origem": arquivo.name,
                "data_cadastro": agora,
            }
            operacoes.append(
                UpdateOne(
                    {
                        "categoria": categoria,
                        "palavra_normalizada": normalizada,
                    },
                    {"$setOnInsert": documento},
                    upsert=True,
                )
            )
            if len(operacoes) >= BATCH_SIZE:
                resultado = collection.bulk_write(operacoes, ordered=False)
                novas_candidatas += resultado.upserted_count
                operacoes.clear()

        if operacoes:
            resultado = collection.bulk_write(operacoes, ordered=False)
            novas_candidatas += resultado.upserted_count

        gerenciadas_final = collection.count_documents(
            {"categoria": categoria, "origem_seed": SEED_ORIGIN}
        )
        state_collection.update_one(
            {"_id": categoria},
            {
                "$set": {
                    "checksum": checksum,
                    "limite": max_per_category,
                    "palavras_unicas_na_origem": len(unicas),
                    "palavras_selecionadas": len(selecionadas),
                    "documentos_gerenciados": gerenciadas_final,
                    "atualizado_em": datetime.now(timezone.utc),
                }
            },
            upsert=True,
        )

        totais[categoria] = collection.count_documents(
            {"categoria": categoria, "palavra": {"$type": "string"}}
        )
        atualizadas += 1
        print(
            f"{categoria}: origem={len(unicas)} palavras únicas, "
            f"limite={max_per_category}, seed gerenciado={gerenciadas_final}, "
            f"total na coleção={totais[categoria]}."
        )

    print(
        f"Dicionário verificado: {atualizadas} categoria(s) importada(s)/atualizada(s), "
        f"{ignoradas} sem alterações."
    )
    return {
        "arquivos": len(arquivos),
        "atualizadas": atualizadas,
        "ignoradas": ignoradas,
        "totais_por_categoria": totais,
    }
