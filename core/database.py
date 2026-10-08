"""
Gerenciador de Banco de Dados SQL (SQLite) para o Jogo da Forca.
"""

from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Optional
from contextlib import contextmanager


class DatabaseManager:
    """Gerencia conexões e esquema do banco de dados SQLite."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            self.db_path = Path(__file__).parent.parent / "data" / "forca.db"
        else:
            self.db_path = db_path

        self._ensure_storage()
        self.init_schema()

    def _ensure_storage(self) -> None:
        if not self.db_path.parent.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        """Retorna conexão SQLite configurada com foreign keys e Row factory."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        return conn

    @contextmanager
    def transaction(self):
        """Context manager para operações atômicas com commit/rollback automático."""
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_schema(self) -> None:
        """Cria as tabelas e índices se não existirem."""
        with self.transaction() as conn:
            # 1. Tabela de Usuários e Autenticação Simples
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL COLLATE NOCASE,
                    password TEXT NOT NULL,
                    marca_paco TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)


            # 2. Tabela de Estatísticas e Ranking dos Jogadores
            conn.execute("""
                CREATE TABLE IF NOT EXISTS player_stats (
                    user_id INTEGER PRIMARY KEY,
                    score INTEGER NOT NULL DEFAULT 0,
                    partidas INTEGER NOT NULL DEFAULT 0,
                    vitorias INTEGER NOT NULL DEFAULT 0,
                    streak_atual INTEGER NOT NULL DEFAULT 0,
                    best_streak INTEGER NOT NULL DEFAULT 0,
                    marca_paco TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
            """)

            # 3. Tabela de Histórico de Partidas
            conn.execute("""
                CREATE TABLE IF NOT EXISTS partidas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    vencidas INTEGER NOT NULL,
                    categoria TEXT NOT NULL,
                    palavra TEXT NOT NULL,
                    tentativas_restantes INTEGER NOT NULL,
                    pontos INTEGER NOT NULL,
                    marca_paco TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
            """)

            # Índices para performance em buscas e ordenação
            conn.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_stats_score ON player_stats(score DESC, vitorias DESC);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_partidas_user ON partidas(user_id, marca_paco DESC);")

