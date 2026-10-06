"""
Tela de Seleção de Categorias de Palavras.
Herda de BaseGameScreen.
"""

from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.widgets import Button, Footer, Label, OptionList, Static
from textual.widgets.option_list import Option

from interfaces.base_screen import BaseGameScreen

if TYPE_CHECKING:
    from forca_app import ForcaApp


class CategoryScreen(BaseGameScreen):
    """Tela para selecionar o tema com navegação pura por setas."""

    CSS_PATH = Path(__file__).parent / "categories.tcss"

    BINDINGS = [
        Binding("escape", "voltar", "Voltar"),
        Binding("ctrl+escape", "voltar", "Voltar"),
        Binding("ctrl+m", "voltar", "Voltar"),
        Binding("enter", "confirmar", "Confirmar"),
    ]

    def compose(self) -> ComposeResult:
        with Container(id="category-container"):
            yield Label("📂 ESCOLHA UMA CATEGORIA", id="menu-title")
            yield Static("Use as setas [b]↑ e ↓[/b] para navegar pelas listas e [b]Enter[/b] para confirmar:", id="menu-subtitle")
            yield OptionList(id="category-list")
            with Horizontal(classes="modal-buttons"):
                yield Button("Selecionar [Enter]", id="btn-select-cat", variant="success")
                yield Button("Voltar [Esc]", id="btn-voltar-cat", variant="default")
        yield Footer()

    def on_mount(self) -> None:
        app: ForcaApp = self.app  # type: ignore
        option_list = self.query_one("#category-list", OptionList)
        option_list.clear_options()
        
        # Opção 0: Aleatório
        option_list.add_option(Option("🎲 Modo Aleatório (Mistura todas as listas)", id="cat_all"))
        
        # Opções das listas carregadas
        for i, cat in enumerate(app.engine.categorias):
            label = f"📁 {cat.nome} ({cat.total_palavras} palavras)"
            option_list.add_option(Option(label, id=f"cat_{i}"))

        option_list.highlighted = 0
        option_list.focus()

    # ===== Implementação de BaseGameScreen =====
    def on_navigation_up(self) -> None:
        pass  # Tratado nativamente pelo OptionList

    def on_navigation_down(self) -> None:
        pass  # Tratado nativamente pelo OptionList

    def on_navigation_left(self) -> None:
        pass

    def on_navigation_right(self) -> None:
        pass

    def on_action_confirm(self) -> None:
        self.action_confirmar()

    def action_voltar(self) -> None:
        self.app.pop_screen()

    def action_confirmar(self) -> None:
        app: ForcaApp = self.app  # type: ignore
        option_list = self.query_one("#category-list", OptionList)
        idx = option_list.highlighted
        if idx == 0:
            app.selected_category = None
        elif idx is not None and idx > 0 and idx - 1 < len(app.engine.categorias):
            app.selected_category = app.engine.categorias[idx - 1]

        self.app.pop_screen()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-select-cat":
            self.action_confirmar()
        elif event.button.id == "btn-voltar-cat":
            self.action_voltar()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self.action_confirmar()
