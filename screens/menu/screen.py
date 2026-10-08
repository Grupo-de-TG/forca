"""
Tela do Menu Principal da Forca.
Herda de BaseGameScreen.
"""

from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.widgets import Button, Footer, Static

from controllers.menu_controller import MenuController
from interfaces.base_screen import BaseGameScreen

if TYPE_CHECKING:
    from forca_app import ForcaApp


class MenuScreen(BaseGameScreen):
    """Tela de abertura com navegação simplificada."""

    CSS_PATH = Path(__file__).parent / "menu.tcss"

    BINDINGS = [
        Binding("r", "abrir_ranking", "Ranking"),
        Binding("ctrl+escape", "sair", "Sair"),
        Binding("ctrl+q", "sair", "Sair"),
    ]

    MENU_BUTTONS = ["btn-jogar", "btn-ranking", "btn-sair"]

    ASCII_LOGO = """
 ███████╗ ██████╗ ██████╗  ██████╗ █████╗ 
 ██╔════╝██╔═══██╗██╔══██╗██╔════╝██╔══██╗
 █████╗  ██║   ██║██████╔╝██║     ███████║
 ██╔══╝  ██║   ██║██╔══██╗██║     ██╔══██║
 ██║     ╚██████╔╝██║  ██║╚██████╗██║  ██║
 ╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝
"""

    def __init__(self):
        super().__init__()
        self.controller = MenuController(self.MENU_BUTTONS)

    def compose(self) -> ComposeResult:
        with Container(id="menu-container"):
            yield Static(self.ASCII_LOGO, id="menu-title")
            yield Static("JOGO DA FORCA - SYSOPS EDITION", id="menu-subtitle")

            with Vertical(id="menu-buttons"):
                yield Button("Iniciar Jogo [Enter]", id="btn-jogar", variant="success", classes="menu-btn")
                yield Button("Ranking [R]", id="btn-ranking", variant="warning", classes="menu-btn")
                yield Button("Sair do Jogo [Ctrl+Esc]", id="btn-sair", variant="error", classes="menu-btn")

        yield Footer()

    def on_mount(self) -> None:
        self.focar_elemento_atual()

    def on_screen_resume(self) -> None:
        self.focar_elemento_atual()

    def focar_elemento_atual(self) -> None:
        target_id = self.controller.get_current_target_id()
        try:
            self.query_one(f"#{target_id}", Button).focus()
        except Exception:
            pass

    # ===== Implementação de BaseGameScreen =====
    def on_navigation_up(self) -> None:
        target_id = self.controller.move_up()
        self.query_one(f"#{target_id}", Button).focus()

    def on_navigation_down(self) -> None:
        target_id = self.controller.move_down()
        self.query_one(f"#{target_id}", Button).focus()

    def on_navigation_left(self) -> None:
        self.on_navigation_up()

    def on_navigation_right(self) -> None:
        self.on_navigation_down()

    def on_action_confirm(self) -> None:
        target_id = self.controller.get_current_target_id()
        if target_id == "btn-jogar":
            self.action_jogar()
        elif target_id == "btn-ranking":
            self.action_abrir_ranking()
        elif target_id == "btn-sair":
            self.action_sair()

    def on_key(self, event: events.Key) -> None:
        if event.key in ("up", "left"):
            self.on_navigation_up()
            event.prevent_default()
        elif event.key in ("down", "right"):
            self.on_navigation_down()
            event.prevent_default()

    def action_jogar(self) -> None:
        from screens.game.screen import GameScreen
        self.app.push_screen(GameScreen(self.app.selected_category))

    def action_abrir_ranking(self) -> None:
        from screens.ranking.screen import RankingScreen
        self.app.push_screen(RankingScreen())

    def action_sair(self) -> None:
        self.app.exit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-jogar":
            self.action_jogar()
        elif event.button.id == "btn-ranking":
            self.action_abrir_ranking()
        elif event.button.id == "btn-sair":
            self.action_sair()
