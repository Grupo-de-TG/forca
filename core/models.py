"""
Modelos de dados para o Jogo da Forca.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class Categoria:
    nome: str
    arquivo_path: Path
    total_palavras: int = 0


@dataclass
class GameState:
    categoria_nome: str
    palavra_original: str
    palavra_normalizada: str
    tentativas_restantes: int = 6
    letras_certas: List[str] = field(default_factory=list)
    letras_erradas: List[str] = field(default_factory=list)
    mensagem: str = "Bora começar! Navegue com as setas ou digite uma letra e tecle Enter."
    venceu: bool = False
    fim_de_jogo: bool = False
    chute_usado: bool = False

    @property
    def erros(self) -> int:
        return 6 - self.tentativas_restantes

    @property
    def progresso_exibicao(self) -> str:
        """Gera a representação visual da palavra oculta com letras reveladas."""
        res = []
        for char in self.palavra_normalizada:
            if char == " ":
                res.append(" ")
            elif char == "-":
                res.append("-")
            elif char in self.letras_certas:
                res.append(char.upper())
            else:
                res.append("_")
        return " ".join(res)

    @property
    def todas_tentativas(self) -> List[str]:
        return self.letras_certas + self.letras_erradas
