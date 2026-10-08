"""
Modal para Redefinição de Senha do Jogador.
"""

from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.widgets import Button, Input, Label, Static

from interfaces.base_modal import BaseGameModal

if TYPE_CHECKING:
    from forca_app import ForcaApp


class ResetPasswordModal(BaseGameModal[Optional[str]]):
    """Modal interativo para redefinir a senha de um jogador cadastrado."""

    CSS_PATH = Path(__file__).parent / "reset_password.tcss"

    BINDINGS = [
        Binding("escape", "cancelar", "Cancelar"),
        Binding("ctrl+escape", "cancelar", "Cancelar"),
    ]

    def __init__(self, default_name: str = ""):
        super().__init__()
        self.default_name = default_name.strip()

    def compose(self) -> ComposeResult:
        with Container(classes="modal-dialog"):
            yield Label("🔑 ESQUECI A SENHA / REDEFINIR", classes="modal-title")
            yield Static("Digite o nome do jogador e a nova senha desejada:", id="reset-aviso")

            yield Input(
                value=self.default_name,
                placeholder="Nome do Jogador...",
                id="input-reset-nome",
                classes="reset-input",
                max_length=20,
            )

            yield Input(
                placeholder="Nova Senha...",
                password=True,
                id="input-reset-pwd",
                classes="reset-input",
                max_length=32,
            )

            yield Input(
                placeholder="Confirme a Nova Senha...",
                password=True,
                id="input-reset-pwd-confirm",
                classes="reset-input",
                max_length=32,
            )

            yield Static("", id="reset-status-msg")

            with Horizontal(classes="modal-buttons"):
                yield Button("Salvar Nova Senha [Enter]", id="btn-salvar-nova-senha", variant="success")
                yield Button("Cancelar [Esc]", id="btn-cancelar-reset", variant="default")

    def on_mount(self) -> None:
        if self.default_name:
            self.query_one("#input-reset-pwd", Input).focus()
        else:
            self.query_one("#input-reset-nome", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "input-reset-nome":
            self.query_one("#input-reset-pwd", Input).focus()
        elif event.input.id == "input-reset-pwd":
            self.query_one("#input-reset-pwd-confirm", Input).focus()
        elif event.input.id == "input-reset-pwd-confirm":
            self.action_salvar()

    def on_key(self, event: events.Key) -> None:
        focused = self.focused
        focused_id = focused.id if focused else ""

        if event.key == "down":
            if focused_id == "input-reset-nome":
                self.query_one("#input-reset-pwd", Input).focus()
                event.prevent_default()
            elif focused_id == "input-reset-pwd":
                self.query_one("#input-reset-pwd-confirm", Input).focus()
                event.prevent_default()
            elif focused_id == "input-reset-pwd-confirm":
                self.query_one("#btn-salvar-nova-senha", Button).focus()
                event.prevent_default()
            elif focused_id in ("btn-salvar-nova-senha", "btn-cancelar-reset"):
                self.query_one("#input-reset-nome", Input).focus()
                event.prevent_default()
        elif event.key == "up":
            if focused_id == "input-reset-nome":
                self.query_one("#btn-cancelar-reset", Button).focus()
                event.prevent_default()
            elif focused_id == "input-reset-pwd":
                self.query_one("#input-reset-nome", Input).focus()
                event.prevent_default()
            elif focused_id == "input-reset-pwd-confirm":
                self.query_one("#input-reset-pwd", Input).focus()
                event.prevent_default()
            elif focused_id in ("btn-salvar-nova-senha", "btn-cancelar-reset"):
                self.query_one("#input-reset-pwd-confirm", Input).focus()
                event.prevent_default()
        elif event.key == "right" and focused_id == "btn-salvar-nova-senha":
            self.query_one("#btn-cancelar-reset", Button).focus()
            event.prevent_default()
        elif event.key == "left" and focused_id == "btn-cancelar-reset":
            self.query_one("#btn-salvar-nova-senha", Button).focus()
            event.prevent_default()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-salvar-nova-senha":
            self.action_salvar()
        elif event.button.id == "btn-cancelar-reset":
            self.action_cancelar()

    def action_salvar(self) -> None:
        nome = self.query_one("#input-reset-nome", Input).value.strip()
        pwd1 = self.query_one("#input-reset-pwd", Input).value
        pwd2 = self.query_one("#input-reset-pwd-confirm", Input).value
        status = self.query_one("#reset-status-msg", Static)

        if not nome:
            status.update("[bold red]⚠️ Informe o nome do jogador.[/bold red]")
            self.query_one("#input-reset-nome", Input).focus()
            return

        if not pwd1:
            status.update("[bold red]⚠️ Digite a nova senha.[/bold red]")
            self.query_one("#input-reset-pwd", Input).focus()
            return

        if pwd1 != pwd2:
            status.update("[bold red]❌ As senhas não conferem. Tente novamente.[/bold red]")
            self.query_one("#input-reset-pwd-confirm", Input).value = ""
            self.query_one("#input-reset-pwd-confirm", Input).focus()
            return

        app: ForcaApp = self.app  # type: ignore
        sucesso, msg, player = app.ranking_service.reset_password(nome, pwd1)

        if not sucesso or not player:
            status.update(f"[bold red]❌ {msg}[/bold red]")
            return

        self.dismiss(pwd1)

    def action_cancelar(self) -> None:
        self.dismiss(None)
