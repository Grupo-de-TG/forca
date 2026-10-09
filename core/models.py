"""
Modelos de dados para o Jogo da Forca.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class Categoria:
    id: str
    nome: str
    arquivo_path: Optional[Path] = None
    total_palavras: int = 0
    group: str = "Geral"


@dataclass
class WordData:
    text: str
    normalized: str
    theme_id: str
    theme_name: str


@dataclass
class Player:
    id: int
    name: str
    score: int = 0
    partidas: int = 0
    vitorias: int = 0
    streak_atual: int = 0
    best_streak: int = 0

    @property
    def games_played(self) -> int:
        return self.partidas

    @property
    def games_won(self) -> int:
        return self.vitorias

    @property
    def current_streak(self) -> int:
        return self.streak_atual

    @property
    def win_rate(self) -> float:
        if self.partidas == 0:
            return 0.0
        return (self.vitorias / self.partidas) * 100.0


@dataclass
class MatchRecord:
    id: int
    user_id: int
    username: str
    vencidas: bool
    categoria: str
    palavra: str
    tentativas_restantes: int
    pontos: int
    marca_paco: str

    @property
    def won(self) -> bool:
        return self.vencidas

    @property
    def category_name(self) -> str:
        return self.categoria

    @property
    def word(self) -> str:
        return self.palavra

    @property
    def attempts_left(self) -> int:
        return self.tentativas_restantes

    @property
    def points_earned(self) -> int:
        return self.pontos

    @property
    def played_at(self) -> str:
        return self.marca_paco


@dataclass
class GameState:
    categoria_nome: str
    palavra_original: str
    palavra_normalizada: str
    tentativas_restantes: int = 6
    letras_certas: List[str] = field(default_factory=list)
    letras_erradas: List[str] = field(default_factory=list)
    mensagem: str = "Bora começar! Digite uma letra no teclado e tecle Enter."
    venceu: bool = False
    fim_de_jogo: bool = False
    chute_usado: bool = False
    dicas: List[str] = field(default_factory=list)

    @property
    def erros(self) -> int:
        return 6 - self.tentativas_restantes

    @property
    def total_tentativas_feitas(self) -> int:
        return len(self.todas_tentativas)

    @property
    def dica_atual(self) -> str:
        """Retorna a dica correspondente ao número de letras tentadas."""
        if not self.dicas:
            return "💡 Dica: Sem pistas adicionais no grafo."
        idx = min(self.total_tentativas_feitas, len(self.dicas) - 1)
        total = len(self.dicas)
        return f"💡 Dica ({idx + 1}/{total}): {self.dicas[idx]}"

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
