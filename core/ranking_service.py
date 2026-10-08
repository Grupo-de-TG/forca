"""
Serviço Dedicado de Pontuação, Ranking e Histórico de Partidas (RankingService).
Persistência relacional em SQL das estatísticas acumuladas e partidas individuais.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Tuple

from core.database import DatabaseManager


@dataclass
class Player:
    id: int
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


@dataclass
class MatchRecord:
    id: int
    user_id: int
    username: str
    won: bool
    category_name: str
    word: str
    attempts_left: int
    points_earned: int
    played_at: str


class RankingService:
    """Gerencia regras de pontuação, tabela de classificação e histórico de partidas em SQL."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    @staticmethod
    def calculate_match_points(won: bool, attempts_left: int = 0, current_streak: int = 0) -> int:
        """
        Calcula os pontos obtidos em uma rodada:
        Vitória: 100 base + (20 * vidas restantes) + bônus de sequência (máx 100).
        Derrota: 10 pontos de participação.
        """
        if won:
            next_streak = current_streak + 1
            streak_bonus = min(next_streak * 10, 100)
            return 100 + (attempts_left * 20) + streak_bonus
        return 10

    def get_all_players(self) -> List[Player]:
        """Retorna todos os jogadores ordenados por pontuação, vitórias e streak."""
        with self.db.transaction() as conn:
            cursor = conn.execute("""
                SELECT u.id, u.username, s.score, s.games_played, s.games_won, s.current_streak, s.best_streak
                FROM users u
                INNER JOIN player_stats s ON u.id = s.user_id
                ORDER BY s.score DESC, s.games_won DESC, s.best_streak DESC;
            """)
            players = []
            for row in cursor.fetchall():
                players.append(
                    Player(
                        id=row["id"],
                        name=row["username"],
                        score=row["score"],
                        games_played=row["games_played"],
                        games_won=row["games_won"],
                        current_streak=row["current_streak"],
                        best_streak=row["best_streak"],
                    )
                )
            return players

    def get_player_by_id(self, user_id: int) -> Optional[Player]:
        """Obtém as estatísticas de um jogador por ID de usuário."""
        with self.db.transaction() as conn:
            cursor = conn.execute("""
                SELECT u.id, u.username, s.score, s.games_played, s.games_won, s.current_streak, s.best_streak
                FROM users u
                INNER JOIN player_stats s ON u.id = s.user_id
                WHERE u.id = ?;
            """, (user_id,))
            row = cursor.fetchone()
            if row:
                return Player(
                    id=row["id"],
                    name=row["username"],
                    score=row["score"],
                    games_played=row["games_played"],
                    games_won=row["games_won"],
                    current_streak=row["current_streak"],
                    best_streak=row["best_streak"],
                )
            return None

    def get_player_by_name(self, username: str) -> Optional[Player]:
        """Obtém as estatísticas de um jogador por nome."""
        clean_name = username.strip()
        if not clean_name:
            return None

        with self.db.transaction() as conn:
            cursor = conn.execute("""
                SELECT u.id, u.username, s.score, s.games_played, s.games_won, s.current_streak, s.best_streak
                FROM users u
                INNER JOIN player_stats s ON u.id = s.user_id
                WHERE u.username = ? COLLATE NOCASE;
            """, (clean_name,))
            row = cursor.fetchone()
            if row:
                return Player(
                    id=row["id"],
                    name=row["username"],
                    score=row["score"],
                    games_played=row["games_played"],
                    games_won=row["games_won"],
                    current_streak=row["current_streak"],
                    best_streak=row["best_streak"],
                )
            return None

    def record_match(
        self,
        user_id: int,
        won: bool,
        category_name: str,
        word: str,
        attempts_left: int = 0,
    ) -> Tuple[Player, int]:
        """
        Registra atomicamente a partida no histórico (matches) e atualiza o ranking (player_stats).
        Retorna (Player atualizado, pontos ganhos na rodada).
        """
        with self.db.transaction() as conn:
            # 1. Carrega dados atuais do jogador
            cursor = conn.execute(
                "SELECT score, games_played, games_won, current_streak, best_streak FROM player_stats WHERE user_id = ?;",
                (user_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Estatísticas não encontradas para o user_id {user_id}")

            score = row["score"]
            games_played = row["games_played"] + 1
            games_won = row["games_won"]
            current_streak = row["current_streak"]
            best_streak = row["best_streak"]

            points_earned = self.calculate_match_points(won, attempts_left, current_streak)
            score += points_earned

            if won:
                games_won += 1
                current_streak += 1
                if current_streak > best_streak:
                    best_streak = current_streak
            else:
                current_streak = 0

            # 2. Atualiza tabela agregada player_stats
            conn.execute("""
                UPDATE player_stats
                SET score = ?, games_played = ?, games_won = ?, current_streak = ?, best_streak = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?;
            """, (score, games_played, games_won, current_streak, best_streak, user_id))

            # 3. Insere registro individual no histórico de partidas (matches)
            conn.execute("""
                INSERT INTO matches (user_id, won, category_name, word, attempts_left, points_earned)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (user_id, 1 if won else 0, category_name, word, attempts_left, points_earned))

            # 4. Obtém nome do usuário
            u_cur = conn.execute("SELECT username FROM users WHERE id = ?;", (user_id,))
            u_row = u_cur.fetchone()
            username = u_row["username"] if u_row else "Jogador"

            player = Player(
                id=user_id,
                name=username,
                score=score,
                games_played=games_played,
                games_won=games_won,
                current_streak=current_streak,
                best_streak=best_streak,
            )
            return player, points_earned

    def get_player_match_history(self, user_id: int, limit: int = 20) -> List[MatchRecord]:
        """Obtém o histórico de partidas de um jogador específico."""
        with self.db.transaction() as conn:
            cursor = conn.execute("""
                SELECT m.id, m.user_id, u.username, m.won, m.category_name, m.word, m.attempts_left, m.points_earned, m.played_at
                FROM matches m
                INNER JOIN users u ON m.user_id = u.id
                WHERE m.user_id = ?
                ORDER BY m.id DESC
                LIMIT ?;
            """, (user_id, limit))
            records = []
            for row in cursor.fetchall():
                records.append(
                    MatchRecord(
                        id=row["id"],
                        user_id=row["user_id"],
                        username=row["username"],
                        won=bool(row["won"]),
                        category_name=row["category_name"],
                        word=row["word"],
                        attempts_left=row["attempts_left"],
                        points_earned=row["points_earned"],
                        played_at=str(row["played_at"]),
                    )
                )
            return records

    def get_recent_matches(self, limit: int = 50) -> List[MatchRecord]:
        """Obtém o histórico global recente de todas as partidas."""
        with self.db.transaction() as conn:
            cursor = conn.execute("""
                SELECT m.id, m.user_id, u.username, m.won, m.category_name, m.word, m.attempts_left, m.points_earned, m.played_at
                FROM matches m
                INNER JOIN users u ON m.user_id = u.id
                ORDER BY m.id DESC
                LIMIT ?;
            """, (limit,))
            records = []
            for row in cursor.fetchall():
                records.append(
                    MatchRecord(
                        id=row["id"],
                        user_id=row["user_id"],
                        username=row["username"],
                        won=bool(row["won"]),
                        category_name=row["category_name"],
                        word=row["word"],
                        attempts_left=row["attempts_left"],
                        points_earned=row["points_earned"],
                        played_at=str(row["played_at"]),
                    )
                )
            return records

