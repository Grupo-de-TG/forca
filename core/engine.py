"""
Mecanismo central de regras de negócio do Jogo da Forca.
Consome o IWordRepository desacoplado (Neo4j ou File fallback).
"""

from __future__ import annotations
import random
from pathlib import Path
from typing import List, Optional, Tuple

from interfaces.word_repository import IWordRepository
from interfaces.hint_repository import IHintRepository
from core.models import Categoria, GameState, WordData
from core.normalizer import normalizar_texto
from core.neo4j_word_repository import Neo4jWordRepository
from core.file_word_repository import FileWordRepository
from core.neo4j_hint_repository import Neo4jHintRepository


class ForcaEngine:
    """Gerencia listas de palavras, sorteios e o fluxo de regras das rodadas."""

    FORCA_ARTES = [
        # 0 erros
        """
  +---+
  |   |
      |
      |
      |
      |
=========
        """,
        # 1 erro (cabeça)
        """
  +---+
  |   |
  O   |
      |
      |
      |
=========
        """,
        # 2 erros (tronco)
        """
  +---+
  |   |
  O   |
  |   |
      |
      |
=========
        """,
        # 3 erros (braço esquerdo)
        """
  +---+
  |   |
  O   |
 /|   |
      |
      |
=========
        """,
        # 4 erros (braço direito)
        """
  +---+
  |   |
  O   |
 /|\\  |
      |
      |
=========
        """,
        # 5 erros (perna esquerda)
        """
  +---+
  |   |
  O   |
 /|\\  |
 /    |
      |
=========
        """,
        # 6 erros (perna direita - enforcado)
        """
  +---+
  |   |
  O   |
 /|\\  |
 / \\  |
      |
=========
        """
    ]

    def __init__(
        self,
        word_repo: IWordRepository,
        hint_repo: Optional[IHintRepository] = None
    ):
        self.word_repo = word_repo
        self.hint_repo = hint_repo if hint_repo is not None else Neo4jHintRepository()

    @property
    def categorias(self) -> List[Categoria]:
        return self.word_repo.list_themes()

    def sortear_palavra(self, categoria: Optional[Categoria] = None) -> Tuple[str, str, str]:
        """Retorna (categoria_nome, palavra_original, palavra_normalizada)."""
        categorias_disponiveis = self.categorias
        if not categorias_disponiveis:
            return ("Geral", "computador", "computador")

        # 1. O Python sorteia a categoria caso nenhuma tenha sido selecionada:
        cat_escolhida = categoria if categoria else random.choice(categorias_disponiveis)

        # 2. Pede a palavra da categoria ao repositório:
        word_data = self.word_repo.get_random_word(theme_id=cat_escolhida.id)
        if word_data:
            return (word_data.theme_name, word_data.text, word_data.normalized)
        return (cat_escolhida.nome, "computador", "computador")

    def novo_jogo(self, categoria: Optional[Categoria] = None) -> GameState:
        cat_nome, original, norm = self.sortear_palavra(categoria)
        dicas = []
        if self.hint_repo:
            try:
                dicas = self.hint_repo.get_hints(norm)
            except Exception:
                dicas = []

        if cat_nome == "Conjugações" and not any("conjugação" in d.lower() for d in dicas):
            dicas.insert(0, "É uma conjugação verbal da língua portuguesa")

        return GameState(
            categoria_nome=cat_nome,
            palavra_original=original,
            palavra_normalizada=norm,
            tentativas_restantes=6,
            letras_certas=[],
            letras_erradas=[],
            mensagem="Bora começar! Digite uma letra no teclado e tecle Enter.",
            dicas=dicas,
        )

    def processar_tentativa(self, state: GameState, tentativa: str) -> Tuple[GameState, str]:
        """
        Processa uma tentativa de letra.
        Retorna (state atualizado, tipo_feedback: 'acerto' | 'erro' | 'repetida' | 'invalido')
        """
        if state.fim_de_jogo:
            return state, "invalido"

        tentativa = normalizar_texto(tentativa)

        if len(tentativa) != 1 or not (tentativa.isalpha() or tentativa == "ç"):
            state.mensagem = "Digite apenas uma letra válida (A-Z ou Ç)."
            return state, "invalido"

        if tentativa in state.todas_tentativas:
            state.mensagem = f"Você já tentou a letra '{tentativa.upper()}'."
            return state, "repetida"

        letras_unicas_palavra = set(c for c in state.palavra_normalizada if c.isalpha())

        if tentativa in letras_unicas_palavra:
            state.letras_certas.append(tentativa)
            state.mensagem = f"Boa! A letra '{tentativa.upper()}' está na palavra."
            feedback = "acerto"
        else:
            state.letras_erradas.append(tentativa)
            state.tentativas_restantes -= 1
            state.mensagem = f"Ops! A letra '{tentativa.upper()}' não está na palavra."
            feedback = "erro"

        # Verifica vitória por letras
        acertou_tudo = all(c in state.letras_certas or not c.isalpha() for c in state.palavra_normalizada)
        if acertou_tudo:
            state.venceu = True
            state.fim_de_jogo = True
            state.mensagem = f"🎉 Parabéns! Você descobriu a palavra: {state.palavra_original}"
        elif state.tentativas_restantes <= 0:
            state.venceu = False
            state.fim_de_jogo = True
            state.mensagem = f"💀 Fim de jogo! A palavra era: {state.palavra_original}"

        return state, feedback

    def processar_chute(self, state: GameState, chute: str) -> Tuple[GameState, bool]:
        """Processa um chute da palavra completa (All-in)."""
        if state.fim_de_jogo:
            return state, False

        chute_norm = normalizar_texto(chute)
        state.chute_usado = True
        state.fim_de_jogo = True

        if chute_norm == state.palavra_normalizada:
            state.venceu = True
            for c in state.palavra_normalizada:
                if c.isalpha() and c not in state.letras_certas:
                    state.letras_certas.append(c)
            state.mensagem = f"🎯 Chute certeiro! Você acertou: {state.palavra_original}"
            return state, True
        else:
            state.venceu = False
            state.tentativas_restantes = 0
            state.mensagem = f"❌ Chute incorreto ({chute})! A palavra era: {state.palavra_original}"
            return state, False

    def obter_arte_forca(self, erros: int) -> str:
        indice = max(0, min(erros, len(self.FORCA_ARTES) - 1))
        return self.FORCA_ARTES[indice]
