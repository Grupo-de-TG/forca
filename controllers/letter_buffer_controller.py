"""
Controlador de buffer de letra e navegação de foco entre o slot de entrada e os botões de ação (POO).
Implementa IController com navegação bidimensional entre o slot de letra e a barra de ações.
"""

from __future__ import annotations
from typing import List, Optional
from interfaces.controller import IController


class LetterBufferController(IController):
    """
    Gerencia o foco hierárquico entre o slot de letra (Linha 0)
    e os botões de ação (Linha 1), além do buffer de digitação.
    """

    SLOT_ID: str = "slot-letra"
    ACTION_BUTTONS: List[str] = ["btn-chutar", "btn-nova-palavra", "btn-voltar-menu"]

    def __init__(self):
        self.candidate_letter: Optional[str] = None
        self.current_row: int = 0  # 0 = slot de letra, 1 = botões de ação
        self.action_idx: int = 0   # Índice do botão na linha 1

    def set_candidate(self, letter: str) -> None:
        """Define a letra atualmente digitada e direciona o foco para o slot."""
        if letter and letter.isalpha():
            self.candidate_letter = letter.upper()
            self.current_row = 0  # Garante que o foco está no slot

    def clear_candidate(self) -> None:
        """Limpa o buffer de letra candidata."""
        self.candidate_letter = None

    def get_candidate(self) -> Optional[str]:
        """Retorna a letra candidata atual ou None."""
        return self.candidate_letter

    def has_candidate(self) -> bool:
        """Indica se há uma letra pendente de confirmação."""
        return self.candidate_letter is not None

    def is_on_letter_slot(self) -> bool:
        """Retorna True se o foco estiver na área de inserção de letra."""
        return self.current_row == 0

    def is_on_action_button(self) -> bool:
        """Retorna True se o foco estiver nos botões de ação."""
        return self.current_row == 1

    def focus_letter_slot(self) -> str:
        """Move o foco diretamente para o slot de letra."""
        self.current_row = 0
        return self.SLOT_ID

    def move_up(self) -> str:
        """Seta para cima: sobe dos botões de ação para o slot de letra."""
        self.current_row = 0
        return self.get_current_target_id()

    def move_down(self) -> str:
        """Seta para baixo: desce do slot de letra para os botões de ação."""
        self.current_row = 1
        return self.get_current_target_id()

    def move_left(self) -> str:
        """Seta para a esquerda: navega entre botões se estiver na linha 1."""
        if self.current_row == 1:
            self.action_idx = (self.action_idx - 1) % len(self.ACTION_BUTTONS)
        return self.get_current_target_id()

    def move_right(self) -> str:
        """Seta para a direita: navega entre botões se estiver na linha 1."""
        if self.current_row == 1:
            self.action_idx = (self.action_idx + 1) % len(self.ACTION_BUTTONS)
        return self.get_current_target_id()

    def get_current_target_id(self) -> str:
        if self.current_row == 0:
            return self.SLOT_ID
        return self.ACTION_BUTTONS[self.action_idx]

    def reset(self) -> None:
        self.candidate_letter = None
        self.current_row = 0
        self.action_idx = 0
