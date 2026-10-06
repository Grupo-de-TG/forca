"""
Tela Principal do Jogo da Forca.
100% Teclado Físico: Entrada com retorno visual minimalista (underline) e legenda curta.
Layouts Dinâmicos Horizontal e Vertical orientados pela proporção 40/60.
"""

from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Footer, Header, Label, Static

from controllers.letter_buffer_controller import LetterBufferController
from core.models import Categoria, GameState
from core.orientation import OrientationDetector, OrientationType
from interfaces.base_screen import BaseGameScreen

if TYPE_CHECKING:
    from forca_app import ForcaApp


class GameScreen(BaseGameScreen):
    """
    Tela principal da partida da Forca.
    Entrada minimalista via teclado físico com slot de underline e legenda curta.
    """

    CSS_PATH = Path(__file__).parent / "game.tcss"

    BINDINGS = [
        Binding("ctrl+m", "menu_principal", "Menu"),
        Binding("ctrl+f", "chutar_tudo", "Chutar Palavra"),
        Binding("ctrl+r", "reiniciar", "Nova Palavra"),
        Binding("ctrl+escape", "sair_jogo", "Sair"),
        Binding("ctrl+q", "sair_jogo", "Sair"),
    ]

    def __init__(self, categoria: Optional[Categoria] = None):
        super().__init__()
        self.categoria_inicial = categoria
        self.state: Optional[GameState] = None
        self.controller = LetterBufferController()
        self.current_orientation: OrientationType = OrientationType.HORIZONTAL

    AUTO_FOCUS = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with Container(id="game-body"):
            # Painel da Forca (40%: Esquerda no Horizontal, Topo no Vertical)
            with Container(id="forca-panel"):
                yield Static(id="forca-art")
                yield Label(id="vidas-display")

            # Painel Principal (60%: Direita no Horizontal, Base no Vertical)
            with Vertical(id="game-main-panel"):
                with Horizontal():
                    yield Label(id="badge-categoria")
                yield Static(id="palavra-secreta")
                yield Label(id="status-mensagem")

                # Retorno Visual Minimalista da Letra com Underline
                with Horizontal(id="slot-letra-row"):
                    yield Label("Letra: ", id="lbl-letra")
                    yield Static("_", id="slot-letra-candidata")
                    yield Label("[Enter: Enviar | Backspace: Apagar]", id="legenda-curta")

                # Histórico de Letras Certas e Erradas
                with Container(id="letras-historico"):
                    yield Label("Letras Certas: [green]-[/green]", id="letras-certas-box", classes="letras-label")
                    yield Label("Letras Erradas: [red]-[/red]", id="letras-erradas-box", classes="letras-label")

        with Horizontal(id="game-actions"):
            yield Button("🎯 Chutar Palavra [Ctrl+F]", id="btn-chutar", variant="warning", classes="action-btn")
            yield Button("🔄 Nova Palavra [Ctrl+R]", id="btn-nova-palavra", variant="primary", classes="action-btn")
            yield Button("🏠 Menu [Ctrl+M]", id="btn-voltar-menu", variant="default", classes="action-btn")

        yield Footer()

    def on_mount(self) -> None:
        self.ajustar_orientacao(self.size.width, self.size.height)
        app: ForcaApp = self.app  # type: ignore
        self.iniciar_nova_partida(self.categoria_inicial or app.selected_category)

    def on_resize(self, event: events.Resize) -> None:
        self.ajustar_orientacao(event.size.width, event.size.height)

    def ajustar_orientacao(self, width: int, height: int) -> None:
        """Aplica dinamicamente a proporção 40/60 no layout horizontal ou vertical."""
        orientacao = OrientationDetector.detect(width, height)
        self.current_orientation = orientacao

        if orientacao == OrientationType.VERTICAL:
            self.remove_class("layout-horizontal")
            self.add_class("layout-vertical")
        else:
            self.remove_class("layout-vertical")
            self.add_class("layout-horizontal")

    def iniciar_nova_partida(self, categoria: Optional[Categoria] = None) -> None:
        """Inicializa nova rodada e reseta o controlador e buffers."""
        app: ForcaApp = self.app  # type: ignore
        self.state = app.engine.novo_jogo(categoria)
        self.controller.reset()
        self.atualizar_ui()
        self.atualizar_slot_letra()

    def atualizar_ui(self) -> None:
        """Sincroniza os widgets visuais com o estado do jogo."""
        if not self.state:
            return
        app: ForcaApp = self.app  # type: ignore

        # 1. Arte da forca e vidas
        forca_txt = app.engine.obter_arte_forca(self.state.erros)
        self.query_one("#forca-art", Static).update(forca_txt)

        coracoes = "❤️ " * self.state.tentativas_restantes + "🖤 " * self.state.erros
        self.query_one("#vidas-display", Label).update(
            f"Tentativas: {self.state.tentativas_restantes}/6\n{coracoes}"
        )

        # 2. Categoria e Palavra Secreta
        self.query_one("#badge-categoria", Label).update(f"📂 Tema: {self.state.categoria_nome}")
        self.query_one("#palavra-secreta", Static).update(self.state.progresso_exibicao)

        # 3. Status
        self.query_one("#status-mensagem", Label).update(self.state.mensagem)

        # 4. Histórico
        certas_str = ", ".join(c.upper() for c in self.state.letras_certas) or "Nenhuma"
        erradas_str = ", ".join(c.upper() for c in self.state.letras_erradas) or "Nenhuma"
        self.query_one("#letras-certas-box", Label).update(f"Certas: [green]{certas_str}[/green]")
        self.query_one("#letras-erradas-box", Label).update(f"Erradas: [red]{erradas_str}[/red]")

    def atualizar_slot_letra(self) -> None:
        """Atualiza o slot com a letra inserida ou underline."""
        candidata = self.controller.get_candidate()
        if candidata:
            self.query_one("#slot-letra-candidata", Static).update(f"[b][u]{candidata}[/u][/b]")
        else:
            self.query_one("#slot-letra-candidata", Static).update("_")

    # ===== Implementação de BaseGameScreen =====
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
        """Processa exclusivamente a letra candidata quando o usuário teclar Enter."""
        if not self.state or self.state.fim_de_jogo:
            return

        app: ForcaApp = self.app  # type: ignore

        if self.controller.has_candidate():
            letra = self.controller.get_candidate()
            if letra:
                self.state, feedback = app.engine.processar_tentativa(self.state, letra)
                self.controller.clear_candidate()
                self.atualizar_ui()
                self.atualizar_slot_letra()

                if self.state.fim_de_jogo:
                    self.exibir_modal_fim_de_jogo()
        else:
            self.query_one("#status-mensagem", Label).update("⚠️ Digite uma letra no teclado antes de teclar ENTER.")

    def on_key(self, event: events.Key) -> None:
        # Navegação entre botões de ação
        if event.key in ("left", "up"):
            self.on_navigation_left()
            event.prevent_default()
            return
        elif event.key in ("right", "down"):
            self.on_navigation_right()
            event.prevent_default()
            return
        elif event.key == "enter":
            self.on_action_confirm()
            event.prevent_default()
            return
        elif event.key in ("backspace", "delete"):
            self.controller.clear_candidate()
            self.atualizar_slot_letra()
            event.prevent_default()
            return

        # Digitação direta no teclado físico (A-Z ou ç) atualiza o retorno visual da letra
        if event.character and (event.character.isalpha() or event.character == "ç"):
            self.controller.set_candidate(event.character)
            self.atualizar_slot_letra()
            event.prevent_default()

    def action_chutar_tudo(self) -> None:
        if not self.state or self.state.fim_de_jogo:
            return
        from screens.modals.chute_modal import ChuteModal
        app: ForcaApp = self.app  # type: ignore

        def callback_chute(chute: Optional[str]) -> None:
            if chute:
                self.state, acertou = app.engine.processar_chute(self.state, chute)
                self.atualizar_ui()
                self.atualizar_slot_letra()
                self.exibir_modal_fim_de_jogo()

        self.app.push_screen(ChuteModal(), callback_chute)

    def exibir_modal_fim_de_jogo(self) -> None:
        from screens.modals.game_over_modal import GameOverModal
        from screens.categories.screen import CategoryScreen
        app: ForcaApp = self.app  # type: ignore

        def callback_fim(acao: str) -> None:
            if acao == "replay":
                self.iniciar_nova_partida(app.selected_category)
            elif acao == "categories":
                self.app.push_screen(CategoryScreen())
            elif acao == "menu":
                self.app.pop_screen()

        self.app.push_screen(GameOverModal(self.state), callback_fim)

    def action_reiniciar(self) -> None:
        app: ForcaApp = self.app  # type: ignore
        self.iniciar_nova_partida(app.selected_category)

    def action_menu_principal(self) -> None:
        self.app.pop_screen()

    def action_sair_jogo(self) -> None:
        self.app.exit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""
        if btn_id == "btn-chutar":
            self.action_chutar_tudo()
        elif btn_id == "btn-nova-palavra":
            self.action_reiniciar()
        elif btn_id == "btn-voltar-menu":
            self.action_menu_principal()
