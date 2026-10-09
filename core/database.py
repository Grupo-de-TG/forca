"""
Gerenciador de Banco de Dados Múltiplos (MySQL + MongoDB)
para o Jogo da Forca.

MySQL:
    - users
    - player_stats

MongoDB:
    - dicionario
    - logs_partidas

O esquema do MySQL é criado pelo init.sql durante a inicialização do
container. Este módulo fica responsável apenas pelas conexões.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Iterator, Optional

import mysql.connector
from mysql.connector import Error
from mysql.connector import pooling
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database as MongoDatabase


class MySQLTransaction:
    """Adapta uma conexão MySQL para a interface execute() usada pelos serviços."""

    def __init__(self, connection: Any):
        self.connection = connection

    def execute(
        self,
        query: str,
        params: Optional[tuple[Any, ...]] = None,
    ):
        """Executa uma consulta usando cursor com resultados em dicionário."""
        cursor = self.connection.cursor(
            dictionary=True,
            buffered=True,
        )
        cursor.execute(query, params or ())
        return cursor


class DatabaseManager:
    """Gerencia conexões do MySQL e do MongoDB."""

    def __init__(self, db_path: Optional[Any] = None):
        """
        Inicializa os clientes dos bancos.

        O argumento db_path é mantido por compatibilidade com o código atual
        da aplicação, mas deixa de ser utilizado porque o armazenamento passa
        a ser feito pelo MySQL.
        """
        # Mantido somente para compatibilidade com ForcaApp.
        del db_path

        # ============================================================
        # MYSQL
        # ============================================================

        self.mysql_host = os.getenv(
            "MYSQL_HOST",
            "localhost",
        )

        self.mysql_port = int(
            os.getenv(
                "MYSQL_PORT",
                "3306",
            )
        )

        self.mysql_user = os.getenv(
            "MYSQL_USER",
            "forca_user",
        )

        self.mysql_password = os.getenv(
            "MYSQL_PASSWORD",
            "forca_password",
        )

        self.mysql_database = os.getenv(
            "MYSQL_DATABASE",
            "forca_db",
        )

        self._init_mysql_pool()

        # ============================================================
        # MONGODB
        # ============================================================

        self.mongo_uri = os.getenv(
            "MONGO_URI",
            "mongodb://localhost:27017/",
        )

        self.mongo_database = os.getenv(
            "MONGO_DATABASE",
            "forca_db",
        )

        self._init_mongo()

    def _init_mysql_pool(self) -> None:
        """Cria o pool de conexões do MySQL."""

        try:
            self.mysql_pool = pooling.MySQLConnectionPool(
                pool_name="forca_pool",
                pool_size=5,
                pool_reset_session=True,
                host=self.mysql_host,
                port=self.mysql_port,
                user=self.mysql_user,
                password=self.mysql_password,
                database=self.mysql_database,
                autocommit=False,
            )

        except Error as exc:
            raise RuntimeError(
                "Não foi possível conectar ao MySQL. "
                f"Host={self.mysql_host}:{self.mysql_port}, "
                f"database={self.mysql_database}. "
                f"Erro: {exc}"
            ) from exc

    def _init_mongo(self) -> None:
        """Inicializa o cliente e as coleções do MongoDB."""

        try:
            self.mongo_client = MongoClient(
                self.mongo_uri,
                serverSelectionTimeoutMS=5000,
            )

            # Testa a conexão imediatamente.
            self.mongo_client.admin.command("ping")

        except Exception as exc:
            raise RuntimeError(
                "Não foi possível conectar ao MongoDB "
                f"em {self.mongo_uri}. "
                f"Erro: {exc}"
            ) from exc

        self.mongo_db: MongoDatabase = self.mongo_client[
            self.mongo_database
        ]

        # Coleção do dicionário de palavras.
        self.dicionario_collection: Collection = (
            self.mongo_db["dicionario"]
        )

        # Coleção dos logs/histórico detalhado das partidas.
        self.logs_partidas_collection: Collection = (
            self.mongo_db["logs_partidas"]
        )

        # Aliases para facilitar a utilização futura.
        self.words_collection = self.dicionario_collection
        self.sessions_collection = self.logs_partidas_collection

    @contextmanager
    def transaction(self) -> Iterator[MySQLTransaction]:
        """
        Abre uma transação MySQL com commit/rollback automático.

        O objeto entregue ao bloco possui execute(), mantendo
        temporariamente a forma de uso dos serviços atuais.
        """

        conn = None

        try:
            conn = self.mysql_pool.get_connection()

            transaction = MySQLTransaction(conn)

            yield transaction

            conn.commit()

        except Exception:
            if conn is not None:
                conn.rollback()

            raise

        finally:
            if conn is not None:
                conn.close()

    def close(self) -> None:
        """Fecha o cliente do MongoDB."""

        self.mongo_client.close()