"""
Interface base para controladores de navegação e entrada de usuário (POO).
"""

from __future__ import annotations
from typing import Optional


class IController:
    """Contrato base para qualquer controlador de navegação por teclado/foco."""

    def move_up(self) -> Optional[str]:
        """Move o cursor para cima e retorna o ID do elemento focado."""
        raise NotImplementedError

    def move_down(self) -> Optional[str]:
        """Move o cursor para baixo e retorna o ID do elemento focado."""
        raise NotImplementedError

    def move_left(self) -> Optional[str]:
        """Move o cursor para a esquerda e retorna o ID do elemento focado."""
        raise NotImplementedError

    def move_right(self) -> Optional[str]:
        """Move o cursor para a direita e retorna o ID do elemento focado."""
        raise NotImplementedError

    def get_current_target_id(self) -> str:
        """Retorna o ID do widget atualmente selecionado no controlador."""
        raise NotImplementedError

    def reset(self) -> None:
        """Reseta a posição do cursor para o estado inicial."""
        raise NotImplementedError
