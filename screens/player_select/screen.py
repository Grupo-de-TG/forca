"""
Tela / Modal de Assinatura de Partida e Autenticação de Jogador.
Permite autenticar jogador existente com senha, cadastrar novo jogador ou recuperar senha ao fim da partida.
"""

from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Footer, Input, Label, OptionList, Static
from textual.widgets.option_list import Option

from core.models import GameState
from core.ranking_service import Player
from interfaces.base_modal import BaseGameModal
from screens.modals.reset_password_modal import ResetPasswordModal

if TYPE_CHECKING:
    from forca_app import ForcaApp


class SelectPlayerScreen(BaseGameModal[str]):
    """Modal de assinatura e registro de score pós-partida com autenticação e recuperação."""

    CSS_PATH = Path(__file__).parent / "player_select.tcss"

    BINDINGS = [
        Binding("escape", "pular", "Continuar"),
        Binding("ctrl+escape", "pular", "Continuar"),
        Binding("ctrl+e", "esqueci_senha", "Esqueci Senha"),
        Binding("ctrl+r", "replay", "Jogar Novamente"),
        Binding("ctrl+m", "menu", "Menu"),
        Binding("ctrl+q", "sair_jogo", "Sair"),
    ]

    def __init__(self, game_state: Optional[GameState] = None):
        super().__init__()
        self.game_state = game_state
        self.players: List[Player] = []
        self.signed: bool = False
        self.points_earned: int = 0

    def compose(self) -> ComposeResult:
        with Container(id="player-select-container"):
            with Vertical(id="player-select-box"):
                if self.game_state:
                    venceu = self.game_state.venceu
                    titulo = "🎉 VITÓRIA NA FORCA!" if venceu else "💀 ENFORCADO!"
                    classe_titulo = "vitoria" if venceu else "derrota"
                    yield Label(titulo, id="player-select-title", classes=classe_titulo)

                    pts_estimados = 0
                    if hasattr(self.app, "ranking_service"):
                        cur_streak = self.app.current_player.current_streak if self.app.current_player else 0
                        pts_estimados = self.app.ranking_service.calculate_match_points(
                            won=venceu,
                            attempts_left=self.game_state.tentativas_restantes,
                            current_streak=cur_streak,
                        )

                    resumo = (
                        f"• Palavra: [bold]{self.game_state.palavra_original.upper()}[/bold]\n"
                        f"• Tema: [yellow]{self.game_state.categoria_nome}[/yellow] | "
                        f"Vidas: [cyan]{self.game_state.tentativas_restantes}/6[/cyan] | "
                        f"Pontos em jogo: [bold green]+{pts_estimados} pts[/bold green]"
                    )
                    yield Static(resumo, classes="match-summary")
                else:
                    yield Label("🎮 IDENTIFICAÇÃO DO JOGADOR", id="player-select-title")

                yield Label("✍️ Assine a partida para registrar seu score no Ranking:", id="player-select-subtitle")

                yield Input(
                    placeholder="Nome do Jogador / Apelido...",
                    id="input-player-name",
                    classes="input-field",
                    max_length=20,
                )

                yield Input(
                    placeholder="Senha do Jogador (defina uma nova se for seu 1º jogo)...",
                    password=True,
                    id="input-player-password",
                    classes="input-field",
                    max_length=32,
                )

                yield Static("💡 Digite seu nome e senha para assinar ou criar sua conta.", id="player-status-msg")

                yield Label("Perfis Registrados no Ranking:", id="player-history-label")
                yield OptionList(id="player-list")

                with Horizontal(id="player-actions-row1"):
                    yield Button("Assinar [Enter]", id="btn-assinar", variant="success", classes="player-btn")
                    yield Button("Esqueci Senha [Ctrl+E]", id="btn-esqueci-senha", variant="warning", classes="player-btn")
                    yield Button("Pular [Esc]", id="btn-pular", variant="default", classes="player-btn")

                with Horizontal(id="player-actions-row2"):
                    yield Button("Jogar Novamente [Ctrl+R]", id="btn-replay", variant="primary", classes="player-btn")
                    yield Button("Menu Principal [Ctrl+M]", id="btn-menu", variant="error", classes="player-btn")

        yield Footer()

    def on_mount(self) -> None:
        self.carregar_jogadores()
        app: ForcaApp = self.app  # type: ignore

        input_name = self.query_one("#input-player-name", Input)
        if app.current_player:
            input_name.value = app.current_player.name
            self.atualizar_status_perfil(app.current_player.name)
            self.query_one("#input-player-password", Input).focus()
        else:
            input_name.focus()

    def carregar_jogadores(self) -> None:
        app: ForcaApp = self.app  # type: ignore
        self.players = app.ranking_service.get_all_players()
        opt_list = self.query_one("#player-list", OptionList)
        opt_list.clear_options()

        if self.players:
            for p in self.players[:10]:
                opt_list.add_option(Option(f"👤 {p.name} (Score: {p.score} | Vitórias: {p.games_won})", id=p.name))
        else:
            opt_list.add_option(Option("Nenhum perfil salvo ainda", disabled=True))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_id:
            input_name = self.query_one("#input-player-name", Input)
            input_name.value = str(event.option_id)
            self.atualizar_status_perfil(str(event.option_id))
            self.query_one("#input-player-password", Input).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "input-player-name":
            self.atualizar_status_perfil(event.value)

    def atualizar_status_perfil(self, nome: str) -> None:
        status_widget = self.query_one("#player-status-msg", Static)
        clean_nome = nome.strip()
        if not clean_nome:
            status_widget.update("💡 Digite seu nome e senha para assinar ou criar sua conta.")
            return

        app: ForcaApp = self.app  # type: ignore
        if app.ranking_service.player_exists(clean_nome):
            status_widget.update(f"[yellow]ℹ️ Jogador '{clean_nome}' cadastrado. Digite sua senha para assinar.[/yellow]")
        else:
            status_widget.update(f"[cyan]✨ Novo jogador '{clean_nome}' detectado! Defina sua senha para registrar.[/cyan]")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "input-player-name":
            self.query_one("#input-player-password", Input).focus()
        elif event.input.id == "input-player-password":
            self.action_assinar()

    # ===== Navegação Robusta por Setas =====
    def on_key(self, event: events.Key) -> None:
        focused = self.focused
        focused_id = focused.id if focused else ""

        if event.key == "down":
            if focused_id == "input-player-name":
                self.query_one("#input-player-password", Input).focus()
                event.prevent_default()
            elif focused_id == "input-player-password":
                opt_list = self.query_one("#player-list", OptionList)
                if self.players:
                    opt_list.focus()
                else:
                    self.query_one("#btn-assinar", Button).focus()
                event.prevent_default()
            elif focused_id == "player-list":
                self.query_one("#btn-assinar", Button).focus()
                event.prevent_default()
            elif focused_id == "btn-assinar":
                self.query_one("#btn-replay", Button).focus()
                event.prevent_default()
            elif focused_id in ("btn-esqueci-senha", "btn-pular"):
                self.query_one("#btn-menu", Button).focus()
                event.prevent_default()
            elif focused_id in ("btn-replay", "btn-menu"):
                self.query_one("#input-player-name", Input).focus()
                event.prevent_default()

        elif event.key == "up":
            if focused_id == "input-player-name":
                self.query_one("#btn-replay", Button).focus()
                event.prevent_default()
            elif focused_id == "input-player-password":
                self.query_one("#input-player-name", Input).focus()
                event.prevent_default()
            elif focused_id == "player-list":
                self.query_one("#input-player-password", Input).focus()
                event.prevent_default()
            elif focused_id in ("btn-assinar", "btn-esqueci-senha", "btn-pular"):
                if self.players:
                    self.query_one("#player-list", OptionList).focus()
                else:
                    self.query_one("#input-player-password", Input).focus()
                event.prevent_default()
            elif focused_id == "btn-replay":
                self.query_one("#btn-assinar", Button).focus()
                event.prevent_default()
            elif focused_id == "btn-menu":
                self.query_one("#btn-esqueci-senha", Button).focus()
                event.prevent_default()

        elif event.key == "right":
            if focused_id == "btn-assinar":
                self.query_one("#btn-esqueci-senha", Button).focus()
                event.prevent_default()
            elif focused_id == "btn-esqueci-senha":
                self.query_one("#btn-pular", Button).focus()
                event.prevent_default()
            elif focused_id == "btn-pular":
                self.query_one("#btn-assinar", Button).focus()
                event.prevent_default()
            elif focused_id == "btn-replay":
                self.query_one("#btn-menu", Button).focus()
                event.prevent_default()
            elif focused_id == "btn-menu":
                self.query_one("#btn-replay", Button).focus()
                event.prevent_default()

        elif event.key == "left":
            if focused_id == "btn-pular":
                self.query_one("#btn-esqueci-senha", Button).focus()
                event.prevent_default()
            elif focused_id == "btn-esqueci-senha":
                self.query_one("#btn-assinar", Button).focus()
                event.prevent_default()
            elif focused_id == "btn-assinar":
                self.query_one("#btn-pular", Button).focus()
                event.prevent_default()
            elif focused_id == "btn-menu":
                self.query_one("#btn-replay", Button).focus()
                event.prevent_default()
            elif focused_id == "btn-replay":
                self.query_one("#btn-menu", Button).focus()
                event.prevent_default()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "btn-assinar":
            self.action_assinar()
        elif btn_id == "btn-esqueci-senha":
            self.action_esqueci_senha()
        elif btn_id == "btn-pular":
            self.action_pular()
        elif btn_id == "btn-replay":
            self.action_replay()
        elif btn_id == "btn-menu":
            self.action_menu()

    def action_assinar(self) -> None:
        if self.signed:
            self.query_one("#player-status-msg", Static).update("[green]✅ Esta partida já foi assinada e gravada![/green]")
            self.query_one("#btn-replay", Button).focus()
            return

        input_name = self.query_one("#input-player-name", Input)
        input_pwd = self.query_one("#input-player-password", Input)
        status_widget = self.query_one("#player-status-msg", Static)

        nome = input_name.value.strip()
        senha = input_pwd.value

        if not nome:
            status_widget.update("[bold red]⚠️ Por favor, informe um nome de jogador.[/bold red]")
            input_name.focus()
            return

        if not senha:
            status_widget.update("[bold red]⚠️ Por favor, informe sua senha para autenticar ou cadastrar.[/bold red]")
            input_pwd.focus()
            return

        app: ForcaApp = self.app  # type: ignore
        sucesso, msg, player = app.ranking_service.verify_or_register_player(nome, senha)

        if not sucesso or not player:
            status_widget.update(f"[bold red]❌ {msg}[/bold red]")
            input_pwd.value = ""
            input_pwd.focus()
            return

        # Autenticado com sucesso
        app.current_player = player
        if self.game_state:
            player, self.points_earned = app.ranking_service.record_game_for_player(
                player,
                won=self.game_state.venceu,
                attempts_left=self.game_state.tentativas_restantes,
            )
            app.current_player = player

        self.signed = True
        status_widget.update(
            f"[bold green]✅ Partida assinada com sucesso! Pontos ganhos: +{self.points_earned} | "
            f"Score Total: {player.score} pts (Sequência: {player.current_streak})[/bold green]"
        )
        self.carregar_jogadores()
        self.query_one("#btn-replay", Button).focus()

    def action_esqueci_senha(self) -> None:
        """Abre o modal para redefinir senha do jogador."""
        current_name = self.query_one("#input-player-name", Input).value.strip()

        def callback_reset(nova_senha: Optional[str]) -> None:
            if nova_senha:
                pwd_input = self.query_one("#input-player-password", Input)
                pwd_input.value = nova_senha
                status = self.query_one("#player-status-msg", Static)
                status.update("[bold green]✅ Senha redefinida! Pressione Enter para assinar a partida.[/bold green]")
                self.query_one("#btn-assinar", Button).focus()

        self.app.push_screen(ResetPasswordModal(default_name=current_name), callback_reset)

    def action_pular(self) -> None:
        """Pula a assinatura da partida descartando o resultado."""
        if not self.signed:
            app: ForcaApp = self.app  # type: ignore
            app.current_player = None
        self.dismiss("replay")

    def action_replay(self) -> None:
        """Reinicia uma nova partida."""
        if not self.signed:
            app: ForcaApp = self.app  # type: ignore
            app.current_player = None
        self.dismiss("replay")

    def action_menu(self) -> None:
        """Retorna ao menu principal."""
        if not self.signed:
            app: ForcaApp = self.app  # type: ignore
            app.current_player = None
        self.dismiss("menu")

    def action_sair_jogo(self) -> None:
        self.app.exit()


