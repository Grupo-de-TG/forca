"""
Implementação do repositório de palavras baseado em arquivos .txt locais (Contingência/Offline).
"""

from __future__ import annotations
from pathlib import Path
import random
from typing import List, Optional, Dict

from interfaces.word_repository import IWordRepository
from core.models import Categoria, WordData
from core.normalizer import normalizar_texto


class FileWordRepository(IWordRepository):
    """Repositório de palavras que lê diretamente dos arquivos em listas/*.txt."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.listas_dir = project_root / "listas"
        self._cache_palavras: Dict[str, List[str]] = {}

    def list_themes(self) -> List[Categoria]:
        categorias = []
        if not self.listas_dir.exists():
            return categorias

        for txt_path in sorted(self.listas_dir.glob("*.txt")):
            theme_id = txt_path.stem
            theme_name = theme_id.replace("-", " ").replace("_", " ").title()
            
            # Contagem de palavras no arquivo
            try:
                with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
                    total = sum(1 for line in f if line.strip())
            except Exception:
                total = 0

            categorias.append(Categoria(
                id=theme_id,
                nome=theme_name,
                arquivo_path=txt_path,
                total_palavras=total,
            ))
        return categorias

    def _get_words_for_file(self, file_path: Path) -> List[str]:
        cache_key = str(file_path)
        if cache_key not in self._cache_palavras:
            palavras = []
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        termo = line.strip()
                        if termo:
                            palavras.append(termo)
            except Exception:
                pass
            self._cache_palavras[cache_key] = palavras
        return self._cache_palavras[cache_key]

    def get_random_word(
        self, 
        theme_id: Optional[str] = None, 
        exclude_words: Optional[List[str]] = None
    ) -> Optional[WordData]:
        themes = self.list_themes()
        if not themes:
            return None

        exclude = set(exclude_words or [])

        # Se theme_id foi informado, busca o arquivo correspondente
        target_theme = None
        if theme_id:
            for t in themes:
                if t.id == theme_id or t.nome.lower() == theme_id.lower():
                    target_theme = t
                    break

        # Se não especificou ou não encontrou, escolhe um tema aleatório
        if not target_theme:
            target_theme = random.choice(themes)

        if not target_theme.arquivo_path or not target_theme.arquivo_path.exists():
            return None

        todas_palavras = self._get_words_for_file(target_theme.arquivo_path)
        if not todas_palavras:
            return None

        # Filtra palavras excluídas
        candidatas = [
            p for p in todas_palavras 
            if normalizar_texto(p) not in exclude
        ]

        if not candidatas:
            candidatas = todas_palavras  # Fallback caso todas tenham sido excluídas

        escolhida = random.choice(candidatas)
        return WordData(
            text=escolhida,
            normalized=normalizar_texto(escolhida),
            theme_id=target_theme.id,
            theme_name=target_theme.nome,
        )
