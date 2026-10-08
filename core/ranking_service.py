"""
Serviço de Gerenciamento de Jogadores e Ranking com persistência JSON e Autenticação.
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import hashlib
import secrets
from typing import List, Optional, Dict, Tuple


def hash_password(password: str, salt: str = "") -> Tuple[str, str]:
    """Gera hash PBKDF2-HMAC-SHA256 seguro com salt."""
    if not salt:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100000,
    ).hex()
    return hashed, salt


def verify_password(password: str, hashed: str, salt: str) -> bool:
    """Verifica se a senha fornecida confere com o hash e salt usando tempo constante."""
    if not hashed or not salt:
        return False
    new_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(new_hash, hashed)


@dataclass
class Player:
    name: str
    password_hash: str = ""
    password_salt: str = ""
    score: int = 0
    games_played: int = 0
    games_won: int = 0
    current_streak: int = 0
    best_streak: int = 0

    @property
    def has_password(self) -> bool:
        return bool(self.password_hash and self.password_salt)

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
            password_hash=data.get("password_hash", ""),
            password_salt=data.get("password_salt", ""),
            score=data.get("score", 0),
            games_played=data.get("games_played", 0),
            games_won=data.get("games_won", 0),
            current_streak=data.get("current_streak", 0),
            best_streak=data.get("best_streak", 0),
        )


class RankingService:
    """Gerencia leitura, escrita, autenticação e pontuação de jogadores."""

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

    def player_exists(self, name: str) -> bool:
        clean_name = name.strip()
        if not clean_name:
            return False
        data = self._load_data()
        return clean_name.lower() in data

    def get_player(self, name: str) -> Optional[Player]:
        clean_name = name.strip()
        data = self._load_data()
        key = clean_name.lower()
        if key in data:
            return Player.from_dict(data[key])
        return None

    def verify_or_register_player(self, name: str, password: str) -> Tuple[bool, str, Optional[Player]]:
        """
        Verifica a senha de um jogador existente ou cadastra um novo jogador com a senha informada.
        Retorna (sucesso, mensagem, player).
        """
        clean_name = name.strip()
        if not clean_name:
            return False, "O nome do jogador não pode ser vazio.", None

        if not password:
            return False, "A senha não pode ser vazia.", None

        data = self._load_data()
        key = clean_name.lower()

        if key in data:
            player = Player.from_dict(data[key])
            if not player.has_password:
                # Perfil herdado sem senha: cadastra a nova senha
                pwd_hash, pwd_salt = hash_password(password)
                player.password_hash = pwd_hash
                player.password_salt = pwd_salt
                data[key] = player.to_dict()
                self._save_data(data)
                return True, f"Senha registrada para o jogador existente '{player.name}'!", player

            # Valida senha existente
            if verify_password(password, player.password_hash, player.password_salt):
                return True, f"Autenticado com sucesso como '{player.name}'!", player
            else:
                return False, f"Senha incorreta para o jogador '{player.name}'.", None

        # Novo jogador
        pwd_hash, pwd_salt = hash_password(password)
        new_player = Player(
            name=clean_name,
            password_hash=pwd_hash,
            password_salt=pwd_salt,
        )
        data[key] = new_player.to_dict()
        self._save_data(data)
        return True, f"Novo jogador '{new_player.name}' cadastrado com sucesso!", new_player

    def reset_password(self, name: str, new_password: str) -> Tuple[bool, str, Optional[Player]]:
        """Redefine a senha de um jogador existente com novo salt e hash."""
        clean_name = name.strip()
        if not clean_name:
            return False, "O nome do jogador não pode ser vazio.", None
        if not new_password:
            return False, "A nova senha não pode ser vazia.", None

        data = self._load_data()
        key = clean_name.lower()
        if key not in data:
            return False, f"Jogador '{clean_name}' não encontrado no ranking.", None

        player = Player.from_dict(data[key])
        pwd_hash, pwd_salt = hash_password(new_password)
        player.password_hash = pwd_hash
        player.password_salt = pwd_salt
        data[key] = player.to_dict()
        self._save_data(data)
        return True, f"Senha do jogador '{player.name}' redefinida com sucesso!", player


    @staticmethod
    def calculate_match_points(won: bool, attempts_left: int = 0, current_streak: int = 0) -> int:
        """Calcula os pontos potenciais de uma partida."""
        if won:
            next_streak = current_streak + 1
            streak_bonus = min(next_streak * 10, 100)
            return 100 + (attempts_left * 20) + streak_bonus
        return 10

    def record_game_for_player(self, player: Player, won: bool, attempts_left: int = 0) -> Tuple[Player, int]:
        """
        Registra o resultado da partida para a instância do Player autenticado.
        """
        player.games_played += 1

        points_earned = 0
        if won:
            player.games_won += 1
            player.current_streak += 1
            if player.current_streak > player.best_streak:
                player.best_streak = player.current_streak

            streak_bonus = min(player.current_streak * 10, 100)
            points_earned = 100 + (attempts_left * 20) + streak_bonus
            player.score += points_earned
        else:
            player.current_streak = 0
            points_earned = 10
            player.score += points_earned

        data = self._load_data()
        data[player.name.lower()] = player.to_dict()
        self._save_data(data)

        return player, points_earned

    def record_game_result(self, player_name: str, won: bool, attempts_left: int = 0) -> tuple[Player, int]:
        """Método de compatibilidade legado."""
        clean_name = player_name.strip() or "Jogador"
        player = self.get_player(clean_name)
        if not player:
            player = Player(name=clean_name)
        return self.record_game_for_player(player, won, attempts_left)

