"""
Serviço Dedicado de Pontuação, Ranking e Histórico de Partidas.

MySQL:
    - Estatísticas acumuladas dos jogadores.
    - Ranking.

MongoDB:
    - Histórico detalhado das partidas.

A interface pública do serviço é mantida compatível com as telas
existentes da aplicação.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from core.database import DatabaseManager


@dataclass
class Player:
    """Representa um jogador e suas estatísticas consolidadas."""

    id: int
    name: str
    score: int = 0
    partidas: int = 0
    vitorias: int = 0
    streak_atual: int = 0
    best_streak: int = 0

    @property
    def games_played(self) -> int:
        return self.partidas

    @property
    def games_won(self) -> int:
        return self.vitorias

    @property
    def current_streak(self) -> int:
        return self.streak_atual

    @property
    def win_rate(self) -> float:
        if self.partidas == 0:
            return 0.0

        return (self.vitorias / self.partidas) * 100.0


@dataclass
class MatchRecord:
    """
    Representa uma partida armazenada no MongoDB.

    O MongoDB utiliza ObjectId, portanto o id do histórico é
    representado como string.
    """

    id: str
    user_id: int
    username: str
    vencidas: bool
    categoria: str
    palavra: str
    tentativas_restantes: int
    pontos: int
    marca_paco: str

    @property
    def won(self) -> bool:
        return self.vencidas

    @property
    def category_name(self) -> str:
        return self.categoria

    @property
    def word(self) -> str:
        return self.palavra

    @property
    def attempts_left(self) -> int:
        return self.tentativas_restantes

    @property
    def points_earned(self) -> int:
        return self.pontos

    @property
    def played_at(self) -> str:
        return self.marca_paco


from interfaces.player_repository import IPlayerRepository


class RankingService(IPlayerRepository):
    """
    Gerencia pontuação, ranking e histórico de partidas.

    MySQL:
        users
        player_stats

    MongoDB:
        logs_partidas
    """

    def __init__(self, db: DatabaseManager):
        self.db = db

    # ============================================================
    # CÁLCULO DE PONTOS
    # ============================================================

    @staticmethod
    def calculate_match_points(
        won: bool,
        attempts_left: int = 0,
        current_streak: int = 0,
    ) -> int:
        """
        Calcula os pontos obtidos em uma rodada.

        Vitória:
            100 pontos base
            + 20 pontos por vida restante
            + bônus de sequência (máx. 100)

        Derrota:
            10 pontos de participação.
        """

        if won:
            next_streak = current_streak + 1
            streak_bonus = min(next_streak * 10, 100)

            return 100 + (attempts_left * 20) + streak_bonus

        return 10

    # ============================================================
    # RANKING - MYSQL
    # ============================================================

    def get_all_players(self) -> List[Player]:
        """Retorna todos os jogadores ordenados por desempenho."""

        with self.db.transaction() as conn:
            cursor = conn.execute(
                """
                SELECT
                    u.id,
                    u.username,
                    s.score,
                    s.partidas,
                    s.vitorias,
                    s.streak_atual,
                    s.best_streak
                FROM users u
                INNER JOIN player_stats s
                    ON u.id = s.user_id
                ORDER BY
                    s.score DESC,
                    s.vitorias DESC,
                    s.best_streak DESC;
                """
            )

            players: List[Player] = []

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

    def get_player_by_id(
        self,
        user_id: int,
    ) -> Optional[Player]:
        """Obtém as estatísticas de um jogador por ID."""

        with self.db.transaction() as conn:
            cursor = conn.execute(
                """
                SELECT
                    u.id,
                    u.username,
                    s.score,
                    s.partidas,
                    s.vitorias,
                    s.streak_atual,
                    s.best_streak
                FROM users u
                INNER JOIN player_stats s
                    ON u.id = s.user_id
                WHERE u.id = %s
                LIMIT 1;
                """,
                (user_id,),
            )

            row = cursor.fetchone()

            if not row:
                return None

            return Player(
                id=row["id"],
                name=row["username"],
                score=row["score"],
                partidas=row["partidas"],
                vitorias=row["vitorias"],
                streak_atual=row["streak_atual"],
                best_streak=row["best_streak"],
            )

    def get_player_by_name(
        self,
        username: str,
    ) -> Optional[Player]:
        """Obtém as estatísticas de um jogador por nome."""

        clean_name = username.strip()

        if not clean_name:
            return None

        with self.db.transaction() as conn:
            cursor = conn.execute(
                """
                SELECT
                    u.id,
                    u.username,
                    s.score,
                    s.partidas,
                    s.vitorias,
                    s.streak_atual,
                    s.best_streak
                FROM users u
                INNER JOIN player_stats s
                    ON u.id = s.user_id
                WHERE u.username = %s
                LIMIT 1;
                """,
                (clean_name,),
            )

            row = cursor.fetchone()

            if not row:
                return None

            return Player(
                id=row["id"],
                name=row["username"],
                score=row["score"],
                partidas=row["partidas"],
                vitorias=row["vitorias"],
                streak_atual=row["streak_atual"],
                best_streak=row["best_streak"],
            )

    def get_player(self, name: str) -> Optional[Player]:
        """Implementação da interface IPlayerRepository."""
        return self.get_player_by_name(name)

    def get_or_create_player(self, name: str) -> Player:
        """Implementação da interface IPlayerRepository: obtém ou registra."""
        player = self.get_player_by_name(name)
        if player:
            return player
        # Se não existir, registra no MySQL
        with self.db.transaction() as conn:
            cursor = conn.execute(
                "INSERT INTO users (username, password) VALUES (%s, %s);",
                (name.strip(), "padrao123")
            )
            user_id = cursor.lastrowid
            conn.execute(
                "INSERT INTO player_stats (user_id, score, partidas, vitorias, streak_atual, best_streak) VALUES (%s, 0, 0, 0, 0, 0);",
                (user_id,)
            )
        return self.get_player_by_id(user_id)  # type: ignore

    def record_game_result(
        self,
        player_name: str,
        won: bool,
        attempts_left: int = 0
    ) -> Tuple[Player, int]:
        """Implementação da interface IPlayerRepository."""
        player = self.get_or_create_player(player_name)
        return self.record_match(
            user_id=player.id,
            won=won,
            category_name="Geral",
            word="partida",
            attempts_left=attempts_left
        )

    # ============================================================
    # REGISTRO DE PARTIDA
    # ============================================================

    def record_match(
        self,
        user_id: int,
        won: bool,
        category_name: str,
        word: str,
        attempts_left: int = 0,
    ) -> Tuple[Player, int]:
        """
        Registra uma partida.

        1. Atualiza as estatísticas consolidadas no MySQL.
        2. Grava o evento detalhado da partida no MongoDB.

        Retorna:
            (Player atualizado, pontos ganhos)
        """

        # ========================================================
        # 1. MYSQL - atualização das estatísticas
        # ========================================================

        with self.db.transaction() as conn:

            cursor = conn.execute(
                """
                SELECT
                    score,
                    partidas,
                    vitorias,
                    streak_atual,
                    best_streak
                FROM player_stats
                WHERE user_id = %s
                LIMIT 1;
                """,
                (user_id,),
            )

            row = cursor.fetchone()

            if not row:
                raise ValueError(
                    f"Estatísticas não encontradas "
                    f"para o user_id {user_id}"
                )

            score = row["score"]
            partidas = row["partidas"] + 1
            vitorias = row["vitorias"]
            streak_atual = row["streak_atual"]
            best_streak = row["best_streak"]

            # Mantém exatamente a regra de pontuação original.
            points_earned = self.calculate_match_points(
                won,
                attempts_left,
                streak_atual,
            )

            score += points_earned

            if won:
                vitorias += 1
                streak_atual += 1

                if streak_atual > best_streak:
                    best_streak = streak_atual

            else:
                streak_atual = 0

            # Atualiza somente os dados consolidados no MySQL.
            conn.execute(
                """
                UPDATE player_stats
                SET
                    score = %s,
                    partidas = %s,
                    vitorias = %s,
                    streak_atual = %s,
                    best_streak = %s,
                    marca_paco = CURRENT_TIMESTAMP
                WHERE user_id = %s;
                """,
                (
                    score,
                    partidas,
                    vitorias,
                    streak_atual,
                    best_streak,
                    user_id,
                ),
            )

            # Obtém o nome do jogador.
            user_cursor = conn.execute(
                """
                SELECT username
                FROM users
                WHERE id = %s
                LIMIT 1;
                """,
                (user_id,),
            )

            user_row = user_cursor.fetchone()

            username = (
                user_row["username"]
                if user_row
                else "Jogador"
            )

            player = Player(
                id=user_id,
                name=username,
                score=score,
                partidas=partidas,
                vitorias=vitorias,
                streak_atual=streak_atual,
                best_streak=best_streak,
            )

        # ========================================================
        # 2. MONGODB - histórico da partida
        # ========================================================

        log_partida = {
            "user_id": user_id,
            "username": username,
            "vencidas": bool(won),
            "resultado": (
                "vitoria"
                if won
                else "derrota"
            ),
            "categoria": category_name,
            "palavra": word,
            "palavra_alvo": word,
            "tentativas_restantes": attempts_left,
            "pontos": points_earned,
            "data_partida": datetime.now(timezone.utc),
        }

        self.db.logs_partidas_collection.insert_one(
            log_partida
        )

        return player, points_earned

    # ============================================================
    # HISTÓRICO DO JOGADOR - MONGODB
    # ============================================================

    def get_player_match_history(
        self,
        user_id: int,
        limit: int = 20,
    ) -> List[MatchRecord]:
        """Obtém o histórico de partidas de um jogador."""

        limit = max(1, min(int(limit), 100))

        documents = (
            self.db.logs_partidas_collection
            .find(
                {
                    "user_id": user_id
                }
            )
            .sort(
                [
                    ("data_partida", -1),
                    ("_id", -1),
                ]
            )
            .limit(limit)
        )

        records: List[MatchRecord] = []

        for document in documents:
            records.append(
                self._document_to_match_record(
                    document
                )
            )

        return records

    # ============================================================
    # HISTÓRICO GLOBAL - MONGODB
    # ============================================================

    def get_recent_matches(
        self,
        limit: int = 50,
    ) -> List[MatchRecord]:
        """Obtém o histórico global recente de partidas."""

        limit = max(1, min(int(limit), 100))

        documents = (
            self.db.logs_partidas_collection
            .find({})
            .sort(
                [
                    ("data_partida", -1),
                    ("_id", -1),
                ]
            )
            .limit(limit)
        )

        records: List[MatchRecord] = []

        for document in documents:
            records.append(
                self._document_to_match_record(
                    document
                )
            )

        return records

    # ============================================================
    # CONVERSÃO DO DOCUMENTO MONGODB
    # ============================================================

    @staticmethod
    def _document_to_match_record(
        document: dict,
    ) -> MatchRecord:
        """Converte um documento MongoDB para MatchRecord."""

        data_partida = document.get(
            "data_partida"
        )

        if isinstance(data_partida, datetime):
            marca_paco = data_partida.isoformat()
        elif data_partida is None:
            marca_paco = ""
        else:
            marca_paco = str(data_partida)

        vencidas = document.get("vencidas")

        if vencidas is None:
            vencidas = (
                document.get("resultado")
                == "vitoria"
            )

        categoria = document.get(
            "categoria",
            document.get(
                "category_name",
                "",
            ),
        )

        palavra = document.get(
            "palavra",
            document.get(
                "palavra_alvo",
                "",
            ),
        )

        return MatchRecord(
            id=str(document.get("_id")),
            user_id=int(
                document.get(
                    "user_id",
                    0,
                )
            ),
            username=str(
                document.get(
                    "username",
                    "Jogador",
                )
            ),
            vencidas=bool(vencidas),
            categoria=str(categoria),
            palavra=str(palavra),
            tentativas_restantes=int(
                document.get(
                    "tentativas_restantes",
                    0,
                )
            ),
            pontos=int(
                document.get(
                    "pontos",
                    0,
                )
            ),
            marca_paco=marca_paco,
        )