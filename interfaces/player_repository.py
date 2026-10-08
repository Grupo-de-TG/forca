"""
Interface do Repositório de Jogadores, Ranking e Histórico (IPlayerRepository).
Contrato desacoplado para persistência de dados de usuários e partidas.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Optional

from core.models import Player


class IPlayerRepository(ABC):
    """Contrato abstrato para persistência e estatísticas de jogadores."""

    @abstractmethod
    def get_all_players(self) -> List[Player]:
        """Retorna todos os jogadores cadastrados ordenados por ranking."""
        ...

    @abstractmethod
    def get_player(self, name: str) -> Optional[Player]:
        """Busca um jogador pelo nome."""
        ...

    @abstractmethod
    def get_or_create_player(self, name: str) -> Player:
        """Obtém um jogador existente ou cria um novo perfil."""
        ...

    @abstractmethod
    def record_game_result(
        self, 
        player_name: str, 
        won: bool, 
        attempts_left: int = 0
    ) -> tuple[Player, int]:
        """Registra o resultado de uma partida e atualiza as estatísticas do jogador."""
        ...
