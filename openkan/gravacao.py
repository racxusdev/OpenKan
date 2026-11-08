"""Gravação de vídeo (com áudio opcional) em thread separada.

Fluxo:
    1. A thread de câmera entrega os quadros processados em aceitar_quadro();
    2. GravadorVideo (QThread) escreve os quadros com cv2.VideoWriter em um
       arquivo temporário, enquanto um ffmpeg captura a fonte de áudio
       (PulseAudio/PipeWire) para um WAV;
    3. Ao parar, o áudio é misturado ao vídeo com ffmpeg (-c:v copy, rápido)
       e o arquivo final aparece na pasta de vídeos escolhida
       (padrão: <Vídeos>/OpenKan).

Se não houver ffmpeg ou nenhuma fonte escolhida, grava só o vídeo — sem
interromper o resto. A fila de quadros é limitada: em disco lento, quadros
antigos são descartados em vez de travar a captura (otimização).
"""

from __future__ import annotations

import os
import queue
import shutil
import subprocess
from datetime import datetime

import cv2
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal

from . import traducao
from .salvar_foto import pasta_videos

FOURCC_POR_CONTENEDOR = {
    "mp4": "mp4v", "mkv": "mp4v", "webm": "VP80", "avi": "XVID",
}
CODEC_AUDIO = {"mp4": "aac", "mkv": "aac", "webm": "libopus", "avi": "libmp3lame"}


def ffmpeg_disponivel() -> bool:
    return shutil.which("ffmpeg") is not None


