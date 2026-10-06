"""
Controlador de buffer de letra e navegação de ações (POO).
Implementa IController para entrada de letras via teclado físico com confirmação em Enter.
"""

from __future__ import annotations
from typing import List, Optional
from interfaces.controller import IController


class LetterBufferController(IController):
    """
    Gerencia a letra candidata digitada pelo usuário e a navegação entre botões de ação.
    """

    ACTION_BUTTONS: List[str] = ["btn-chutar", "btn-nova-palavra", "btn-voltar-menu"]

    def __init__(self):
        self.candidate_letter: Optional[str] = None
        self.action_idx: int = 0

    def set_candidate(self, letter: str) -> None:
        """Define a letra atualmente digitada para reflexão antes do Enter."""
        if letter and letter.isalpha():
            self.candidate_letter = letter.upper()

    def clear_candidate(self) -> None:
        """Limpa o buffer de letra candidata."""
        self.candidate_letter = None

    def get_candidate(self) -> Optional[str]:
        """Retorna a letra candidata atual ou None."""
        return self.candidate_letter

    def has_candidate(self) -> bool:
        """Indica se há uma letra pendente de confirmação."""
        return self.candidate_letter is not None

    def move_left(self) -> str:
        self.action_idx = (self.action_idx - 1) % len(self.ACTION_BUTTONS)
        return self.get_current_target_id()

    def move_right(self) -> str:
        self.action_idx = (self.action_idx + 1) % len(self.ACTION_BUTTONS)
        return self.get_current_target_id()

    def move_up(self) -> str:
        return self.move_left()

    def move_down(self) -> str:
        return self.move_right()

    def get_current_target_id(self) -> str:
        return self.ACTION_BUTTONS[self.action_idx]

    def reset(self) -> None:
        self.candidate_letter = None
        self.action_idx = 0
