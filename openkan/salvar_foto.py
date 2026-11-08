"""Gravação das fotos e pastas de mídia do OpenKan.

Fotos: PNG ou JPEG, salvas por padrão em <Imagens>/OpenKan (a pasta pode ser
trocada na interface; a escolha fica no QSettings e é passada no parâmetro
`pasta`) com redimensionamento opcional (lado máximo). O salvamento pode ser
feito em segundo plano pela thread FotoTrabalho, para a interface nunca
travar ao salvar PNG grande. Vídeos: pasta escolhida (padrão <Vídeos>/OpenKan,
calculada por pasta_videos).
"""

from __future__ import annotations

import os
import subprocess
from datetime import datetime

import cv2
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal

QUALIDADE_JPEG = 95


def _pasta_xdg(codigo: str, candidatos: list[str]) -> str:
    pasta = ""
    try:
        resultado = subprocess.run(
            ["xdg-user-dir", codigo],
            capture_output=True, text=True, timeout=2,
        )
        pasta = resultado.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pasta = ""
    if pasta and os.path.isdir(pasta):
        return pasta
    for candidato in candidatos:
        caminho = os.path.expanduser(candidato)
        if os.path.isdir(caminho):
            return caminho
    # devolve o preferido mesmo se não existir ainda (SEMPRE expandido —
    # um "~/Vídeos" literal criaria uma pasta "./~/Vídeos" no diretório atual)
    return os.path.expanduser(candidatos[0])


def pasta_fotos(pasta_custom: str | None = None) -> str:
    """Pasta de fotos: a escolhida pelo usuário ou <Imagens>/OpenKan."""
    if pasta_custom:
        os.makedirs(pasta_custom, exist_ok=True)
        return pasta_custom
    base = _pasta_xdg("PICTURES", ["~/Imagens", "~/Pictures"])
    destino = os.path.join(base, "OpenKan")
    os.makedirs(destino, exist_ok=True)
    return destino


def pasta_videos(pasta_custom: str | None = None) -> str:
    """Pasta de vídeos: a escolhida pelo usuário ou <Vídeos>/OpenKan."""
    if pasta_custom:
        os.makedirs(pasta_custom, exist_ok=True)
        return pasta_custom
    base = _pasta_xdg("VIDEOS", ["~/Vídeos", "~/Videos"])
    destino = os.path.join(base, "OpenKan")
    os.makedirs(destino, exist_ok=True)
    return destino


def extensao_de(formato: str) -> str:
    return ".jpg" if formato.lower() in ("jpg", "jpeg") else ".png"


def nome_foto(formato: str = "png") -> str:
    """Nome de arquivo padrão, com data e hora: foto_20261108_153000.png."""
    return datetime.now().strftime("foto_%Y%m%d_%H%M%S") + extensao_de(formato)


def reduzir_para_max(quadro: np.ndarray, lado_max: int) -> np.ndarray:
    """Reduz o quadro (mantendo proporção) se o lado maior exceder lado_max."""
    altura, largura = quadro.shape[:2]
    maior = max(altura, largura)
    if lado_max <= 0 or maior <= lado_max:
        return quadro
    fator = lado_max / maior
    return cv2.resize(
        quadro,
        (int(largura * fator), int(altura * fator)),
        interpolation=cv2.INTER_AREA,
    )


def _gravar_bytes(caminho: str, quadro: np.ndarray) -> str:
    extensao = os.path.splitext(caminho)[1].lower()
    if extensao in (".jpg", ".jpeg"):
        ok, buffer = cv2.imencode(
            ".jpg", quadro, [int(cv2.IMWRITE_JPEG_QUALITY), QUALIDADE_JPEG]
        )
    else:
        ok, buffer = cv2.imencode(".png", quadro)
    if not ok:
        raise RuntimeError("falha ao codificar a imagem")
    pasta = os.path.dirname(caminho)
    if pasta:
        os.makedirs(pasta, exist_ok=True)
    with open(caminho, "wb") as saida:
        saida.write(buffer.tobytes())
    return caminho


def salvar_em(caminho: str, quadro: np.ndarray) -> str:
    """Salva o quadro no caminho indicado (extensão define PNG/JPEG)."""
    return _gravar_bytes(caminho, quadro)


def salvar_foto(quadro: np.ndarray, formato: str = "png", lado_max: int = 0,
                pasta: str | None = None) -> str:
    """Salva na pasta indicada (ou padrão) com nome automático; devolve o caminho."""
    quadro = reduzir_para_max(quadro, lado_max)
    return _gravar_bytes(
        os.path.join(pasta_fotos(pasta), nome_foto(formato)), quadro
    )


class FotoTrabalho(QThread):
    """Salva uma foto em segundo plano (não trava a interface)."""

    concluida = pyqtSignal(str)   # caminho salvo
    falhou = pyqtSignal(str)      # mensagem de erro

    def __init__(self, quadro: np.ndarray, formato: str = "png",
                 lado_max: int = 0, caminho: str | None = None,
                 pasta: str | None = None, parent=None) -> None:
        super().__init__(parent)
        self._quadro = quadro.copy()
        self._formato = formato
        self._lado_max = lado_max
        self._caminho = caminho
        self._pasta = pasta

    def run(self) -> None:
        try:
            if self._caminho:
                caminho = salvar_em(self._caminho, reduzir_para_max(self._quadro, self._lado_max))
            else:
                caminho = salvar_foto(self._quadro, self._formato, self._lado_max,
                                      pasta=self._pasta)
            self.concluida.emit(caminho)
        except Exception as exc:  # noqa: BLE001
            self.falhou.emit(str(exc))
