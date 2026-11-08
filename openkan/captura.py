"""Threads do OpenKan: busca de câmeras e captura de vídeo.

CameraWorker
    Roda em uma QThread própria: abre a câmera com OpenCV/V4L2, aplica o
    efeito escolhido + ajustes de imagem por software (ganho/brilho/
    contraste/saturação) + orientação (rotação/espelhamento) e publica SEMPRE
    o quadro mais recente em um buffer protegido por trava. A interface
    consome esse buffer com um QTimer — esse desenho evita atraso acumulado
    quando a câmera entrega quadros mais rápido do que a interface renderiza.
    Também mede o qps real da câmera (usado como timebase da gravação),
    entrega cada quadro processado a um "receptor" opcional (o gravador) e
    pode pedir uma taxa de quadros específica ao driver (qps_alvo).

ProcuraCameras / LeitorControles
    Trabalhos de fundo curtos: sonda os nós /dev/video* e lê os controles
    V4L2 fora da thread de interface.
"""

from __future__ import annotations

import threading
import time

import cv2
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal

from . import cameras, controles_v4l2, efeitos

RESOLUCAO_PADRAO = (1280, 720)
QPS_DESEJADO = 30
FALHAS_SEGUIDAS_PARA_DESISTIR = 60  # ~2 s em uma câmera de 30 qps


def aplicar_orientacao(quadro: np.ndarray, rotacao: int,
                       espelhar_h: bool, espelhar_v: bool) -> np.ndarray:
    """Aplica rotação (0/90/180/270) e espelhamentos ao quadro."""
    resultado = quadro
    if rotacao == 90:
        resultado = cv2.rotate(resultado, cv2.ROTATE_90_CLOCKWISE)
    elif rotacao == 180:
        resultado = cv2.rotate(resultado, cv2.ROTATE_180)
    elif rotacao == 270:
        resultado = cv2.rotate(resultado, cv2.ROTATE_90_COUNTERCLOCKWISE)
    if espelhar_h:
        resultado = cv2.flip(resultado, 1)
    if espelhar_v:
        resultado = cv2.flip(resultado, 0)
    return resultado


