"""
Módulo de detecção e cálculo de orientação de tela (Horizontal vs Vertical).
Inspirado na lógica de proporção/aspect ratio do Variety / HydraPaper.
"""

from __future__ import annotations
from enum import Enum


class OrientationType(str, Enum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class OrientationDetector:
    """
    Calcula a orientação ideal (Horizontal vs Vertical) com base nas dimensões da janela.
    Leva em conta a proporção física dos caracteres do terminal (~2 colunas por 1 linha).
    """

    # Fator de correção de aspect ratio de caracteres de terminal (altura da célula ~= 2x largura)
    TERMINAL_CHAR_ASPECT: float = 2.0

    # Ponto de corte para transição de layout
    # Abaixo dessa proporção física largura/altura ou abaixo de 95 colunas -> Modo Vertical
    ASPECT_RATIO_THRESHOLD: float = 1.15
    MIN_HORIZONTAL_WIDTH: int = 95

    @classmethod
    def detect(cls, width: int, height: int) -> OrientationType:
        """
        Retorna OrientationType.VERTICAL se a janela for estreita/alta,
        ou OrientationType.HORIZONTAL se for widescreen/larga.
        """
        if width <= 0 or height <= 0:
            return OrientationType.HORIZONTAL

        # Largura absoluta mínima para comportar a forca lado a lado com o teclado
        if width < cls.MIN_HORIZONTAL_WIDTH:
            return OrientationType.VERTICAL

        # Proporção geométrica ajustada pela densidade de caracteres
        # normalized_aspect = (largura_pixels) / (altura_pixels)
        normalized_aspect = (width / 2.0) / float(height)

        if normalized_aspect < cls.ASPECT_RATIO_THRESHOLD:
            return OrientationType.VERTICAL

        return OrientationType.HORIZONTAL
