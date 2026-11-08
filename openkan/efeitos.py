"""Filtros de efeito em tempo real do OpenKan.

Cada efeito é uma função que recebe um quadro BGR (numpy.ndarray) e devolve
um quadro BGR do mesmo tamanho e tipo. A grade de efeitos da interface é
construída a partir da lista EFEITOS — para adicionar um filtro novo, basta
escrever a função e acrescentar uma tupla ("chave", "Nome", funcao) na lista.
"""

from __future__ import annotations

import cv2
import numpy as np


def aplicar_original(frame: np.ndarray) -> np.ndarray:
    """Sem efeito: devolve o quadro como chegou."""
    return frame


def aplicar_espelho(frame: np.ndarray) -> np.ndarray:
    """Espelha o quadro na horizontal (efeito 'selfie')."""
    return cv2.flip(frame, 1)


def aplicar_cinza(frame: np.ndarray) -> np.ndarray:
    """Converte para preto e branco."""
    cinza = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.cvtColor(cinza, cv2.COLOR_GRAY2BGR)


def aplicar_sepia(frame: np.ndarray) -> np.ndarray:
    """Tonalização sépia clássica (matriz de mistura de canais)."""
    matriz = np.array(
        [
            [0.131, 0.534, 0.272],
            [0.168, 0.686, 0.349],
            [0.189, 0.769, 0.393],
        ],
        dtype=np.float32,
    )
    sepia = cv2.transform(frame.astype(np.float32), matriz)
    return np.clip(sepia, 0, 255).astype(np.uint8)


def aplicar_negativo(frame: np.ndarray) -> np.ndarray:
    """Inverte as cores do quadro."""
    return cv2.bitwise_not(frame)


def aplicar_desfoque(frame: np.ndarray) -> np.ndarray:
    """Desfoque gaussiano suave."""
    return cv2.GaussianBlur(frame, (0, 0), sigmaX=8.0)


def aplicar_calor(frame: np.ndarray) -> np.ndarray:
    """Mapa de cores 'câmera térmica' a partir da luminância."""
    cinza = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.applyColorMap(cinza, cv2.COLORMAP_JET)


def aplicar_cartoon(frame: np.ndarray) -> np.ndarray:
    """Efeito cartoon: aplatir cores + contornos escuros.

    O processamento pesado (bilateral) é feito em uma cópia reduzida do
    quadro (largura ~480 px) e o resultado é ampliado de volta, mantendo o
    custo baixo mesmo em câmeras de alta resolução.
    """
    altura, largura = frame.shape[:2]
    escala = min(1.0, 480.0 / max(largura, 1))
    if escala < 1.0:
        pequeno = cv2.resize(
            frame,
            (int(largura * escala), int(altura * escala)),
            interpolation=cv2.INTER_AREA,
        )
    else:
        pequeno = frame

    cinza = cv2.cvtColor(pequeno, cv2.COLOR_BGR2GRAY)
    cinza = cv2.medianBlur(cinza, 5)
    arestas = cv2.adaptiveThreshold(
        cinza, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9
    )
    suave = cv2.bilateralFilter(pequeno, 9, 200, 200)
    desenho = cv2.bitwise_and(suave, suave, mask=arestas)

    if escala < 1.0:
        desenho = cv2.resize(desenho, (largura, altura), interpolation=cv2.INTER_LINEAR)
    return desenho


def aplicar_pixel(frame: np.ndarray) -> np.ndarray:
    """Pixelado: reduz e amplia com interpolação 'serrilhada'."""
    altura, largura = frame.shape[:2]
    fator = max(1.0, min(largura, altura) / 60.0)
    pequeno = cv2.resize(
        frame, (max(1, int(largura / fator)), max(1, int(altura / fator))),
        interpolation=cv2.INTER_LINEAR,
    )
    return cv2.resize(pequeno, (largura, altura), interpolation=cv2.INTER_NEAREST)


def aplicar_vinheta(frame: np.ndarray) -> np.ndarray:
    """Vinheta: escurece as bordas do quadro (máscara radial)."""
    altura, largura = frame.shape[:2]
    eixo_x = np.linspace(-1.0, 1.0, largura, dtype=np.float32)
    eixo_y = np.linspace(-1.0, 1.0, altura, dtype=np.float32)
    grade_x, grade_y = np.meshgrid(eixo_x, eixo_y)
    mascara = 1.0 - np.clip(1.35 * (grade_x ** 2 + grade_y ** 2) ** 0.75, 0.0, 1.0)
    return np.clip(frame.astype(np.float32) * mascara[:, :, None], 0, 255).astype(np.uint8)


