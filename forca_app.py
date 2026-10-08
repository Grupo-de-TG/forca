"""
Ponto de Entrada Principal da Aplicação Textual da Forca (POO).
Orquestra o ciclo de vida, temas globais e gerenciamento de telas.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional

from textual.app import App
from textual.binding import Binding

from core.database import DatabaseManager
from core.auth_service import AuthService, User
from core.engine import ForcaEngine
from core.models import Categoria
from core.ranking_service import Player, RankingService
from core.word_repository_factory import WordRepositoryFactory
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
        self.word_repo = WordRepositoryFactory.create(backend_type=word_backend)
        self.engine = ForcaEngine(word_repo=self.word_repo)
        self.db = DatabaseManager(db_path)
        self.auth_service = AuthService(self.db)
        self.ranking_service = RankingService(self.db)
        self.selected_category: Optional[Categoria] = None
        self.current_user: Optional[User] = None
        self.current_player: Optional[Player] = None


    def on_mount(self) -> None:
        self.push_screen(MenuScreen())

    def action_quit_app(self) -> None:
        self.exit()


if __name__ == "__main__":
    app = ForcaApp()
    app.run()
