"""
Interface do Repositório de Palavras e Temas (IWordRepository).
Contrato puro e desacoplado de banco de dados para consulta ao vocabulário.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Optional

from core.models import Categoria, WordData


class IWordRepository(ABC):
    """Contrato abstrato para repositórios de palavras da Forca."""

    @abstractmethod
    def list_themes(self) -> List[Categoria]:
        """Retorna a lista de temas/categorias disponíveis."""
        ...

    @abstractmethod
    def get_random_word(
        self, 
        theme_id: Optional[str] = None, 
        exclude_words: Optional[List[str]] = None
    ) -> Optional[WordData]:
        """Sorteia uma palavra aleatória no tema informado (ou qualquer tema se theme_id for None)."""
        ...
