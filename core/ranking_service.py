"""
Serviço Dedicado de Pontuação, Ranking e Histórico de Partidas (RankingService).
Persistência relacional em SQL das estatísticas acumuladas e partidas individuais.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Tuple

from core.database import DatabaseManager
from core.models import Player, MatchRecord
from interfaces.player_repository import IPlayerRepository


class RankingService(IPlayerRepository):
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
                SELECT u.id, u.username, s.score, s.partidas, s.vitorias, s.streak_atual, s.best_streak
                FROM users u
                INNER JOIN player_stats s ON u.id = s.user_id
                ORDER BY s.score DESC, s.vitorias DESC, s.best_streak DESC;
            """)
            players = []
            for row in cursor.fetchall():
                players.append(
                    Player(
                        id=row["id"],
                        name=row["username"],
                        score=row["score"],
                        partidas=row["partidas"],
                        vitorias=row["vitorias"],
                        streak_atual=row["streak_atual"],
                        best_streak=row["best_streak"],
                    )
                )
            return players

    def get_player_by_id(self, user_id: int) -> Optional[Player]:
        """Obtém as estatísticas de um jogador por ID de usuário."""
        with self.db.transaction() as conn:
            cursor = conn.execute("""
                SELECT u.id, u.username, s.score, s.partidas, s.vitorias, s.streak_atual, s.best_streak
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
                    partidas=row["partidas"],
                    vitorias=row["vitorias"],
                    streak_atual=row["streak_atual"],
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
                SELECT u.id, u.username, s.score, s.partidas, s.vitorias, s.streak_atual, s.best_streak
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
                    partidas=row["partidas"],
                    vitorias=row["vitorias"],
                    streak_atual=row["streak_atual"],
                    best_streak=row["best_streak"],
                )
            return None
    def get_player(self, name: str) -> Optional[Player]:
        """Alias para get_player_by_name."""
        return self.get_player_by_name(name)

    def get_or_create_player(self, name: str) -> Player:
        """Obtém um jogador existente ou cria um novo perfil e suas estatísticas."""
        clean_name = name.strip() or "Jogador"
        existing = self.get_player_by_name(clean_name)
        if existing:
            return existing

        with self.db.transaction() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO users (username, password) VALUES (?, ?);",
                (clean_name, ""),
            )
            u_cur = conn.execute("SELECT id FROM users WHERE username = ? COLLATE NOCASE;", (clean_name,))
            user_id = u_cur.fetchone()["id"]
            conn.execute(
                "INSERT OR IGNORE INTO player_stats (user_id, score, partidas, vitorias, streak_atual, best_streak) VALUES (?, 0, 0, 0, 0, 0);",
                (user_id,),
            )
            return Player(id=user_id, name=clean_name)

    def record_game_result(
        self,
        player_name: str,
        won: bool,
        attempts_left: int = 0,
        category_name: str = "Geral",
        word: str = "",
    ) -> Tuple[Player, int]:
        """Implementação da interface IPlayerRepository para registrar resultado por nome."""
        player = self.get_or_create_player(player_name)
        return self.record_match(
            user_id=player.id,
            won=won,
            category_name=category_name,
            word=word,
            attempts_left=attempts_left,
        )

    def record_match(
        self,
        user_id: int,
        won: bool,
        category_name: str,
        word: str,
        attempts_left: int = 0,
    ) -> Tuple[Player, int]:
        """
        Registra atomicamente a partida no histórico (partidas) e atualiza o ranking (player_stats).
        Retorna (Player atualizado, pontos ganhos na rodada).
        """
        with self.db.transaction() as conn:
            # 1. Carrega dados atuais do jogador
            cursor = conn.execute(
                "SELECT score, partidas, vitorias, streak_atual, best_streak FROM player_stats WHERE user_id = ?;",
                (user_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Estatísticas não encontradas para o user_id {user_id}")

            score = row["score"]
            partidas = row["partidas"] + 1
            vitorias = row["vitorias"]
            streak_atual = row["streak_atual"]
            best_streak = row["best_streak"]

            points_earned = self.calculate_match_points(won, attempts_left, streak_atual)
            score += points_earned

            if won:
                vitorias += 1
                streak_atual += 1
                if streak_atual > best_streak:
                    best_streak = streak_atual
            else:
                streak_atual = 0

            # 2. Atualiza tabela agregada player_stats
            conn.execute("""
                UPDATE player_stats
                SET score = ?, partidas = ?, vitorias = ?, streak_atual = ?, best_streak = ?, marca_paco = CURRENT_TIMESTAMP
                WHERE user_id = ?;
            """, (score, partidas, vitorias, streak_atual, best_streak, user_id))

            # 3. Insere registro individual no histórico de partidas
            conn.execute("""
                INSERT INTO partidas (user_id, vencidas, categoria, palavra, tentativas_restantes, pontos)
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
                partidas=partidas,
                vitorias=vitorias,
                streak_atual=streak_atual,
                best_streak=best_streak,
            )
            return player, points_earned

    def get_player_match_history(self, user_id: int, limit: int = 20) -> List[MatchRecord]:
        """Obtém o histórico de partidas de um jogador específico."""
        with self.db.transaction() as conn:
            cursor = conn.execute("""
                SELECT p.id, p.user_id, u.username, p.vencidas, p.categoria, p.palavra, p.tentativas_restantes, p.pontos, p.marca_paco
                FROM partidas p
                INNER JOIN users u ON p.user_id = u.id
                WHERE p.user_id = ?
                ORDER BY p.id DESC
                LIMIT ?;
            """, (user_id, limit))
            records = []
            for row in cursor.fetchall():
                records.append(
                    MatchRecord(
                        id=row["id"],
                        user_id=row["user_id"],
                        username=row["username"],
                        vencidas=bool(row["vencidas"]),
                        categoria=row["categoria"],
                        palavra=row["palavra"],
                        tentativas_restantes=row["tentativas_restantes"],
                        pontos=row["pontos"],
                        marca_paco=str(row["marca_paco"]),
                    )
                )
            return records

    def get_recent_matches(self, limit: int = 50) -> List[MatchRecord]:
        """Obtém o histórico global recente de todas as partidas."""
        with self.db.transaction() as conn:
            cursor = conn.execute("""
                SELECT p.id, p.user_id, u.username, p.vencidas, p.categoria, p.palavra, p.tentativas_restantes, p.pontos, p.marca_paco
                FROM partidas p
                INNER JOIN users u ON p.user_id = u.id
                ORDER BY p.id DESC
                LIMIT ?;
            """, (limit,))
            records = []
            for row in cursor.fetchall():
                records.append(
                    MatchRecord(
                        id=row["id"],
                        user_id=row["user_id"],
                        username=row["username"],
                        vencidas=bool(row["vencidas"]),
                        categoria=row["categoria"],
                        palavra=row["palavra"],
                        tentativas_restantes=row["tentativas_restantes"],
                        pontos=row["pontos"],
                        marca_paco=str(row["marca_paco"]),
                    )
                )
            return records