def listar_fontes_audio() -> list[str]:
    """Fontes de entrada do PulseAudio/PipeWire (mics + monitores)."""
    try:
        resultado = subprocess.run(
            ["pactl", "list", "short", "sources"],
            capture_output=True, text=True, timeout=4,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    fontes: list[str] = []
    for linha in resultado.stdout.splitlines():
        campos = linha.split("\t")
        if len(campos) >= 2 and campos[1].strip():
            fontes.append(campos[1].strip())
    return fontes


def _ajustar_para(quadro: np.ndarray, resolucao: tuple[int, int]) -> np.ndarray:
    """Redimensiona mantendo proporção e completa com bordas pretas."""
    alvo_l, alvo_a = resolucao
    altura, largura = quadro.shape[:2]
    fator = min(alvo_l / largura, alvo_a / altura)
    novo_l, novo_a = int(largura * fator), int(altura * fator)
    interpolacao = cv2.INTER_AREA if fator < 1.0 else cv2.INTER_LINEAR
    redimensionado = cv2.resize(quadro, (novo_l, novo_a), interpolation=interpolacao)
    tela = np.zeros((alvo_a, alvo_l, 3), dtype=np.uint8)
    desloc_x, desloc_y = (alvo_l - novo_l) // 2, (alvo_a - novo_a) // 2
    tela[desloc_y:desloc_y + novo_a, desloc_x:desloc_x + novo_l] = redimensionado
    return tela


class GravadorVideo(QThread):
    """Grava os quadros que chegam da câmera e mistura o áudio ao final."""

    gravacao_finalizada = pyqtSignal(str, str)  # (caminho, aviso_ou_erro)

    def __init__(self, pasta: str, contenedor: str, resolucao: tuple[int, int] | None,
                 fonte_audio: str | None, qps: float, parent=None) -> None:
        super().__init__(parent)
        self._pasta = pasta
        self._contenedor = contenedor if contenedor in FOURCC_POR_CONTENEDOR else "mp4"
        self._resolucao = resolucao
        self._fonte_audio = fonte_audio
        self._qps = max(1.0, float(qps or 30))
        self._fila: queue.Queue = queue.Queue(maxsize=150)
        self._gravando = True
        self._descartados = 0
        carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.caminho_final = os.path.join(pasta, f"video_{carimbo}.{self._contenedor}")
        self._caminho_video = os.path.join(pasta, f".video_{carimbo}_parcial.{self._contenedor}")
        self._caminho_audio = os.path.join(pasta, f".audio_{carimbo}.wav")

    # ------------- API chamada por outras threads -------------

    def aceitar_quadro(self, quadro: np.ndarray) -> None:
        """Recebe um quadro da thread de captura (não bloqueia nunca)."""
        if not self._gravando:
            return
        try:
            self._fila.put_nowait(quadro)
        except queue.Full:
            try:
                self._fila.get_nowait()  # descarta o mais antigo
                self._fila.put_nowait(quadro)
                self._descartados += 1
            except queue.Empty:
                pass

    def parar(self) -> None:
        """Pede o encerramento; a finalização acontece na própria thread."""
        self._gravando = False
        try:
            self._fila.put_nowait(None)  # sentinela
        except queue.Full:
            pass

    # ------------- laço da thread -------------

    def run(self) -> None:
        aviso = ""

        processo_audio = self._iniciar_audio()
        writer: cv2.VideoWriter | None = None
        fourcc = cv2.VideoWriter_fourcc(*FOURCC_POR_CONTENEDOR[self._contenedor])

        try:
            while True:
                item = self._fila.get()
                if item is None:
                    break
                quadro = item
                if self._resolucao is not None:
                    quadro = _ajustar_para(quadro, self._resolucao)
                if writer is None:
                    # Abre o writer com o tamanho do primeiro quadro real.
                    tamanho = (quadro.shape[1], quadro.shape[0])
                    writer = cv2.VideoWriter(
                        self._caminho_video, fourcc, self._qps, tamanho
                    )
                    if not writer.isOpened():
                        self._encerrar_audio(processo_audio)
                        self.gravacao_finalizada.emit("", traducao.t("erro.writer"))
                        return
                writer.write(quadro)
        finally:
            if writer is not None:
                writer.release()

        self._encerrar_audio(processo_audio)

        if processo_audio is not None and not os.path.isfile(self._caminho_audio):
            aviso = traducao.t("erro.audio")

        tem_audio = (
            processo_audio is not None
            and os.path.isfile(self._caminho_audio)
            and os.path.getsize(self._caminho_audio) > 1024
        )
        if tem_audio:
            ok_mux, erro_mux = self._misturar_audio()
            if not ok_mux:
                aviso = (aviso + " · " if aviso else "") + (erro_mux or traducao.t("erro.mux"))
                self._promover_video()
        else:
            self._promover_video()

        for temporario in (self._caminho_video, self._caminho_audio):
            try:
                if os.path.isfile(temporario):
                    os.remove(temporario)
            except OSError:
                pass

        if self._descartados:
            aviso = (aviso + " · " if aviso else "") + traducao.t(
                "status.gravacao_descartados", n=self._descartados
            )
        self.gravacao_finalizada.emit(self.caminho_final, aviso)

    # ------------- etapas internas -------------

    def _iniciar_audio(self) -> subprocess.Popen | None:
        if not self._fonte_audio or not ffmpeg_disponivel():
            return None
        comando = [
            "ffmpeg", "-nostdin", "-y",
            "-f", "pulse", "-i", self._fonte_audio,
            "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2",
            self._caminho_audio,
        ]
        try:
            return subprocess.Popen(
                comando, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
            )
        except OSError:
            return None

    def _encerrar_audio(self, processo: subprocess.Popen | None) -> None:
        if processo is None:
            return
        try:
            processo.wait(timeout=1)
            return
        except subprocess.TimeoutExpired:
            pass
        processo.terminate()
        try:
            processo.wait(timeout=3)
        except subprocess.TimeoutExpired:
            processo.kill()

    def _misturar_audio(self) -> tuple[bool, str]:
        codec = CODEC_AUDIO[self._contenedor]
        comando = [
            "ffmpeg", "-nostdin", "-y",
            "-i", self._caminho_video, "-i", self._caminho_audio,
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "copy", "-c:a", codec, "-shortest",
            self.caminho_final,
        ]
        try:
            resultado = subprocess.run(
                comando, capture_output=True, text=True, timeout=120,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return False, str(exc)
        if resultado.returncode == 0 and os.path.isfile(self.caminho_final):
            return True, ""
        linhas = (resultado.stderr or "").strip().splitlines()
        return False, (linhas[-1] if linhas else "")

    def _promover_video(self) -> None:
        try:
            os.replace(self._caminho_video, self.caminho_final)
        except OSError as exc:
            # Se o renome falhar (raro), tenta com o próprio caminho final.
            try:
                shutil.copyfile(self._caminho_video, self.caminho_final)
                os.remove(self._caminho_video)
            except OSError:
                self.caminho_final = self._caminho_video  # último recurso
                _ = exc
