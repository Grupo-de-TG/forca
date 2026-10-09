"""
Contrato de Repositório de Dicas.
Permite consultar pistas e dicas contextuais a partir de um banco/grafo de conhecimento.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List


class IHintRepository(ABC):
    """Interface abstrata para provedores de dicas do jogo."""

    @abstractmethod
    def get_hints(self, word_normalized: str) -> List[str]:
        """
        Retorna uma lista ordenada de dicas contextuais (da mais genérica para a mais específica)
        para a palavra normalizada informada.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Verifica se o backend de dicas está disponível."""
        pass
