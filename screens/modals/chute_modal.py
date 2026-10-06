"""
Modal para arriscar a palavra inteira (All-In).
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static


class ChuteModal(ModalScreen[Optional[str]]):
    """Modal para arriscar a palavra inteira (All-In)."""

    CSS_PATH = Path(__file__).parent / "chute.tcss"

    BINDINGS = [
        Binding("escape", "cancelar", "Cancelar"),
        Binding("ctrl+escape", "cancelar", "Cancelar"),
    ]

    def compose(self) -> ComposeResult:
        with Container(classes="modal-dialog"):
            yield Label("🎯 CHUTE ALL-IN (Palavra Completa)", classes="modal-title")
            yield Static(
                "Atenção: Se acertar, você vence na hora!\n"
                "Se errar a palavra, todas as vidas serão perdidas.\n",
                id="chute-aviso",
            )
            yield Input(placeholder="Digite a palavra completa...", id="chute-input")
            with Horizontal(classes="modal-buttons"):
                yield Button("Confirmar Chute [Enter]", id="btn-confirmar-chute", variant="warning")
                yield Button("Cancelar [Esc]", id="btn-cancelar-chute", variant="default")

    def on_mount(self) -> None:
        self.query_one("#chute-input", Input).focus()

    def action_cancelar(self) -> None:
        self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        val = event.value.strip()
        self.dismiss(val if val else None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-confirmar-chute":
            val = self.query_one("#chute-input", Input).value.strip()
            self.dismiss(val if val else None)
        elif event.button.id == "btn-cancelar-chute":
            self.dismiss(None)
