"""OpenKan — aplicativo de webcam para Ubuntu inspirado no Webcamoid.

Módulos:
    efeitos      — filtros em tempo real (numpy/OpenCV)
    cameras      — detecção de câmeras V4L2 em /dev/video*
    captura      — thread de captura de vídeo (Qt)
    controles_v4l2 — controles manuais (obturador, ISO, balanço de branco…)
    gravacao     — gravação de vídeo com áudio opcional (ffmpeg)
    salvar_foto  — gravação das fotos capturadas
    traducao     — interface bilíngue pt/en
    janela       — janela principal (tema grafite + vermelho sangue)
    main         — ponto de entrada (python3 -m openkan)
"""

VERSAO = "2.2.0"

# Autoria e links oficiais (exibidos na interface e no README)
AUTOR = "Racxus"
LINK_KOFI = "https://ko-fi.com/racxus"
LINK_DISCORD = "https://discord.gg/hDA2YTFJpX"
LINK_GITHUB = "https://github.com/racxus/OpenKan"
