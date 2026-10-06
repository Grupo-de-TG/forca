"""
Mecanismo central de regras de negócio do Jogo da Forca.
"""

from __future__ import annotations
import random
from pathlib import Path
from typing import List, Optional, Tuple

from core.models import Categoria, GameState
from core.normalizer import normalizar_texto


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

    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            base_dir = Path(__file__).parent.parent
        self.listas_dir = base_dir / "listas"
        self.categorias: List[Categoria] = []
        self.carregar_categorias()

    def carregar_categorias(self) -> None:
        """Descobre todos os arquivos txt disponíveis na pasta listas/."""
        self.categorias.clear()
        if not self.listas_dir.exists():
            return

        for f in sorted(self.listas_dir.glob("**/*.txt")):
            try:
                with open(f, "r", encoding="utf-8", errors="ignore") as file:
                    linhas = [l.strip() for l in file if l.strip()]
                    nome_formatado = f.stem.replace("-", " ").replace("_", " ").title()
                    self.categorias.append(Categoria(nome=nome_formatado, arquivo_path=f, total_palavras=len(linhas)))
            except Exception:
                pass

    def sortear_palavra(self, categoria: Optional[Categoria] = None) -> Tuple[str, str, str]:
        """Retorna (categoria_nome, palavra_original, palavra_normalizada)."""
        if not self.categorias:
            return ("Geral", "computador", "computador")

        cat_escolhida = categoria if categoria else random.choice(self.categorias)

        with open(cat_escolhida.arquivo_path, "r", encoding="utf-8", errors="ignore") as f:
            linhas = [l.strip() for l in f if l.strip()]

        if not linhas:
            return (cat_escolhida.nome, "terminal", "terminal")

        palavra_original = random.choice(linhas)
        palavra_norm = normalizar_texto(palavra_original)
        return (cat_escolhida.nome, palavra_original, palavra_norm)

    def novo_jogo(self, categoria: Optional[Categoria] = None) -> GameState:
        cat_nome, original, norm = self.sortear_palavra(categoria)
        return GameState(
            categoria_nome=cat_nome,
            palavra_original=original,
            palavra_normalizada=norm,
            tentativas_restantes=6,
            letras_certas=[],
            letras_erradas=[],
            mensagem="Bora começar! Navegue com as setas ou digite uma letra e tecle Enter.",
        )

    def processar_tentativa(self, state: GameState, tentativa: str) -> Tuple[GameState, str]:
        """
        Processa uma tentativa de letra.
        Retorna (state atualizado, tipo_feedback: 'acerto' | 'erro' | 'repetida' | 'invalido')
        """
        if state.fim_de_jogo:
            return state, "invalido"

        tentativa = normalizar_texto(tentativa)

        if len(tentativa) != 1 or not tentativa.isalpha():
            state.mensagem = "Digite apenas uma letra válida (A-Z)."
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
