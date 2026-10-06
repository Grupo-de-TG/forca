"""
Utilitários de normalização de strings para o Jogo da Forca.
"""

from __future__ import annotations
import unicodedata


def normalizar_texto(texto: str) -> str:
    """Remove acentos, converte para minúsculas e remove quebras de linha."""
    nfkd = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join([c for c in nfkd if not unicodedata.combining(c)])
    return sem_acento.lower().strip()