class CameraWorker(QThread):
    """Captura quadros de uma câmera V4L2 e publica o quadro mais recente.

    `cam` é o dicionário devolvido por cameras.listar_cameras():
    {'caminho': '/dev/video0', 'indice': 0, 'nome': '...'}. A abertura é
    SEMPRE pelo índice numérico (o backend V4L2 do OpenCV não abre por nome).
    """

    camera_pronta = pyqtSignal(str)      # ex.: "1280×720"
    falha = pyqtSignal(str)              # código: 'abrir' | 'quadros' | 'parou'

    def __init__(self, cam: dict, indice_efeito: int = efeitos.INDICE_ORIGINAL,
                 parent=None, qps_alvo: float | None = None) -> None:
        super().__init__(parent)
        self.caminho = cam["caminho"]
        self.indice = cameras.indice_do(self.caminho)
        self.receptor = None  # callable(quadro) — ex.: gravador de vídeo
        self._indice_efeito = indice_efeito
        self._qps_alvo = qps_alvo
        self._ajustes: dict = {
            "ganho": 1.0, "brilho": 0.0, "contraste": 1.0, "saturacao": 1.0,
        }
        self._rotacao = 0
        self._espelhar_h = False
        self._espelhar_v = False
        self._trava = threading.Lock()
        self._executando = True
        self._ultimo_quadro: np.ndarray | None = None
        self._qps_atual = 0.0

    # ---------- API usada pela thread de interface ----------

    def definir_efeito(self, indice: int) -> None:
        """Troca o efeito aplicado aos próximos quadros (seguro entre threads)."""
        with self._trava:
            self._indice_efeito = indice
        efeitos.redefinir_temporais()

    def definir_ajustes(self, ajustes: dict) -> None:
        """Define ganho/brilho/contraste/saturação por software (ao vivo)."""
        with self._trava:
            self._ajustes = dict(ajustes)

    def definir_orientacao(self, rotacao: int, espelhar_h: bool,
                           espelhar_v: bool) -> None:
        with self._trava:
            self._rotacao = rotacao
            self._espelhar_h = espelhar_h
            self._espelhar_v = espelhar_v

    def ultimo_quadro(self) -> np.ndarray | None:
        """Cópia do quadro mais recente capturado (ou None)."""
        with self._trava:
            if self._ultimo_quadro is None:
                return None
            return self._ultimo_quadro.copy()

    def qps_atual(self) -> float:
        """Taxa real de quadros capturados pela câmera."""
        with self._trava:
            return self._qps_atual

    def parar(self) -> None:
        """Pede o encerramento e aguarda até 5 s a thread terminar."""
        self._executando = False
        self.wait(5000)

    # ---------- laço da thread ----------

    def run(self) -> None:
        if self.indice is None:
            self.falha.emit("abrir")
            return
        cap = cv2.VideoCapture(self.indice, cv2.CAP_V4L2)
        if not cap.isOpened():
            self.falha.emit("abrir")
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, RESOLUCAO_PADRAO[0])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, RESOLUCAO_PADRAO[1])
        cap.set(
            cv2.CAP_PROP_FPS,
            float(self._qps_alvo) if self._qps_alvo else QPS_DESEJADO,
        )
        # MJPG permite 30 qps em 720p na maioria das webcams USB.
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        efeitos.redefinir_temporais()

        try:
            ok, quadro = cap.read()
            if not ok:
                self.falha.emit("quadros")
                return

            largura = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            altura = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.camera_pronta.emit(f"{largura}×{altura}")

            falhas_seguidas = 0
            contagem_qps = 0
            marca_qps = time.monotonic()
            while self._executando:
                ok, quadro = cap.read()
                if not ok:
                    falhas_seguidas += 1
                    if falhas_seguidas >= FALHAS_SEGUIDAS_PARA_DESISTIR:
                        self.falha.emit("parou")
                        return
                    continue
                falhas_seguidas = 0

                with self._trava:
                    indice = self._indice_efeito
                    rotacao, esp_h, esp_v = (
                        self._rotacao, self._espelhar_h, self._espelhar_v,
                    )
                    ajustes = dict(self._ajustes)
                processado = efeitos.aplicar_efeito(quadro, indice)
                processado = efeitos.aplicar_ajustes(processado, ajustes)
                processado = aplicar_orientacao(processado, rotacao, esp_h, esp_v)

                with self._trava:
                    self._ultimo_quadro = processado

                if self.receptor is not None:
                    try:
                        self.receptor(processado)
                    except Exception:
                        pass

                # Medição do qps real de captura
                contagem_qps += 1
                agora = time.monotonic()
                if agora - marca_qps >= 1.0:
                    with self._trava:
                        self._qps_atual = contagem_qps / (agora - marca_qps)
                    contagem_qps = 0
                    marca_qps = agora
        finally:
            cap.release()


class ProcuraCameras(QThread):
    """Sonda as câmeras do sistema em segundo plano."""

    cameras_prontas = pyqtSignal(list)  # lista de {'caminho':..., 'nome':...}

    def run(self) -> None:
        try:
            lista = cameras.listar_cameras()
        except Exception:
            lista = []
        self.cameras_prontas.emit(lista)


class LeitorControles(QThread):
    """Lê os controles V4L2 da câmera ativa em segundo plano."""

    controles_prontos = pyqtSignal(str, list)  # (caminho, lista de controles)

    def __init__(self, caminho: str, parent=None) -> None:
        super().__init__(parent)
        self._caminho = caminho

    def run(self) -> None:
        try:
            lista = controles_v4l2.listar_controles(self._caminho)
        except Exception:
            lista = []
        self.controles_prontos.emit(self._caminho, lista)
