"""
Serviço de Autenticação e Usuários (AuthService).

Responsável pelo gerenciamento de:
    - cadastro de usuários;
    - consulta de usuários;
    - autenticação;
    - redefinição de senha.

Os dados permanentes de usuários ficam armazenados no MySQL.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from core.database import DatabaseManager


@dataclass
class User:
    """Representa os dados públicos de um usuário."""

    id: int
    username: str
    marca_paco: str = ""

    @property
    def created_at(self) -> str:
        """Mantém compatibilidade com o código existente."""
        return self.marca_paco


class AuthService:
    """Serviço de autenticação com persistência no MySQL."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def user_exists(self, username: str) -> bool:
        """Verifica se um usuário já existe no banco."""

        clean_name = username.strip()

        if not clean_name:
            return False

        try:
            with self.db.transaction() as conn:
                cursor = conn.execute(
                    """
                    SELECT id
                    FROM users
                    WHERE username = %s
                    LIMIT 1;
                    """,
                    (clean_name,),
                )

                return cursor.fetchone() is not None

        except Exception:
            return False

    def get_user_by_name(self, username: str) -> Optional[User]:
        """Obtém os dados públicos do usuário pelo nome."""

        clean_name = username.strip()

        if not clean_name:
            return None

        with self.db.transaction() as conn:
            cursor = conn.execute(
                """
                SELECT
                    id,
                    username,
                    marca_paco
                FROM users
                WHERE username = %s
                LIMIT 1;
                """,
                (clean_name,),
            )

            row = cursor.fetchone()

            if row:
                return User(
                    id=row["id"],
                    username=row["username"],
                    marca_paco=str(row["marca_paco"]),
                )

            return None

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Obtém os dados públicos do usuário pelo ID."""

        with self.db.transaction() as conn:
            cursor = conn.execute(
                """
                SELECT
                    id,
                    username,
                    marca_paco
                FROM users
                WHERE id = %s
                LIMIT 1;
                """,
                (user_id,),
            )

            row = cursor.fetchone()

            if row:
                return User(
                    id=row["id"],
                    username=row["username"],
                    marca_paco=str(row["marca_paco"]),
                )

            return None

    def register_user(
        self,
        username: str,
        password: str,
    ) -> Tuple[bool, str, Optional[User]]:
        """Cadastra um novo usuário no MySQL."""

        clean_name = username.strip()

        if not clean_name:
            return (
                False,
                "O nome do jogador não pode ser vazio.",
                None,
            )

        if not password:
            return (
                False,
                "A senha não pode ser vazia.",
                None,
            )

        if len(clean_name) > 50:
            return (
                False,
                "O nome do jogador deve ter no máximo 50 caracteres.",
                None,
            )

        if self.user_exists(clean_name):
            return (
                False,
                f"O usuário '{clean_name}' já existe.",
                None,
            )

        try:
            with self.db.transaction() as conn:

                # ------------------------------------------------
                # 1. Cria o usuário
                # ------------------------------------------------

                cursor = conn.execute(
                    """
                    INSERT INTO users (
                        username,
                        password
                    )
                    VALUES (%s, %s);
                    """,
                    (
                        clean_name,
                        password,
                    ),
                )

                user_id = cursor.lastrowid

                # ------------------------------------------------
                # 2. Cria as estatísticas iniciais
                # ------------------------------------------------

                conn.execute(
                    """
                    INSERT INTO player_stats (
                        user_id,
                        score,
                        partidas,
                        vitorias,
                        streak_atual,
                        best_streak
                    )
                    VALUES (
                        %s,
                        0,
                        0,
                        0,
                        0,
                        0
                    );
                    """,
                    (user_id,),
                )

                return (
                    True,
                    f"Novo jogador '{clean_name}' cadastrado com sucesso!",
                    User(
                        id=user_id,
                        username=clean_name,
                    ),
                )

        except Exception as exc:
            return (
                False,
                f"Erro ao registrar usuário: {exc}",
                None,
            )

    def authenticate(
        self,
        username: str,
        password: str,
    ) -> Tuple[bool, str, Optional[User]]:
        """Autentica o usuário verificando a senha no MySQL."""

        clean_name = username.strip()

        if not clean_name:
            return (
                False,
                "O nome do jogador não pode ser vazio.",
                None,
            )

        if not password:
            return (
                False,
                "A senha não pode ser vazia.",
                None,
            )

        with self.db.transaction() as conn:
            cursor = conn.execute(
                """
                SELECT
                    id,
                    username,
                    password,
                    marca_paco
                FROM users
                WHERE username = %s
                LIMIT 1;
                """,
                (clean_name,),
            )

            row = cursor.fetchone()

            if not row:
                return (
                    False,
                    f"Jogador '{clean_name}' não encontrado.",
                    None,
                )

            if row["password"] == password:
                return (
                    True,
                    f"Autenticado com sucesso como '{row['username']}'!",
                    User(
                        id=row["id"],
                        username=row["username"],
                        marca_paco=str(row["marca_paco"]),
                    ),
                )

            return (
                False,
                f"Senha incorreta para o jogador '{row['username']}'.",
                None,
            )

    def verify_or_register_user(
        self,
        username: str,
        password: str,
    ) -> Tuple[bool, str, Optional[User]]:
        """
        Atalho utilizado pela aplicação.

        Se o usuário existir:
            autentica.

        Se não existir:
            cadastra.
        """

        clean_name = username.strip()

        if not clean_name:
            return (
                False,
                "O nome do jogador não pode ser vazio.",
                None,
            )

        if not password:
            return (
                False,
                "A senha não pode ser vazia.",
                None,
            )

        if self.user_exists(clean_name):
            return self.authenticate(
                clean_name,
                password,
            )

        return self.register_user(
            clean_name,
            password,
        )

    def reset_password(
        self,
        username: str,
        new_password: str,
    ) -> Tuple[bool, str, Optional[User]]:
        """Redefine a senha de um usuário existente."""

        clean_name = username.strip()

        if not clean_name:
            return (
                False,
                "O nome do jogador não pode ser vazio.",
                None,
            )

        if not new_password:
            return (
                False,
                "A nova senha não pode ser vazia.",
                None,
            )

        user = self.get_user_by_name(clean_name)

        if not user:
            return (
                False,
                f"Jogador '{clean_name}' não encontrado.",
                None,
            )

        try:
            with self.db.transaction() as conn:
                conn.execute(
                    """
                    UPDATE users
                    SET password = %s
                    WHERE id = %s;
                    """,
                    (
                        new_password,
                        user.id,
                    ),
                )

                return (
                    True,
                    f"Senha do jogador '{user.username}' redefinida com sucesso!",
                    user,
                )

        except Exception as exc:
            return (
                False,
                f"Erro ao redefinir senha: {exc}",
                None,
            )