"""
Controlador de navegação linear para menus e botões.
Implementa IController.
"""

from __future__ import annotations
from typing import List, Optional
from interfaces.controller import IController


class MenuController(IController):
    """
    Gerencia navegação sequencial entre botões de menu ou modais.
    """

    def __init__(self, button_ids: List[str]):
        if not button_ids:
            raise ValueError("button_ids não pode ser vazio.")
        self.button_ids = button_ids
        self.current_idx = 0

    def move_up(self) -> str:
        self.current_idx = (self.current_idx - 1) % len(self.button_ids)
        return self.get_current_target_id()

    def move_down(self) -> str:
        self.current_idx = (self.current_idx + 1) % len(self.button_ids)
        return self.get_current_target_id()

    def move_left(self) -> str:
        return self.move_up()

    def move_right(self) -> str:
        return self.move_down()

    def get_current_target_id(self) -> str:
        return self.button_ids[self.current_idx]

    def reset(self) -> None:
        self.current_idx = 0
