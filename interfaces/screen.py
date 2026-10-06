"""
Interface base para telas da aplicação (POO via Protocol).
"""

from __future__ import annotations
from typing import Protocol, runtime_checkable


@runtime_checkable
class IScreen(Protocol):
    """Contrato que define comportamentos de navegação e ação de uma tela da Forca."""

    def on_navigation_left(self) -> None:
        """Trata navegação para a esquerda."""
        ...

    def on_navigation_right(self) -> None:
        """Trata navegação para a direita."""
        ...

    def on_navigation_up(self) -> None:
        """Trata navegação para cima."""
        ...

    def on_navigation_down(self) -> None:
        """Trata navegação para baixo."""
        ...

    def on_action_confirm(self) -> None:
        """Trata a confirmação via tecla Enter."""
        ...
