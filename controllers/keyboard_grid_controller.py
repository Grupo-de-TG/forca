"""
Controlador da matriz 2D do teclado virtual e botões de ação do jogo.
Implementa IController.
"""

from __future__ import annotations
from typing import List, Optional
from interfaces.controller import IController


class KeyboardGridController(IController):
    """
    Gerencia a navegação 2D em grid para o teclado da forca e botões de ação.
    """

    GRID: List[List[str]] = [
        ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"],
        ["a", "s", "d", "f", "g", "h", "j", "k", "l"],
        ["z", "x", "c", "v", "b", "n", "m"],
        ["btn-chutar", "btn-nova-palavra", "btn-voltar-menu"]
    ]

    def __init__(self, initial_row: int = 0, initial_col: int = 0):
        self.row = initial_row
        self.col = initial_col

    def move_up(self) -> str:
        self.row = max(0, self.row - 1)
        max_col = len(self.GRID[self.row]) - 1
        self.col = min(self.col, max_col)
        return self.get_current_target_id()

    def move_down(self) -> str:
        self.row = min(len(self.GRID) - 1, self.row + 1)
        max_col = len(self.GRID[self.row]) - 1
        self.col = min(self.col, max_col)
        return self.get_current_target_id()

    def move_left(self) -> str:
        self.col = max(0, self.col - 1)
        return self.get_current_target_id()

    def move_right(self) -> str:
        max_col = len(self.GRID[self.row]) - 1
        self.col = min(max_col, self.col + 1)
        return self.get_current_target_id()

    def jump_to_letter(self, letter: str) -> Optional[str]:
        """Localiza a letra na matriz e move o cursor diretamente até ela."""
        letra_low = letter.lower()
        for r in range(3):
            if letra_low in self.GRID[r]:
                self.row = r
                self.col = self.GRID[r].index(letra_low)
                return self.get_current_target_id()
        return None

    def get_current_target_id(self) -> str:
        elem = self.GRID[self.row][self.col]
        return elem if elem.startswith("btn-") else f"key-{elem}"

    def get_current_letter(self) -> Optional[str]:
        """Retorna a letra atual selecionada ou None se estiver num botão de ação."""
        if self.row < 3:
            return self.GRID[self.row][self.col].upper()
        return None

    def is_action_button(self) -> bool:
        return self.row == 3

    def reset(self) -> None:
        self.row = 0  # Linha do 'Q'
        self.col = 0  # Letra 'Q'
