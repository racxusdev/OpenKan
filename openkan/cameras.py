"""Detecção de câmeras V4L2 no Linux.

No Ubuntu cada webcam costuma criar dois nós em /dev/video*: um de captura
(por exemplo /dev/video0) e um nó de metadados (ex.: /dev/video1) que NÃO
entrega imagens. Por isso, além de listar os nós, este módulo "sonda" cada
dispositivo com OpenCV e só devolve os que realmente produzem quadros.

IMPORTANTE: o backend V4L2 do OpenCV só aceita ABERTURA POR ÍNDICE numérico
("/dev/video0" como texto dispara o aviso "can't be used to capture by
name" e falha). Toda abertura aqui usa o índice extraído do caminho.
"""

from __future__ import annotations

import glob
import os
import re

import cv2


def _ordenacao_natural(caminho: str) -> tuple[str, int]:
    """Ordena /dev/video2 depois de /dev/video10 (ordem numérica)."""
    base = os.path.basename(caminho)
    numero = re.sub(r"\D", "", base)
    return (caminho, int(numero) if numero else 0)


def indice_do(caminho: str) -> int | None:
    """Extrai o índice numérico do nó: /dev/video3 -> 3 (None se inválido)."""
    m = re.fullmatch(r"/dev/video(\d+)", caminho.strip())
    return int(m.group(1)) if m else None


def _nome_sysfs(caminho: str) -> str | None:
    """Lê o nome amigável da câmera em /sys/class/video4linux/<nó>/name."""
    arq = f"/sys/class/video4linux/{os.path.basename(caminho)}/name"
    try:
        with open(arq, "r", encoding="utf-8", errors="replace") as fonte:
            nome = fonte.read().strip()
    except OSError:
        return None
    if not nome:
        return None
    # Nomes do kernel costumam terminar com a localização física:
    # "HD Webcam: HD Webcam (usb-0000:00:14.0-6)"
    nome = re.sub(r"\s*\([^)]*\)\s*$", "", nome)
    return nome.strip() or None


def dispositivos_encontrados() -> list[str]:
    """Lista todos os nós /dev/video* em ordem numérica."""
    return sorted(glob.glob("/dev/video*"), key=_ordenacao_natural)


def sondar_camera(caminho: str, largura: int = 640, altura: int = 480) -> bool:
    """Abre o dispositivo (por índice) e verifica se ele entrega um quadro."""
    indice = indice_do(caminho)
    if indice is None:
        return False
    cap = cv2.VideoCapture(indice, cv2.CAP_V4L2)
    try:
        if not cap.isOpened():
            return False
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, largura)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, altura)
        ok, _ = cap.read()
        return ok
    finally:
        cap.release()


def listar_cameras() -> list[dict]:
    """Devolve as câmeras utilizáveis: [{'caminho': '/dev/video0', 'nome': '...'}]."""
    cameras: list[dict] = []
    for caminho in dispositivos_encontrados():
        try:
            if not sondar_camera(caminho):
                continue
        except Exception:
            continue
        nome = _nome_sysfs(caminho) or f"Câmera {len(cameras) + 1}"
        cameras.append(
            {"caminho": caminho, "indice": indice_do(caminho), "nome": nome}
        )

    # Dois nós diferentes podem pertencer ao mesmo hardware e herdar o nome:
    # numera as repetições para não confundir na lista.
    aparições: dict[str, int] = {}
    for cam in cameras:
        base = cam["nome"]
        aparições[base] = aparições.get(base, 0) + 1
        if aparições[base] > 1:
            cam["nome"] = f"{base} ({aparições[base]})"
    return cameras
