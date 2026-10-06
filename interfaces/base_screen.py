"""
Classe base abstrata para telas da aplicação Forca (POO).
"""

from __future__ import annotations
from textual.screen import Screen


class BaseGameScreen(Screen):
    """Contrato e base para telas de jogo com navegação por teclado e setas."""

    def on_navigation_left(self) -> None:
        """Trata navegação para a esquerda."""
        pass

    def on_navigation_right(self) -> None:
        """Trata navegação para a direita."""
        pass

    def on_navigation_up(self) -> None:
        """Trata navegação para cima."""
        pass

    def on_navigation_down(self) -> None:
        """Trata navegação para baixo."""
        pass

    def on_action_confirm(self) -> None:
        """Trata a confirmação via tecla Enter."""
        pass
