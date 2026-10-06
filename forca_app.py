"""
Aplicação Textual TUI do Jogo da Forca - SysOps Edition.
Zero dependência de mouse, navegação total por setas, confirmação de letra no Enter,
destaque visual no teclado e atalhos compostos (Ctrl+Esc, Ctrl+F, Ctrl+R, Ctrl+M).
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Optional, List, Tuple

from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen, ModalScreen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    OptionList,
    Static,
)
from textual.widgets.option_list import Option

from forca_game import ForcaEngine, Categoria, GameState


# ==========================================
# MODAL: CHUTAR PALAVRA COMPLETA (ALL-IN)
# ==========================================
class ChuteModal(ModalScreen[Optional[str]]):
    """Modal para arriscar a palavra inteira (All-In)."""

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


# ==========================================
# MODAL: FIM DE JOGO (VITÓRIA OU DERROTA)
# ==========================================
class GameOverModal(ModalScreen[str]):
    """Modal de fim de jogo com navegação por setas entre opções."""

    BINDINGS = [
        Binding("escape", "menu", "Menu"),
        Binding("ctrl+escape", "menu", "Menu"),
        Binding("ctrl+m", "menu", "Menu"),
        Binding("ctrl+r", "replay", "Jogar Novamente"),
    ]

    MODAL_BUTTONS = ["btn-replay", "btn-cat", "btn-menu"]

    def __init__(self, state: GameState):
        super().__init__()
        self.game_state = state

    def compose(self) -> ComposeResult:
        venceu = self.game_state.venceu
        titulo = "🎉 VITÓRIA ESPETACULAR! 🎉" if venceu else "💀 FIM DE JOGO! ENFORCADO 💀"
        classe_titulo = "vitoria" if venceu else "derrota"

        with Container(classes="modal-dialog"):
            yield Label(titulo, classes=f"modal-title {classe_titulo}")
            yield Static(f"A palavra secreta era: [b]{self.game_state.palavra_original.upper()}[/b]\n", classes="modal-palavra")
            
            stats_text = (
                f"• Categoria: [yellow]{self.game_state.categoria_nome}[/yellow]\n"
                f"• Letras Certas: [green]{len(self.game_state.letras_certas)}[/green]\n"
                f"• Letras Erradas: [red]{len(self.game_state.letras_erradas)}[/red]\n"
                f"• Vidas Restantes: [cyan]{self.game_state.tentativas_restantes}/6[/cyan]"
            )
            yield Static(stats_text, id="modal-stats")

            with Horizontal(classes="modal-buttons"):
                yield Button("Jogar Novamente [Enter]", id="btn-replay", variant="success")
                yield Button("Trocar Categoria", id="btn-cat", variant="primary")
                yield Button("Menu Principal", id="btn-menu", variant="default")

    def on_mount(self) -> None:
        self.query_one("#btn-replay", Button).focus()

    def action_replay(self) -> None:
        self.dismiss("replay")

    def action_categories(self) -> None:
        self.dismiss("categories")

    def action_menu(self) -> None:
        self.dismiss("menu")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-replay":
            self.action_replay()
        elif event.button.id == "btn-cat":
            self.action_categories()
        elif event.button.id == "btn-menu":
            self.action_menu()

    def on_key(self, event: events.Key) -> None:
        focused = self.focused
        if not focused or not focused.id:
            return

        if event.key in ("left", "up"):
            if focused.id in self.MODAL_BUTTONS:
                idx = self.MODAL_BUTTONS.index(focused.id)
                novo_idx = (idx - 1) % len(self.MODAL_BUTTONS)
                self.query_one(f"#{self.MODAL_BUTTONS[novo_idx]}", Button).focus()
                event.prevent_default()
        elif event.key in ("right", "down"):
            if focused.id in self.MODAL_BUTTONS:
                idx = self.MODAL_BUTTONS.index(focused.id)
                novo_idx = (idx + 1) % len(self.MODAL_BUTTONS)
                self.query_one(f"#{self.MODAL_BUTTONS[novo_idx]}", Button).focus()
                event.prevent_default()


# ==========================================
# MODAL: SOBRE / REGRAS
# ==========================================
class AboutModal(ModalScreen[None]):
    """Modal com informações do projeto e mapa de controles."""

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
                "• [b]Tecnologia:[/b] Python + Textual TUI (100% Teclado)\n\n"
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


# ==========================================
# TELA: SELEÇÃO DE CATEGORIAS
# ==========================================
class CategoryScreen(Screen):
    """Tela para selecionar o tema com navegação pura por setas."""

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
        option_list = self.query_one("#category-list", OptionList)
        option_list.clear_options()
        
        # Opção 0: Aleatório
        option_list.add_option(Option("🎲 Modo Aleatório (Mistura todas as listas)", id="cat_all"))
        
        # Opções das listas carregadas
        for i, cat in enumerate(self.app.engine.categorias):
            label = f"📁 {cat.nome} ({cat.total_palavras} palavras)"
            option_list.add_option(Option(label, id=f"cat_{i}"))

        option_list.highlighted = 0
        option_list.focus()

    def action_voltar(self) -> None:
        self.app.pop_screen()

    def action_confirmar(self) -> None:
        option_list = self.query_one("#category-list", OptionList)
        idx = option_list.highlighted
        if idx == 0:
            self.app.selected_category = None
        elif idx is not None and idx > 0 and idx - 1 < len(self.app.engine.categorias):
            self.app.selected_category = self.app.engine.categorias[idx - 1]

        self.app.pop_screen()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-select-cat":
            self.action_confirmar()
        elif event.button.id == "btn-voltar-cat":
            self.action_voltar()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self.action_confirmar()


# ==========================================
# TELA: JOGO DA FORCA (100% TECLADO & SETAS)
# ==========================================
class GameScreen(Screen):
    """
    Tela principal do jogo.
    Navegação 2D no teclado virtual via setas (↑ ↓ ← →),
    digitação direta destaca a letra, e Enter confirma a jogada.
    """

    BINDINGS = [
        Binding("ctrl+m", "menu_principal", "Menu"),
        Binding("ctrl+f", "chutar_tudo", "Chutar Palavra"),
        Binding("ctrl+r", "reiniciar", "Nova Palavra"),
        Binding("ctrl+escape", "sair_jogo", "Sair"),
        Binding("ctrl+q", "sair_jogo", "Sair"),
    ]

    # Matriz 2D para navegação por setas (3 linhas de letras + 1 linha de botões de ação)
    GRID_MAP = [
        ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"],
        ["a", "s", "d", "f", "g", "h", "j", "k", "l"],
        ["z", "x", "c", "v", "b", "n", "m"],
        ["btn-chutar", "btn-nova-palavra", "btn-voltar-menu"]
    ]

    def __init__(self, categoria: Optional[Categoria] = None):
        super().__init__()
        self.categoria_inicial = categoria
        self.state: Optional[GameState] = None
        self.cursor_r = 1  # Inicia na linha do 'A'
        self.cursor_c = 0  # Inicia na letra 'A'

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with Container(id="game-body"):
            # Coluna Esquerda: Forca ASCII e Vidas
            with Vertical(id="forca-panel"):
                yield Static(id="forca-art")
                yield Label(id="vidas-display")

            # Coluna Direita: Jogo
            with Vertical(id="game-main-panel"):
                with Horizontal():
                    yield Label(id="badge-categoria")
                yield Static(id="palavra-secreta")
                yield Label(id="status-mensagem")

                # Histórico de Letras
                with Container(id="letras-historico"):
                    yield Label("Letras Certas: [green]-[/green]", id="letras-certas-box", classes="letras-label")
                    yield Label("Letras Erradas: [red]-[/red]", id="letras-erradas-box", classes="letras-label")

                # Teclado Virtual Interativo (Destacável e Navegável por setas)
                with Vertical(id="teclado-container"):
                    for r, linha in enumerate(self.GRID_MAP[:3]):
                        with Horizontal(classes="teclado-linha"):
                            for letra in linha:
                                yield Button(letra.upper(), id=f"key-{letra}", classes="key-btn")

        with Horizontal(id="game-actions"):
            yield Button("🎯 Chutar Palavra [Ctrl+F]", id="btn-chutar", variant="warning", classes="action-btn")
            yield Button("🔄 Nova Palavra [Ctrl+R]", id="btn-nova-palavra", variant="primary", classes="action-btn")
            yield Button("🏠 Menu [Ctrl+M]", id="btn-voltar-menu", variant="default", classes="action-btn")

        yield Footer()

    def on_mount(self) -> None:
        self.iniciar_nova_partida(self.categoria_inicial or self.app.selected_category)
        self.focar_no_cursor()

    def iniciar_nova_partida(self, categoria: Optional[Categoria] = None) -> None:
        """Inicializa nova rodada e reseta o teclado."""
        self.state = self.app.engine.novo_jogo(categoria)
        self.atualizar_ui()
        self.resetar_teclado()
        self.cursor_r = 1
        self.cursor_c = 0
        self.focar_no_cursor()

    def atualizar_ui(self) -> None:
        """Sincroniza os widgets visuais com o estado do jogo."""
        if not self.state:
            return

        # 1. Arte da forca e vidas
        forca_txt = self.app.engine.obter_arte_forca(self.state.erros)
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

    def resetar_teclado(self) -> None:
        for btn in self.query(".key-btn"):
            btn.remove_class("usada-certa")
            btn.remove_class("usada-errada")

    def registrar_letra_no_teclado(self, letra: str, feedback: str) -> None:
        try:
            btn = self.query_one(f"#key-{letra.lower()}", Button)
            if feedback == "acerto":
                btn.add_class("usada-certa")
            elif feedback == "erro":
                btn.add_class("usada-errada")
        except Exception:
            pass

    def focar_no_cursor(self) -> None:
        """Move o foco visual para o elemento correspondente à posição (cursor_r, cursor_c)."""
        elem = self.GRID_MAP[self.cursor_r][self.cursor_c]
        widget_id = elem if elem.startswith("btn-") else f"key-{elem}"
        try:
            self.query_one(f"#{widget_id}", Button).focus()
        except Exception:
            pass

    def mover_cursor_para_letra(self, letra: str) -> None:
        """Localiza a letra no grid 2D e foca nela imediatamente para reflexão antes do Enter."""
        letra_low = letra.lower()
        for r in range(3):
            if letra_low in self.GRID_MAP[r]:
                self.cursor_r = r
                self.cursor_c = self.GRID_MAP[r].index(letra_low)
                self.focar_no_cursor()
                self.query_one("#status-mensagem", Label).update(
                    f"Letra [b]{letra.upper()}[/b] selecionada. Pressione [b]ENTER[/b] para confirmar."
                )
                return

    def tentar_letra_atual(self) -> None:
        """Aplica a letra atualmente focada na matriz quando o jogador teclar Enter."""
        if not self.state or self.state.fim_de_jogo:
            return

        if self.cursor_r < 3:
            letra = self.GRID_MAP[self.cursor_r][self.cursor_c]
            self.state, feedback = self.app.engine.processar_tentativa(self.state, letra)
            self.registrar_letra_no_teclado(letra, feedback)
            self.atualizar_ui()

            if self.state.fim_de_jogo:
                self.exibir_modal_fim_de_jogo()
        else:
            # Pressionou enter em um botão de ação
            btn_id = self.GRID_MAP[self.cursor_r][self.cursor_c]
            if btn_id == "btn-chutar":
                self.action_chutar_tudo()
            elif btn_id == "btn-nova-palavra":
                self.action_reiniciar()
            elif btn_id == "btn-voltar-menu":
                self.action_menu_principal()

    def on_key(self, event: events.Key) -> None:
        # Navegação 2D por Setas
        if event.key == "left":
            self.cursor_c = max(0, self.cursor_c - 1)
            self.focar_no_cursor()
            event.prevent_default()
            return
        elif event.key == "right":
            max_c = len(self.GRID_MAP[self.cursor_r]) - 1
            self.cursor_c = min(max_c, self.cursor_c + 1)
            self.focar_no_cursor()
            event.prevent_default()
            return
        elif event.key == "up":
            self.cursor_r = max(0, self.cursor_r - 1)
            max_c = len(self.GRID_MAP[self.cursor_r]) - 1
            self.cursor_c = min(self.cursor_c, max_c)
            self.focar_no_cursor()
            event.prevent_default()
            return
        elif event.key == "down":
            self.cursor_r = min(len(self.GRID_MAP) - 1, self.cursor_r + 1)
            max_c = len(self.GRID_MAP[self.cursor_r]) - 1
            self.cursor_c = min(self.cursor_c, max_c)
            self.focar_no_cursor()
            event.prevent_default()
            return
        elif event.key == "enter":
            self.tentar_letra_atual()
            event.prevent_default()
            return

        # Digitação direta de qualquer letra (A-Z) move o foco para a letra correspondente
        if event.character and event.character.isalpha():
            self.mover_cursor_para_letra(event.character)
            event.prevent_default()

    def action_chutar_tudo(self) -> None:
        if not self.state or self.state.fim_de_jogo:
            return

        def callback_chute(chute: Optional[str]) -> None:
            if chute:
                self.state, acertou = self.app.engine.processar_chute(self.state, chute)
                self.atualizar_ui()
                self.exibir_modal_fim_de_jogo()
            else:
                self.focar_no_cursor()

        self.app.push_screen(ChuteModal(), callback_chute)

    def exibir_modal_fim_de_jogo(self) -> None:
        def callback_fim(acao: str) -> None:
            if acao == "replay":
                self.iniciar_nova_partida(self.app.selected_category)
            elif acao == "categories":
                self.app.push_screen(CategoryScreen())
            elif acao == "menu":
                self.app.pop_screen()

        self.app.push_screen(GameOverModal(self.state), callback_fim)

    def action_reiniciar(self) -> None:
        self.iniciar_nova_partida(self.app.selected_category)

    def action_menu_principal(self) -> None:
        self.app.pop_screen()

    def action_sair_jogo(self) -> None:
        self.app.exit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""
        if btn_id.startswith("key-"):
            letra = btn_id.replace("key-", "")
            self.mover_cursor_para_letra(letra)
        elif btn_id == "btn-chutar":
            self.action_chutar_tudo()
        elif btn_id == "btn-nova-palavra":
            self.action_reiniciar()
        elif btn_id == "btn-voltar-menu":
            self.action_menu_principal()


# ==========================================
# TELA: MENU PRINCIPAL (NAVEGAÇÃO PURA POR SETAS)
# ==========================================
class MenuScreen(Screen):
    """Tela de abertura com navegação por setas e atalhos compostos."""

    BINDINGS = [
        Binding("ctrl+escape", "sair", "Sair"),
        Binding("ctrl+q", "sair", "Sair"),
        Binding("ctrl+s", "sobre", "Sobre"),
        Binding("ctrl+c", "categorias", "Categorias"),
    ]

    MENU_BUTTONS = ["btn-jogar", "btn-categorias", "btn-sobre", "btn-sair"]

    ASCII_LOGO = """
 ███████╗ ██████╗ ██████╗  ██████╗ █████╗ 
 ██╔════╝██╔═══██╗██╔══██╗██╔════╝██╔══██╗
 █████╗  ██║   ██║██████╔╝██║     ███████║
 ██╔══╝  ██║   ██║██╔══██╗██║     ██╔══██║
 ██║     ╚██████╔╝██║  ██║╚██████╗██║  ██║
 ╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝
"""

    def compose(self) -> ComposeResult:
        with Container(id="menu-container"):
            yield Static(self.ASCII_LOGO, id="menu-title")
            yield Static("🎮 JOGO DA FORCA - SYSOPS EDITION 🎮", id="menu-subtitle")
            yield Label(id="menu-category-info")

            with Vertical(id="menu-buttons"):
                yield Button("🚀 Iniciar Jogo [Enter]", id="btn-jogar", variant="success", classes="menu-btn")
                yield Button("📂 Escolher Categoria [Ctrl+C]", id="btn-categorias", variant="primary", classes="menu-btn")
                yield Button("ℹ️ Sobre & Controles [Ctrl+S]", id="btn-sobre", variant="default", classes="menu-btn")
                yield Button("🚪 Sair do Jogo [Ctrl+Esc]", id="btn-sair", variant="error", classes="menu-btn")

        yield Footer()

    def on_mount(self) -> None:
        self.atualizar_categoria_info()
        # Inicia imediatamente focado no primeiro botão
        self.query_one("#btn-jogar", Button).focus()

    def on_screen_resume(self) -> None:
        self.atualizar_categoria_info()
        self.query_one("#btn-jogar", Button).focus()

    def atualizar_categoria_info(self) -> None:
        cat = self.app.selected_category
        cat_nome = cat.nome if cat else "Aleatório (Todas as listas)"
        self.query_one("#menu-category-info", Label).update(f"📂 Tema Atual: {cat_nome}")

    def on_key(self, event: events.Key) -> None:
        focused = self.focused
        if not focused or not focused.id:
            return

        if event.key in ("up", "left"):
            if focused.id in self.MENU_BUTTONS:
                idx = self.MENU_BUTTONS.index(focused.id)
                novo_idx = (idx - 1) % len(self.MENU_BUTTONS)
                self.query_one(f"#{self.MENU_BUTTONS[novo_idx]}", Button).focus()
                event.prevent_default()
        elif event.key in ("down", "right"):
            if focused.id in self.MENU_BUTTONS:
                idx = self.MENU_BUTTONS.index(focused.id)
                novo_idx = (idx + 1) % len(self.MENU_BUTTONS)
                self.query_one(f"#{self.MENU_BUTTONS[novo_idx]}", Button).focus()
                event.prevent_default()

    def action_jogar(self) -> None:
        self.app.push_screen(GameScreen(self.app.selected_category))

    def action_categorias(self) -> None:
        self.app.push_screen(CategoryScreen())

    def action_sobre(self) -> None:
        self.app.push_screen(AboutModal())

    def action_sair(self) -> None:
        self.app.exit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-jogar":
            self.action_jogar()
        elif event.button.id == "btn-categorias":
            self.action_categorias()
        elif event.button.id == "btn-sobre":
            self.action_sobre()
        elif event.button.id == "btn-sair":
            self.action_sair()


# ==========================================
# APLICAÇÃO PRINCIPAL (TEXTUAL APP)
# ==========================================
class ForcaApp(App):
    """Aplicação Textual da Forca."""

    CSS_PATH = "styles.tcss"
    TITLE = "Jogo da Forca - SysOps"
    SUB_TITLE = "Textual TUI"

    BINDINGS = [
        Binding("ctrl+escape", "quit_app", "Sair"),
        Binding("ctrl+q", "quit_app", "Sair"),
    ]

    def __init__(self):
        super().__init__()
        self.engine = ForcaEngine(Path(__file__).parent)
        self.selected_category: Optional[Categoria] = None

    def on_mount(self) -> None:
        self.push_screen(MenuScreen())

    def action_quit_app(self) -> None:
        self.exit()


if __name__ == "__main__":
    app = ForcaApp()
    app.run()
