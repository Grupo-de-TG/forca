"""
Aplicação Textual TUI do Jogo da Forca - SysOps Edition.
Transcreve e expande o projeto forca.sh com telas, modais e componentes reativos.
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Optional, List

from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, Grid
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
    """Modal para arriscar a palavra inteira (o comando ! do forca.sh)."""

    def compose(self) -> ComposeResult:
        with Container(classes="modal-dialog"):
            yield Label("🎯 CHUTE ALL-IN", classes="modal-title")
            yield Static(
                "Atenção: Se acertar, você vence na hora!\n"
                "Se errar a palavra, você é enforcado imediatamente.",
                id="chute-aviso",
            )
            yield Input(placeholder="Digite a palavra completa...", id="chute-input")
            with Horizontal(classes="modal-buttons"):
                yield Button("Confirmar Chute", id="btn-confirmar-chute", variant="warning")
                yield Button("Cancelar", id="btn-cancelar-chute", variant="default")

    def on_mount(self) -> None:
        # Foca automaticamente no campo de texto
        self.query_one("#chute-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        val = event.value.strip()
        if val:
            self.dismiss(val)
        else:
            self.dismiss(None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-confirmar-chute":
            val = self.query_one("#chute-input", Input).value.strip()
            self.dismiss(val if val else None)
        elif event.button.id == "btn-cancelar-chute":
            self.dismiss(None)

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.dismiss(None)


# ==========================================
# MODAL: FIM DE JOGO (VITÓRIA OU DERROTA)
# ==========================================
class GameOverModal(ModalScreen[str]):
    """Modal exibido ao finalizar a partida."""

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
                yield Button("Trocar Categoria [C]", id="btn-cat", variant="primary")
                yield Button("Menu Principal [M]", id="btn-menu", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-replay":
            self.dismiss("replay")
        elif event.button.id == "btn-cat":
            self.dismiss("categories")
        elif event.button.id == "btn-menu":
            self.dismiss("menu")

    def on_key(self, event: events.Key) -> None:
        if event.key in ("enter", "space"):
            self.dismiss("replay")
        elif event.key == "c":
            self.dismiss("categories")
        elif event.key in ("m", "escape"):
            self.dismiss("menu")


# ==========================================
# MODAL: SOBRE / REGRAS
# ==========================================
class AboutModal(ModalScreen[None]):
    """Modal com informações do projeto e créditos."""

    def compose(self) -> ComposeResult:
        with Container(classes="modal-dialog"):
            yield Label("ℹ️ SOBRE O PROJETO", classes="modal-title")
            yield Static(
                "🎮 [b]Jogo da Forca - SysOps Edition[/b]\n\n"
                "• [b]Autor:[/b] Ryan Henrique Bezerra da Silva\n"
                "• [b]Tecnologias:[/b] Python + Textual (TUI Moderna)\n"
                "• [b]Origem:[/b] Projeto de Sistemas Operacionais II migrado de Shell Script (forca.sh)\n"
                "• [b]Atalhos:[/b]\n"
                "  - Letras [A-Z]: Chutar letra\n"
                "  - [!]: Chutar palavra inteira (All-In)\n"
                "  - [R]: Reiniciar partida\n"
                "  - [Esc]: Voltar / Sair\n",
                id="about-text"
            )
            with Horizontal(classes="modal-buttons"):
                yield Button("Fechar [Enter / Esc]", id="btn-close-about", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)

    def on_key(self, event: events.Key) -> None:
        if event.key in ("enter", "escape", "space"):
            self.dismiss(None)


# ==========================================
# TELA: SELEÇÃO DE CATEGORIAS
# ==========================================
class CategoryScreen(Screen):
    """Tela para selecionar a categoria de palavras."""

    BINDINGS = [
        Binding("escape", "voltar", "Voltar"),
        Binding("enter", "confirmar", "Confirmar"),
    ]

    def compose(self) -> ComposeResult:
        with Container(id="category-container"):
            yield Label("📂 ESCOLHA UMA CATEGORIA", id="menu-title")
            yield Static("Selecione um tema de palavras da pasta 'listas/' ou escolha aleatório:", id="menu-subtitle")
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

        # Seleciona o primeiro
        option_list.highlighted = 0

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
# TELA: JOGO DA FORCA
# ==========================================
class GameScreen(Screen):
    """Tela principal do jogo."""

    BINDINGS = [
        Binding("escape", "menu_principal", "Menu"),
        Binding("exclamation_mark", "chutar_tudo", "Chutar Palavra (!)"),
        Binding("r", "reiniciar", "Reiniciar"),
    ]

    TECLADO_LINHAS = [
        ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
        ["A", "S", "D", "F", "G", "H", "J", "K", "L"],
        ["Z", "X", "C", "V", "B", "N", "M"]
    ]

    def __init__(self, categoria: Optional[Categoria] = None):
        super().__init__()
        self.categoria_inicial = categoria
        self.state: Optional[GameState] = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with Container(id="game-body"):
            # Coluna Esquerda: Desenho da Forca e Vidas
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

                # Teclado Virtual Interativo
                with Vertical(id="teclado-container"):
                    for linha in self.TECLADO_LINHAS:
                        with Horizontal(classes="teclado-linha"):
                            for letra in linha:
                                yield Button(letra, id=f"key-{letra.lower()}", classes="key-btn")

        with Horizontal(id="game-actions"):
            yield Button("🎯 Chutar Palavra (!)", id="btn-chutar", variant="warning", classes="action-btn")
            yield Button("🔄 Nova Palavra [R]", id="btn-nova-palavra", variant="primary", classes="action-btn")
            yield Button("🏠 Menu [Esc]", id="btn-voltar-menu", variant="default", classes="action-btn")

        yield Footer()

    def on_mount(self) -> None:
        self.iniciar_nova_partida(self.categoria_inicial or self.app.selected_category)

    def iniciar_nova_partida(self, categoria: Optional[Categoria] = None) -> None:
        """Inicializa um novo sorteio de palavra e reseta a interface."""
        self.state = self.app.engine.novo_jogo(categoria)
        self.atualizar_ui()
        self.resetar_teclado()

    def atualizar_ui(self) -> None:
        """Sincroniza todos os widgets visuais com o estado atual do jogo."""
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
            btn.disabled = False

    def registrar_letra_no_teclado(self, letra: str, feedback: str) -> None:
        try:
            btn = self.query_one(f"#key-{letra.lower()}", Button)
            btn.disabled = True
            if feedback == "acerto":
                btn.add_class("usada-certa")
            elif feedback == "erro":
                btn.add_class("usada-errada")
        except Exception:
            pass

    def tentar_letra(self, letra: str) -> None:
        if not self.state or self.state.fim_de_jogo:
            return

        self.state, feedback = self.app.engine.processar_tentativa(self.state, letra)
        self.registrar_letra_no_teclado(letra, feedback)
        self.atualizar_ui()

        if self.state.fim_de_jogo:
            self.exibir_modal_fim_de_jogo()

    def action_chutar_tudo(self) -> None:
        if not self.state or self.state.fim_de_jogo:
            return

        def callback_chute(chute: Optional[str]) -> None:
            if chute:
                self.state, acertou = self.app.engine.processar_chute(self.state, chute)
                self.atualizar_ui()
                self.exibir_modal_fim_de_jogo()

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

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""
        if btn_id.startswith("key-"):
            letra = btn_id.replace("key-", "")
            self.tentar_letra(letra)
        elif btn_id == "btn-chutar":
            self.action_chutar_tudo()
        elif btn_id == "btn-nova-palavra":
            self.action_reiniciar()
        elif btn_id == "btn-voltar-menu":
            self.action_menu_principal()

    def on_key(self, event: events.Key) -> None:
        # Pressionar "!" abre o modal de chute
        if event.character == "!":
            self.action_chutar_tudo()
            return

        # Captura digitação direta no teclado (A-Z ou ç)
        if event.character and (event.character.isalpha() or event.character == "ç"):
            self.tentar_letra(event.character)


# ==========================================
# TELA: MENU PRINCIPAL
# ==========================================
class MenuScreen(Screen):
    """Tela de abertura / Menu Principal."""

    BINDINGS = [
        Binding("enter", "jogar", "Jogar"),
        Binding("c", "categorias", "Categorias"),
        Binding("s", "sobre", "Sobre"),
        Binding("q", "sair", "Sair"),
    ]

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
                yield Button("📂 Escolher Categoria [C]", id="btn-categorias", variant="primary", classes="menu-btn")
                yield Button("ℹ️ Sobre / Regras [S]", id="btn-sobre", variant="default", classes="menu-btn")
                yield Button("🚪 Sair do Jogo [Q]", id="btn-sair", variant="error", classes="menu-btn")

        yield Footer()

    def on_screen_resume(self) -> None:
        self.atualizar_categoria_info()

    def on_mount(self) -> None:
        self.atualizar_categoria_info()

    def atualizar_categoria_info(self) -> None:
        cat = self.app.selected_category
        cat_nome = cat.nome if cat else "Aleatório (Todas as listas)"
        self.query_one("#menu-category-info", Label).update(f"📂 Tema Atual: {cat_nome}")

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

    def __init__(self):
        super().__init__()
        self.engine = ForcaEngine(Path(__file__).parent)
        self.selected_category: Optional[Categoria] = None

    def on_mount(self) -> None:
        self.push_screen(MenuScreen())


if __name__ == "__main__":
    app = ForcaApp()
    app.run()