def aplicar_neon(frame: np.ndarray) -> np.ndarray:
    """Neon: contornos em vermelho sobre fundo escuro."""
    cinza = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    arestas = cv2.Canny(cinza, 60, 160)
    fundo = np.full_like(frame, 12)
    fundo[:, :, 2] = 26  # leve tinta vermelha no fundo (BGR)
    brilho = np.zeros_like(frame)
    brilho[:, :, 2] = arestas  # vermelho sangue
    brilho[:, :, 1] = (arestas * 0.18).astype(np.uint8)
    return cv2.add(fundo, brilho)


def aplicar_scanlines(frame: np.ndarray) -> np.ndarray:
    """Scanlines: linhas escuras alternadas, estilo monitor de tubo."""
    resultado = frame.copy()
    resultado[::2, :, :] = (resultado[::2, :, :] * 0.45).astype(np.uint8)
    return resultado


# ------------------------------------------------ ajustes por software
# Funcionam com QUALQUER câmera — inclusive as virtuais (Iriun, DroidCam,
# v4l2loopback), que não expõem controles de hardware no driver.

def aplicar_ajustes(quadro: np.ndarray, ajustes: dict | None = None) -> np.ndarray:
    """Ajustes de imagem por software, aplicados na ordem:
    contraste/brilho → saturação → ganho digital (ISO).

    Valores neutros não custam nada (a função retorna o quadro sem tocar nele).
    """
    a = ajustes or {}
    ganho = float(a.get("ganho", 1.0))
    brilho = float(a.get("brilho", 0.0))
    contraste = float(a.get("contraste", 1.0))
    saturacao = float(a.get("saturacao", 1.0))

    saida = quadro
    if contraste != 1.0 or brilho != 0.0:
        saida = cv2.convertScaleAbs(saida, alpha=contraste, beta=brilho)
    if saturacao != 1.0:
        hsv = cv2.cvtColor(saida, cv2.COLOR_BGR2HSV)
        hsv[:, :, 1] = cv2.convertScaleAbs(hsv[:, :, 1], alpha=saturacao, beta=0)
        saida = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    if ganho != 1.0:
        saida = cv2.convertScaleAbs(saida, alpha=ganho, beta=0)
    return saida


# ------------------------------------------------ efeito temporal

_PESO_NOVO = 0.35  # fração do quadro novo na média (menor = rastro mais longo)
_ACUM_EL: np.ndarray | None = None


def aplicar_exposicao_longa(frame: np.ndarray) -> np.ndarray:
    """Simula obturador lento: média contínua dos últimos quadros.

    Como um driver V4L2 quase nunca permite tempo de exposição real acima do
    suportado pelo sensor, este efeito emula o resultado (rastros de luz e
    movimento borrado) misturando os quadros recentes — funciona até em
    câmeras virtuais como o Iriun.
    """
    global _ACUM_EL
    if _ACUM_EL is None or _ACUM_EL.shape != frame.shape:
        _ACUM_EL = frame.astype(np.float32)
        return frame
    cv2.accumulateWeighted(frame, _ACUM_EL, _PESO_NOVO)
    return np.clip(_ACUM_EL, 0, 255).astype(np.uint8)


def redefinir_temporais() -> None:
    """Zera o estado dos efeitos temporais (troca de efeito ou de câmera)."""
    global _ACUM_EL
    _ACUM_EL = None


# Ordem exibida na grade de efeitos da interface.
# Tuplas: (chave_interna, chave_de_traducao, funcao) — os nomes vêm do módulo
# traducao ("efeito.<chave>"), então a grade fica bilíngue automaticamente.
EFEITOS: list[tuple[str, str, callable]] = [
    ("original", "efeito.original", aplicar_original),
    ("espelho", "efeito.espelho", aplicar_espelho),
    ("cinza", "efeito.cinza", aplicar_cinza),
    ("sepia", "efeito.sepia", aplicar_sepia),
    ("negativo", "efeito.negativo", aplicar_negativo),
    ("desfoque", "efeito.desfoque", aplicar_desfoque),
    ("cartoon", "efeito.cartoon", aplicar_cartoon),
    ("calor", "efeito.calor", aplicar_calor),
    ("pixel", "efeito.pixel", aplicar_pixel),
    ("vinheta", "efeito.vinheta", aplicar_vinheta),
    ("neon", "efeito.neon", aplicar_neon),
    ("scanlines", "efeito.scanlines", aplicar_scanlines),
    # último — índices ficam gravados nas preferências do usuário
    ("exposicao_longa", "efeito.exposicao_longa", aplicar_exposicao_longa),
]

INDICE_ORIGINAL = 0


def aplicar_efeito(frame: np.ndarray, indice: int) -> np.ndarray:
    """Aplica o efeito de índice `indice` (0 = sem efeito)."""
    if indice <= 0 or indice >= len(EFEITOS):
        return frame
    return EFEITOS[indice][2](frame)
