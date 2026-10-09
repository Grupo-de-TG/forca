"""
Tela de Ranking / Leaderboard Geral.
Exibe tabela de pontuação e estatísticas dos jogadores salvos.
"""

from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING, List

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, DataTable, Footer, Label, Static

from interfaces.base_screen import BaseGameScreen
from core.ranking_service import Player

if TYPE_CHECKING:
    from forca_app import ForcaApp


class RankingScreen(BaseGameScreen):
    """Tela de exibição do ranking dos melhores jogadores."""

    CSS_PATH = Path(__file__).parent / "ranking.tcss"

    BINDINGS = [
        Binding("escape", "voltar_menu", "Voltar"),
        Binding("ctrl+escape", "voltar_menu", "Voltar"),
        Binding("ctrl+m", "voltar_menu", "Menu"),
        Binding("ctrl+q", "sair_jogo", "Sair"),
    ]

    def __init__(self):
        super().__init__()

    def compose(self) -> ComposeResult:
        with Container(id="ranking-container"):
            with Vertical(id="ranking-box"):
                yield Label("RANKING GERAL - TOP JOGADORES", id="ranking-title")
                yield Label("Classificação por pontuação acumulada e desempenho", id="ranking-subtitle")

                yield DataTable(id="ranking-table")

                with Horizontal(id="ranking-actions"):
                    yield Button("Voltar ao Menu [Esc]", id="btn-voltar-menu", variant="primary", classes="ranking-btn")

        yield Footer()

    def on_mount(self) -> None:
        self.popular_tabela()
        self.query_one("#btn-voltar-menu", Button).focus()

    def popular_tabela(self) -> None:
        app: ForcaApp = self.app  # type: ignore
        players: List[Player] = app.ranking_service.get_all_players()

        table = self.query_one("#ranking-table", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True

        table.add_columns("Pos", "Jogador", "Pontos", "Vitórias", "Partidas", "Taxa Vit.", "Maior Streak")

        if not players:
            table.add_row("-", "Nenhum registro ainda", "0", "0", "0", "0.0%", "0")
            return

        for idx, p in enumerate(players, start=1):
            pos_icon = f"{idx}º"

            table.add_row(
                pos_icon,
                p.name,
                str(p.score),
                str(p.games_won),
                str(p.games_played),
                f"{p.win_rate:.1f}%",
                str(p.best_streak),
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-voltar-menu":
            self.action_voltar_menu()

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
        self.action_voltar_menu()
