"""
Modal exibido ao finalizar a partida com estatísticas e navegação por setas.
Herda de BaseGameModal.
"""

from __future__ import annotations
from pathlib import Path

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.widgets import Button, Label, Static

from controllers.menu_controller import MenuController
from core.models import GameState
from interfaces.base_modal import BaseGameModal


class GameOverModal(BaseGameModal[str]):
    """Modal de fim de jogo com navegação por setas entre opções."""

    CSS_PATH = Path(__file__).parent / "game_over.tcss"

    BINDINGS = [
        Binding("escape", "menu", "Menu"),
        Binding("ctrl+escape", "menu", "Menu"),
        Binding("ctrl+m", "menu", "Menu"),
        Binding("ctrl+r", "replay", "Jogar Novamente"),
    ]

    MODAL_BUTTONS = ["btn-replay", "btn-menu"]

    def __init__(self, state: GameState):
        super().__init__()
        self.game_state = state
        self.controller = MenuController(self.MODAL_BUTTONS)

    def compose(self) -> ComposeResult:
        venceu = self.game_state.venceu
        titulo = "VITÓRIA!" if venceu else "FIM DE JOGO! ENFORCADO"
        classe_titulo = "vitoria" if venceu else "derrota"

        with Container(classes="modal-dialog"):
            yield Label(titulo, classes=f"modal-title {classe_titulo}")
            yield Static(f"Palavra: [b]{self.game_state.palavra_original.upper()}[/b]\n", classes="modal-palavra")
            
            stats_text = (
                f"• Tema: [yellow]{self.game_state.categoria_nome}[/yellow]\n"
                f"• Letras Certas: [green]{len(self.game_state.letras_certas)}[/green]\n"
                f"• Letras Erradas: [red]{len(self.game_state.letras_erradas)}[/red]\n"
                f"• Vidas Restantes: [cyan]{self.game_state.tentativas_restantes}/6[/cyan]"
            )
            yield Static(stats_text, id="modal-stats")

            with Horizontal(classes="modal-buttons"):
                yield Button("Jogar Novamente [Enter]", id="btn-replay", variant="success")
                yield Button("Menu Principal [Ctrl+M]", id="btn-menu", variant="default")

    def on_mount(self) -> None:
        self.focar_elemento_atual()

    def focar_elemento_atual(self) -> None:
        target_id = self.controller.get_current_target_id()
        try:
            self.query_one(f"#{target_id}", Button).focus()
        except Exception:
            pass

    # ===== Implementação de BaseGameModal =====
    def on_navigation_left(self) -> None:
        target_id = self.controller.move_left()
        self.query_one(f"#{target_id}", Button).focus()

    def on_navigation_right(self) -> None:
        target_id = self.controller.move_right()
        self.query_one(f"#{target_id}", Button).focus()

    def on_navigation_up(self) -> None:
        self.on_navigation_left()

    def on_navigation_down(self) -> None:
        self.on_navigation_right()

    def on_action_confirm(self) -> None:
        target_id = self.controller.get_current_target_id()
        if target_id == "btn-replay":
            self.action_replay()
        elif target_id == "btn-menu":
            self.action_menu()

    def action_replay(self) -> None:
        self.dismiss("replay")

    def action_menu(self) -> None:
        self.dismiss("menu")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-replay":
            self.action_replay()
        elif event.button.id == "btn-menu":
            self.action_menu()

    def on_key(self, event: events.Key) -> None:
        if event.key in ("left", "up"):
            self.on_navigation_left()
            event.prevent_default()
        elif event.key in ("right", "down"):
            self.on_navigation_right()
            event.prevent_default()
        elif event.key == "enter":
            self.on_action_confirm()
            event.prevent_default()
