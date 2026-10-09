"""
Ponto de Entrada Principal da Aplicação Textual da Forca (POO).
Orquestra o ciclo de vida, temas globais, gerenciamento de telas,
conexões com MySQL, MongoDB e Neo4j.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional

from textual.app import App
from textual.binding import Binding

from core.database import DatabaseManager
from core.dictionary_seed import seed_dictionary
from core.auth_service import AuthService, User
from core.engine import ForcaEngine
from core.models import Categoria
from core.ranking_service import Player, RankingService
from core.word_repository_factory import WordRepositoryFactory
from core.neo4j_hint_repository import Neo4jHintRepository
from screens.menu.screen import MenuScreen


class ForcaApp(App):
    """Aplicação Textual da Forca - SysOps Edition."""

    CSS_PATH = Path(__file__).parent / "styles" / "global.tcss"
    TITLE = "Jogo da Forca - SysOps"
    SUB_TITLE = "Textual TUI (POO Modular)"
    theme = "textual-dark"

    BINDINGS = [
        Binding("ctrl+escape", "quit_app", "Sair"),
        Binding("ctrl+q", "quit_app", "Sair"),
    ]

    def __init__(self, db_path: Optional[Path] = None, word_backend: Optional[str] = None):
        super().__init__()
        
        # 1. Conexões de Banco Relacional (MySQL) e Documental (MongoDB)
        self.db = DatabaseManager(db_path)

        # 2. Carga idempotente do dicionário no MongoDB (se conectado)
        try:
            seed_dictionary(
                self.db.dicionario_collection,
                Path(__file__).parent / "listas",
            )
        except Exception:
            pass

        # 3. Repositórios Desacoplados de Palavras (MongoDB/File) e Dicas (Neo4j)
        self.word_repo = WordRepositoryFactory.create(backend_type=word_backend)
        self.hint_repo = Neo4jHintRepository()
        self.engine = ForcaEngine(word_repo=self.word_repo, hint_repo=self.hint_repo)

        # 4. Serviços de Autenticação e Ranking
        self.auth_service = AuthService(self.db)
        self.ranking_service = RankingService(self.db)

        # 5. Estado de Sessão
        self.selected_category: Optional[Categoria] = None
        self.current_user: Optional[User] = None
        self.current_player: Optional[Player] = None

    def on_mount(self) -> None:
        self.push_screen(MenuScreen())

    def on_unmount(self) -> None:
        if hasattr(self, "db"):
            try:
                self.db.close()
            except Exception:
                pass

    def action_quit_app(self) -> None:
        self.exit()


if __name__ == "__main__":
    app = ForcaApp()
    app.run()
