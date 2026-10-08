"""
Serviço Dedicado de Autenticação, Usuários e Criptografia (AuthService).
Responsável exclusivo pelo gerenciamento de credenciais e integridade de acesso.
"""

from __future__ import annotations
from dataclasses import dataclass
import hashlib
import secrets
from typing import Optional, Tuple

from core.database import DatabaseManager


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
class User:
    id: int
    username: str
    created_at: str = ""


class AuthService:
    """Serviço de Autenticação com persistência em banco de dados relacional SQL."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def user_exists(self, username: str) -> bool:
        """Verifica se um usuário já existe no banco."""
        clean_name = username.strip()
        if not clean_name:
            return False

        with self.db.transaction() as conn:
            cursor = conn.execute("SELECT 1 FROM users WHERE username = ? COLLATE NOCASE;", (clean_name,))
            return cursor.fetchone() is not None

    def get_user_by_name(self, username: str) -> Optional[User]:
        """Obtém os dados públicos do usuário por nome."""
        clean_name = username.strip()
        if not clean_name:
            return None

        with self.db.transaction() as conn:
            cursor = conn.execute(
                "SELECT id, username, created_at FROM users WHERE username = ? COLLATE NOCASE;",
                (clean_name,),
            )
            row = cursor.fetchone()
            if row:
                return User(id=row["id"], username=row["username"], created_at=str(row["created_at"]))
            return None

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Obtém os dados do usuário por ID."""
        with self.db.transaction() as conn:
            cursor = conn.execute(
                "SELECT id, username, created_at FROM users WHERE id = ?;",
                (user_id,),
            )
            row = cursor.fetchone()
            if row:
                return User(id=row["id"], username=row["username"], created_at=str(row["created_at"]))
            return None

    def register_user(self, username: str, password: str) -> Tuple[bool, str, Optional[User]]:
        """Cadastra um novo usuário no sistema."""
        clean_name = username.strip()
        if not clean_name:
            return False, "O nome do jogador não pode ser vazio.", None
        if not password:
            return False, "A senha não pode ser vazia.", None

        if self.user_exists(clean_name):
            return False, f"O usuário '{clean_name}' já existe.", None

        pwd_hash, pwd_salt = hash_password(password)

        try:
            with self.db.transaction() as conn:
                cursor = conn.execute(
                    "INSERT INTO users (username, password_hash, password_salt) VALUES (?, ?, ?);",
                    (clean_name, pwd_hash, pwd_salt),
                )
                user_id = cursor.lastrowid
                # Inicializa linha de estatísticas do jogador
                conn.execute(
                    "INSERT INTO player_stats (user_id, score, games_played, games_won, current_streak, best_streak) VALUES (?, 0, 0, 0, 0, 0);",
                    (user_id,),
                )
                return True, f"Novo jogador '{clean_name}' cadastrado com sucesso!", User(id=user_id, username=clean_name)
        except Exception as e:
            return False, f"Erro ao registrar usuário: {e}", None

    def authenticate(self, username: str, password: str) -> Tuple[bool, str, Optional[User]]:
        """Autentica usuário e senha contra o banco de dados."""
        clean_name = username.strip()
        if not clean_name:
            return False, "O nome do jogador não pode ser vazio.", None
        if not password:
            return False, "A senha não pode ser vazia.", None

        with self.db.transaction() as conn:
            cursor = conn.execute(
                "SELECT id, username, password_hash, password_salt, created_at FROM users WHERE username = ? COLLATE NOCASE;",
                (clean_name,),
            )
            row = cursor.fetchone()
            if not row:
                return False, f"Jogador '{clean_name}' não encontrado.", None

            if verify_password(password, row["password_hash"], row["password_salt"]):
                return True, f"Autenticado com sucesso como '{row['username']}'!", User(
                    id=row["id"], username=row["username"], created_at=str(row["created_at"])
                )
            else:
                return False, f"Senha incorreta para o jogador '{row['username']}'.", None

    def verify_or_register_user(self, username: str, password: str) -> Tuple[bool, str, Optional[User]]:
        """
        Atalho inteligente para assinatura pós-partida:
        Se o usuário já existir, autentica com a senha fornecida.
        Se não existir, registra uma nova conta com essa senha.
        """
        clean_name = username.strip()
        if not clean_name:
            return False, "O nome do jogador não pode ser vazio.", None
        if not password:
            return False, "A senha não pode ser vazia.", None

        if self.user_exists(clean_name):
            return self.authenticate(clean_name, password)
        else:
            return self.register_user(clean_name, password)

    def reset_password(self, username: str, new_password: str) -> Tuple[bool, str, Optional[User]]:
        """Redefine a senha de um usuário existente."""
        clean_name = username.strip()
        if not clean_name:
            return False, "O nome do jogador não pode ser vazio.", None
        if not new_password:
            return False, "A nova senha não pode ser vazia.", None

        user = self.get_user_by_name(clean_name)
        if not user:
            return False, f"Jogador '{clean_name}' não encontrado.", None

        pwd_hash, pwd_salt = hash_password(new_password)

        try:
            with self.db.transaction() as conn:
                conn.execute(
                    "UPDATE users SET password_hash = ?, password_salt = ? WHERE id = ?;",
                    (pwd_hash, pwd_salt, user.id),
                )
                return True, f"Senha do jogador '{user.username}' redefinida com sucesso!", user
        except Exception as e:
            return False, f"Erro ao redefinir senha: {e}", None
