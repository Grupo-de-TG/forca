"""
Modal com informações do projeto e mapa de controles.
"""

from __future__ import annotations
from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static


class AboutModal(ModalScreen[None]):
    """Modal com informações do projeto e mapa de controles."""

    CSS_PATH = Path(__file__).parent / "about.tcss"

    BINDINGS = [
        Binding("escape", "fechar", "Fechar"),
        Binding("ctrl+escape", "fechar", "Fechar"),
        Binding("enter", "fechar", "Fechar"),
    ]

    def compose(self) -> ComposeResult:
        with Container(classes="modal-dialog"):
            yield Label("ℹ️ SOBRE & CONTROLES", classes="modal-title")
            yield Static(
                "🎮 [b]Jogo da Forca - SysOps Edition[/b]\n\n"
                "• [b]Autor:[/b] Ryan Henrique Bezerra da Silva\n"
                "• [b]Arquitetura:[/b] POO Modular + Textual TUI (100% Teclado)\n\n"
                "🎯 [b]Como Jogar:[/b]\n"
                "  - [b]Digitar Letra (A-Z) ou Setas (↑ ↓ ← →):[/b] Destaca a letra no teclado virtual\n"
                "  - [b]Enter:[/b] Confirma e aplica a letra selecionada\n"
                "  - [b]Ctrl + F:[/b] Chutar Palavra Completa (All-In)\n"
                "  - [b]Ctrl + R:[/b] Nova Palavra / Reiniciar\n"
                "  - [b]Ctrl + M:[/b] Voltar ao Menu Principal\n"
                "  - [b]Ctrl + Esc (ou Ctrl + Q):[/b] Sair do Jogo\n",
                id="about-text"
            )
            with Horizontal(classes="modal-buttons"):
                yield Button("Entendido [Enter / Esc]", id="btn-close-about", variant="primary")

    def on_mount(self) -> None:
        self.query_one("#btn-close-about", Button).focus()

    def action_fechar(self) -> None:
        self.dismiss(None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.action_fechar()
