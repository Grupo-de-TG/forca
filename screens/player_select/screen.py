"""
Tela de Seleção / Identificação do Jogador.
Permite selecionar um jogador existente ou digitar um novo nome.
"""

from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING, List

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Footer, Header, Input, Label, OptionList, Static
from textual.widgets.option_list import Option

from interfaces.base_screen import BaseGameScreen
from core.ranking_service import Player

if TYPE_CHECKING:
    from forca_app import ForcaApp


class SelectPlayerScreen(BaseGameScreen):
    """Tela para seleção ou cadastro de jogador antes da partida."""

    CSS_PATH = Path(__file__).parent / "player_select.tcss"

    BINDINGS = [
        Binding("escape", "voltar_menu", "Voltar"),
        Binding("ctrl+escape", "voltar_menu", "Voltar"),
        Binding("ctrl+m", "voltar_menu", "Menu"),
        Binding("ctrl+q", "sair_jogo", "Sair"),
    ]

    def __init__(self):
        super().__init__()
        self.players: List[Player] = []

    def compose(self) -> ComposeResult:
        with Container(id="player-select-container"):
            with Vertical(id="player-select-box"):
                yield Label("🎮 IDENTIFICAÇÃO DO JOGADOR", id="player-select-title")
                yield Label("Digite o seu nome ou selecione um perfil salvo:", id="player-select-subtitle")

                yield Input(
                    placeholder="Nome do Jogador...",
                    id="input-player-name",
                    max_length=20,
                )

                yield Label("Jogadores Recentes:", id="player-history-label")
                yield OptionList(id="player-list")

                with Horizontal(id="player-actions"):
                    yield Button("Iniciar Jogo [Enter]", id="btn-confirmar-player", variant="success", classes="player-btn")
                    yield Button("Voltar [Esc]", id="btn-voltar-menu", variant="default", classes="player-btn")

        yield Footer()

    def on_mount(self) -> None:
        self.carregar_jogadores()
        self.query_one("#input-player-name", Input).focus()

    def carregar_jogadores(self) -> None:
        app: ForcaApp = self.app  # type: ignore
        self.players = app.ranking_service.get_all_players()
        opt_list = self.query_one("#player-list", OptionList)
        opt_list.clear_options()

        if self.players:
            for p in self.players[:10]:
                opt_list.add_option(Option(f"{p.name} (Pts: {p.score} | Vitórias: {p.games_won})", id=p.name))
        else:
            opt_list.add_option(Option("Nenhum perfil salvo ainda", disabled=True))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_id:
            input_widget = self.query_one("#input-player-name", Input)
            input_widget.value = str(event.option_id)
            input_widget.focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.confirmar_e_iniciar()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-confirmar-player":
            self.confirmar_e_iniciar()
        elif event.button.id == "btn-voltar-menu":
            self.action_voltar_menu()

    def confirmar_e_iniciar(self) -> None:
        input_widget = self.query_one("#input-player-name", Input)
        nome = input_widget.value.strip()

        if not nome:
            opt_list = self.query_one("#player-list", OptionList)
            if opt_list.highlighted is not None and self.players and opt_list.highlighted < len(self.players):
                nome = self.players[opt_list.highlighted].name
            else:
                nome = "Jogador 1"

        app: ForcaApp = self.app  # type: ignore
        app.current_player = app.ranking_service.get_or_create_player(nome)

        from screens.game.screen import GameScreen
        self.app.push_screen(GameScreen(app.selected_category))

    def action_voltar_menu(self) -> None:
        self.app.pop_screen()

    def action_sair_jogo(self) -> None:
        self.app.exit()

    # Métodos da interface BaseGameScreen
    def on_navigation_up(self) -> None:
        pass

    def on_navigation_down(self) -> None:
        pass

    def on_navigation_left(self) -> None:
        pass

    def on_navigation_right(self) -> None:
        pass

    def on_action_confirm(self) -> None:
        self.confirmar_e_iniciar()
