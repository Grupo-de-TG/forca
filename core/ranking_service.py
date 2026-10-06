"""
Serviço de Gerenciamento de Jogadores e Ranking com persistência JSON.
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import json
from typing import List, Optional, Dict


@dataclass
class Player:
    name: str
    score: int = 0
    games_played: int = 0
    games_won: int = 0
    current_streak: int = 0
    best_streak: int = 0

    @property
    def win_rate(self) -> float:
        if self.games_played == 0:
            return 0.0
        return (self.games_won / self.games_played) * 100.0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Player:
        return cls(
            name=data.get("name", "Anônimo"),
            score=data.get("score", 0),
            games_played=data.get("games_played", 0),
            games_won=data.get("games_won", 0),
            current_streak=data.get("current_streak", 0),
            best_streak=data.get("best_streak", 0),
        )


class RankingService:
    """Gerencia leitura, escrita e pontuação de jogadores."""

    def __init__(self, data_file: Path | None = None):
        if data_file is None:
            self.data_file = Path(__file__).parent.parent / "data" / "ranking.json"
        else:
            self.data_file = data_file
        self._ensure_storage()

    def _ensure_storage(self) -> None:
        if not self.data_file.parent.exists():
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.data_file.exists():
            self.data_file.write_text("{}", encoding="utf-8")

    def _load_data(self) -> Dict[str, dict]:
        try:
            content = self.data_file.read_text(encoding="utf-8")
            return json.loads(content) if content.strip() else {}
        except Exception:
            return {}

    def _save_data(self, data: Dict[str, dict]) -> None:
        self.data_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def get_all_players(self) -> List[Player]:
        data = self._load_data()
        players = [Player.from_dict(p_data) for p_data in data.values()]
        # Ordena por maior pontuação, depois mais vitórias, depois melhor streak
        players.sort(key=lambda p: (p.score, p.games_won, p.best_streak), reverse=True)
        return players

    def get_player(self, name: str) -> Optional[Player]:
        clean_name = name.strip()
        data = self._load_data()
        key = clean_name.lower()
        if key in data:
            return Player.from_dict(data[key])
        return None

    def get_or_create_player(self, name: str) -> Player:
        clean_name = name.strip() or "Jogador"
        data = self._load_data()
        key = clean_name.lower()

        if key in data:
            return Player.from_dict(data[key])

        new_player = Player(name=clean_name)
        data[key] = new_player.to_dict()
        self._save_data(data)
        return new_player

    def record_game_result(self, player_name: str, won: bool, attempts_left: int = 0) -> tuple[Player, int]:
        """
        Registra o resultado da partida para o jogador.
        Retorna a instância do Player atualizada e a pontuação obtida na partida.
        """
        player = self.get_or_create_player(player_name)
        player.games_played += 1

        points_earned = 0
        if won:
            player.games_won += 1
            player.current_streak += 1
            if player.current_streak > player.best_streak:
                player.best_streak = player.current_streak

            # Cálculo de pontuação: 100 base + 20 por vida restante + bônus de sequência
            streak_bonus = min(player.current_streak * 10, 100)
            points_earned = 100 + (attempts_left * 20) + streak_bonus
            player.score += points_earned
        else:
            player.current_streak = 0
            # Pontos de consolo mínimos por participação
            points_earned = 10
            player.score += points_earned

        data = self._load_data()
        data[player.name.lower()] = player.to_dict()
        self._save_data(data)

        return player, points_earned
