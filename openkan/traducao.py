"""Suporte bilíngue (português / inglês) do OpenKan.

As chaves seguem o padrão "modulo.nome". A função t() devolve o texto no
idioma ativo; se faltar, cai para o português e depois para a própria chave.
"""

from __future__ import annotations

from . import AUTOR, LINK_DISCORD, LINK_KOFI

IDIOMAS = {"pt": "Português", "en": "English"}

_idioma_atual = "pt"

_textos: dict[str, dict[str, str]] = {
    # ---------------- aplicação ----------------
    "app.subtitulo": {"pt": "câmera + efeitos para Ubuntu",
                      "en": "camera + effects for Ubuntu"},
    "sobre.texto": {
        "pt": "<h3>OpenKan {versao}</h3>"
              "<p>Aplicativo de webcam para Ubuntu: veja sua câmera, aplique "
              "efeitos em tempo real, ajuste obturador/ISO/balanço de branco, "
              "gire a imagem e capture fotos e vídeos (com áudio).</p>"
              "<p>Inspirado no Webcamoid (webcamoid.github.io).<br>"
              "Feito com Python, OpenCV e PyQt6. Interface animada com "
              "PyQt-Fluent-Widgets (GPL-3). Compatível com Wayland e X11.</p>"
              "<p>Criado por <b>" + AUTOR + "</b> — "
              "<a href='" + LINK_KOFI + "'>Ko-Fi</a> · "
              "<a href='" + LINK_DISCORD + "'>Discord</a></p>"
              "<p style='color:#8a919d'>Código sob licença MIT — use, estude e "
              "modifique à vontade.</p>",
        "en": "<h3>OpenKan {versao}</h3>"
              "<p>Webcam application for Ubuntu: view your camera, apply "
              "real-time effects, adjust shutter/ISO/white balance, rotate the "
              "image and capture photos and videos (with audio).</p>"
              "<p>Inspired by Webcamoid (webcamoid.github.io).<br>"
              "Built with Python, OpenCV and PyQt6. Animated UI by "
              "PyQt-Fluent-Widgets (GPL-3). Works on Wayland and X11.</p>"
              "<p>Created by <b>" + AUTOR + "</b> — "
              "<a href='" + LINK_KOFI + "'>Ko-Fi</a> · "
              "<a href='" + LINK_DISCORD + "'>Discord</a></p>"
              "<p style='color:#8a919d'>Code under MIT license — use, study "
              "and modify freely.</p>",
    },
    # ---------------- apoio ao projeto ----------------
    "apoio.botao": {"pt": "♥ Apoiar no Ko-Fi", "en": "♥ Support on Ko-Fi"},
    "apoio.dica": {
        "pt": "Doação voluntária pelo Ko-Fi — clique para abrir a página",
        "en": "Voluntary donation via Ko-Fi — click to open the page",
    },
    "menu.apoiar": {
        "pt": "&Apoiar o projeto (Ko-Fi)",
        "en": "&Support the project (Ko-Fi)",
    },
    "menu.discord": {
        "pt": "Co&munidade no Discord",
        "en": "&Community on Discord",
    },
    # ---------------- menus ----------------
    "menu.arquivo": {"pt": "&Arquivo", "en": "&File"},
    "menu.salvar_foto_como": {"pt": "Salvar &foto como…", "en": "Save &photo as…"},
    "menu.sair": {"pt": "&Sair", "en": "&Quit"},
    "menu.idioma": {"pt": "&Idioma / Language", "en": "&Language / Idioma"},
    "menu.ajuda": {"pt": "A&juda", "en": "&Help"},
    "menu.sobre": {"pt": "&Sobre o OpenKan", "en": "&About OpenKan"},
    "menu.abrir_fotos": {"pt": "Abrir &pasta das fotos", "en": "Open &photos folder"},
    "menu.abrir_videos": {"pt": "Abrir pasta dos &vídeos", "en": "Open &videos folder"},
    # ---------------- fontes ----------------
    "fontes.titulo": {"pt": "FONTES DE VÍDEO", "en": "VIDEO SOURCES"},
    "fontes.atualizar": {"pt": "Atualizar", "en": "Refresh"},
    "fontes.procurando": {"pt": "Procurando câmeras…", "en": "Looking for cameras…"},
    "fontes.nenhuma": {
        "pt": "Nenhuma câmera detectada.\n\nConecte uma webcam (USB ou integrada) "
              "e clique em Atualizar. Se ainda assim não aparecer, veja a seção "
              "“Solução de problemas” do README.",
        "en": "No camera detected.\n\nConnect a webcam (USB or built-in) and click "
              "Refresh. If it still doesn't show up, see the “Troubleshooting” "
              "section of the README.",
    },
    "fontes.iniciando": {"pt": "Iniciando câmera…", "en": "Starting camera…"},
    "fontes.falha": {"pt": "A câmera não pôde ser aberta.\nTente outra fonte de vídeo ou clique em Atualizar.",
                     "en": "The camera could not be opened.\nTry another video source or click Refresh."},
    "fontes.sem_camera": {"pt": "nenhuma câmera encontrada", "en": "no camera found"},
    # ---------------- efeitos ----------------
    "efeitos.titulo": {"pt": "EFEITOS", "en": "EFFECTS"},
    "efeito.original": {"pt": "Original", "en": "Original"},
    "efeito.espelho": {"pt": "Espelho", "en": "Mirror"},
    "efeito.cinza": {"pt": "Preto e branco", "en": "Black & white"},
    "efeito.sepia": {"pt": "Sépia", "en": "Sepia"},
    "efeito.negativo": {"pt": "Negativo", "en": "Negative"},
    "efeito.desfoque": {"pt": "Desfoque", "en": "Blur"},
    "efeito.cartoon": {"pt": "Cartoon", "en": "Cartoon"},
    "efeito.calor": {"pt": "Térmico", "en": "Thermal"},
    "efeito.pixel": {"pt": "Pixelado", "en": "Pixelate"},
    "efeito.vinheta": {"pt": "Vinheta", "en": "Vignette"},
    "efeito.neon": {"pt": "Neon", "en": "Neon"},
    "efeito.scanlines": {"pt": "Scanlines", "en": "Scanlines"},
    "efeito.exposicao_longa": {"pt": "Exposição longa", "en": "Long exposure"},
    "efeito.tooltip": {"pt": "Aplicar o efeito {nome}", "en": "Apply the {nome} effect"},
    # ---------------- orientação ----------------
    "orientacao.titulo": {"pt": "ORIENTAÇÃO", "en": "ORIENTATION"},
    "orientacao.rotacao": {"pt": "Rotação", "en": "Rotation"},
    "orientacao.espelhar_h": {"pt": "Espelhar horizontal", "en": "Flip horizontal"},
    "orientacao.espelhar_v": {"pt": "Espelhar vertical", "en": "Flip vertical"},
    # ---------------- controles da câmera ----------------
    "controles.titulo": {"pt": "CONTROLES DA CÂMERA", "en": "CAMERA CONTROLS"},
    "controles.carregando": {"pt": "Lendo controles…", "en": "Reading controls…"},
    "controles.driver_titulo": {
        "pt": "CONTROLES DO HARDWARE",
        "en": "HARDWARE CONTROLS",
    },
    "controles.indisponiveis": {
        "pt": "Esta câmera não expõe controles de hardware (obturador, ISO, foco, "
              "zoom, balanço de branco…). Isso é normal em câmeras virtuais — como "
              "o Iriun Webcam e o DroidCam (celular usado como câmera) — e em alguns "
              "modelos simples. Use os ajustes de imagem acima, que funcionam com "
              "qualquer câmera. Ao conectar uma webcam USB real, os controles de "
              "hardware aparecem aqui automaticamente.",
        "en": "This camera exposes no hardware controls (shutter, ISO, focus, zoom, "
              "white balance…). That is normal for virtual cameras — such as Iriun "
              "Webcam and DroidCam (phone used as camera) — and some basic models. "
              "Use the image adjustments above, which work with any camera. When you "
              "plug a real USB webcam, the hardware controls appear here.",
    },
    "controles.restaurar": {"pt": "Restaurar padrões", "en": "Restore defaults"},
    "controles.falha_aplicar": {"pt": "Falha ao ajustar {nome}: {erro}",
                                "en": "Failed to set {nome}: {erro}"},
    "controle.shutter": {"pt": "Obturador (exposição)", "en": "Shutter (exposure)"},
    "controle.iso": {"pt": "ISO (ganho)", "en": "ISO (gain)"},
    "controle.balanco_branco": {"pt": "Balanço de branco (K)", "en": "White balance (K)"},
    "controle.balanco_auto": {"pt": "Balanço de branco automático", "en": "Auto white balance"},
    "controle.exposicao_auto": {"pt": "Exposição automática", "en": "Auto exposure"},
    "controle.zoom": {"pt": "Zoom", "en": "Zoom"},
    "controle.iris": {"pt": "Abertura da lente (íris)", "en": "Lens aperture (iris)"},
    "controle.foco": {"pt": "Foco", "en": "Focus"},
    "controle.foco_auto": {"pt": "Foco automático", "en": "Autofocus"},
    "controle.brilho": {"pt": "Brilho", "en": "Brightness"},
    "controle.contraste": {"pt": "Contraste", "en": "Contrast"},
    "controle.saturacao": {"pt": "Saturação", "en": "Saturation"},
    "controle.matiz": {"pt": "Matiz", "en": "Hue"},
    "controle.nitidez": {"pt": "Nitidez", "en": "Sharpness"},
    "controle.gamma": {"pt": "Gama", "en": "Gamma"},
    "controle.luz_fundo": {"pt": "Compensação de luz de fundo", "en": "Backlight compensation"},
    "controle.freq_rede": {"pt": "Frequência da rede (anti-piscar)", "en": "Power line frequency (anti-flicker)"},
    "controle.menu.desativado": {"pt": "Desativado", "en": "Disabled"},
    # ---------------- ajustes de imagem por software ----------------
    "ajustes.titulo": {
        "pt": "AJUSTES DE IMAGEM (SOFTWARE)",
        "en": "IMAGE ADJUSTMENTS (SOFTWARE)",
    },
    "ajustes.dica": {
        "pt": "Processados pelo OpenKan — funcionam com qualquer câmera, "
              "inclusive virtuais (Iriun, DroidCam). Aplicados também às fotos "
              "e aos vídeos gravados.",
        "en": "Processed by OpenKan — work with any camera, including virtual "
              "ones (Iriun, DroidCam). Also applied to saved photos and videos.",
    },
    "ajustes.ganho": {"pt": "Ganho digital (ISO)", "en": "Digital gain (ISO)"},
    "ajustes.brilho": {"pt": "Brilho", "en": "Brightness"},
    "ajustes.contraste": {"pt": "Contraste", "en": "Contrast"},
    "ajustes.saturacao": {"pt": "Saturação", "en": "Saturation"},
    # ---------------- captura / ajustes ----------------
    "captura.titulo": {"pt": "CAPTURA", "en": "CAPTURE"},
    "captura.qps": {"pt": "QPS", "en": "FPS"},
    "captura.qps_tooltip": {
        "pt": "Taxa de quadros pedida à câmera. Nem todo driver obedece — a taxa "
              "real aparece no rodapé da janela.",
        "en": "Frame rate requested from the camera. Not every driver obeys — the "
              "actual rate shows in the status bar.",
    },
    "captura.secao_foto": {"pt": "FOTO", "en": "PHOTO"},
    "captura.secao_video": {"pt": "VÍDEO", "en": "VIDEO"},
    "captura.formato": {"pt": "Formato", "en": "Format"},
    "captura.tamanho": {"pt": "Tam. máx.", "en": "Max size"},
    "captura.resolucao": {"pt": "Resolução", "en": "Resolution"},
    "captura.audio": {"pt": "Áudio", "en": "Audio"},
    "captura.audio_sem": {"pt": "Sem áudio", "en": "No audio"},
    "captura.audio_monitor": {"pt": "{nome} (monitor)", "en": "{nome} (monitor)"},
    "captura.nativa": {"pt": "Nativa", "en": "Native"},
    "captura.foto_botao": {"pt": "Capturar foto", "en": "Capture photo"},
    "captura.video_botao": {"pt": "Gravar vídeo", "en": "Record video"},
    "captura.video_parar": {"pt": "Parar gravação", "en": "Stop recording"},
    "captura.video_parando": {"pt": "Finalizando…", "en": "Finalizing…"},
    "captura.pasta_foto": {"pt": "Escolher pasta das fotos", "en": "Choose photos folder"},
    "captura.pasta_video": {"pt": "Escolher pasta dos vídeos", "en": "Choose videos folder"},
    "captura.pasta_atual": {"pt": "Salvando em: {pasta}", "en": "Saving to: {pasta}"},
    "captura.pasta_erro": {
        "pt": "Não foi possível usar esta pasta:",
        "en": "This folder could not be used:",
    },
    # ---------------- status ----------------
    "status.bemvindo": {"pt": "Bem-vindo ao OpenKan! Escolha uma câmera na barra lateral.",
                        "en": "Welcome to OpenKan! Pick a camera in the sidebar."},
    "status.camera_iniciada": {"pt": "Câmera iniciada.", "en": "Camera started."},
    "status.efeito": {"pt": "Efeito ativo: {nome}", "en": "Active effect: {nome}"},
    "status.foto_salva": {"pt": "Foto salva em {caminho}", "en": "Photo saved at {path}"},
    "status.gravando": {"pt": "Gravando… {tempo}", "en": "Recording… {time}"},
    "status.gravacao_salva": {"pt": "Vídeo salvo em {caminho}", "en": "Video saved at {path}"},
    "status.gravacao_aviso": {"pt": "Vídeo salvo em {caminho} — mas: {aviso}",
                              "en": "Video saved at {path} — however: {aviso}"},
    "status.gravacao_descartados": {"pt": "{n} quadros descartados por lentidão do disco",
                                    "en": "{n} frames dropped due to slow disk"},
    "status.sem_imagem_foto": {
        "pt": "Nenhuma imagem disponível para capturar.\nEscolha uma câmera e aguarde o vídeo aparecer.",
        "en": "No image available to capture.\nPick a camera and wait for the video to appear.",
    },
    "status.sem_camera_video": {
        "pt": "Nenhuma câmera ativa para gravar.\nEscolha uma câmera e aguarde o vídeo aparecer.",
        "en": "No active camera to record.\nPick a camera and wait for the video to appear.",
    },
    "erro.foto": {"pt": "Não foi possível salvar a foto:\n{erro}",
                  "en": "Could not save the photo:\n{erro}"},
    "erro.gravacao": {"pt": "Não foi possível gravar o vídeo:\n{erro}",
                      "en": "Could not record the video:\n{erro}"},
    "erro.camera_abrir": {
        "pt": "Não foi possível abrir {caminho}.\nVerifique se outro programa está usando a câmera.",
        "en": "Could not open {caminho}.\nCheck whether another program is using the camera.",
    },
    "erro.camera_quadros": {
        "pt": "{caminho} foi aberto, mas não entrega quadros.\nTente outro dispositivo na lista de fontes de vídeo.",
        "en": "{caminho} opened, but delivers no frames.\nTry another device in the video source list.",
    },
    "erro.camera_parou": {"pt": "A câmera {caminho} parou de responder.",
                          "en": "Camera {caminho} stopped responding."},
    "erro.writer": {
        "pt": "O sistema não conseguiu abrir o arquivo de vídeo neste formato.\nTente outro contêiner (ex.: MP4).",
        "en": "The system could not open the video file in this format.\nTry another container (e.g. MP4).",
    },
    "erro.audio": {
        "pt": "não foi possível capturar o áudio selecionado",
        "en": "could not capture the selected audio",
    },
    "erro.mux": {
        "pt": "não foi possível juntar áudio e vídeo (ffmpeg)",
        "en": "could not mux audio and video (ffmpeg)",
    },
    "qps": {"pt": "qps", "en": "fps"},
    # ---------------- notificações animadas (InfoBar) ----------------
    "info.foto_titulo": {"pt": "Foto salva", "en": "Photo saved"},
    "info.video_titulo": {"pt": "Vídeo salvo", "en": "Video saved"},
    "info.aviso_titulo": {"pt": "Atenção", "en": "Warning"},
    "info.erro_titulo": {"pt": "Erro", "en": "Error"},
    "info.sem_imagem": {
        "pt": "Nenhuma imagem disponível — escolha uma câmera e aguarde o vídeo.",
        "en": "No image available — pick a camera and wait for the video.",
    },
    "info.sem_camera_gravar": {
        "pt": "Nenhuma câmera ativa para gravar.",
        "en": "No active camera to record.",
    },
    "info.pasta_ok": {"pt": "Pasta atualizada", "en": "Folder updated"},
}


def idioma_atual() -> str:
    """Código do idioma ativo: 'pt' ou 'en'."""
    return _idioma_atual


def definir_idioma(codigo: str) -> None:
    """Define o idioma ativo ('pt' ou 'en'); códigos desconhecidos viram 'pt'."""
    global _idioma_atual
    _idioma_atual = codigo if codigo in IDIOMAS else "pt"


def idioma_do_sistema() -> str:
    """Detecta o idioma do ambiente; 'pt' para português, senão 'en'."""
    for variavel in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"):
        valor = os_environ(variavel)
        if valor and valor.lower().startswith("pt"):
            return "pt"
        if valor:
            return "en"
    return "en"


def os_environ(nome: str) -> str:
    import os

    return os.environ.get(nome, "")


def t(chave: str, **parametros) -> str:
    """Texto traduzido da chave; aceita parâmetros: t('status.foto_salva', caminho=x)."""
    entrada = _textos.get(chave)
    if not entrada:
        return chave
    texto = entrada.get(_idioma_atual) or entrada.get("pt") or chave
    if parametros:
        try:
            texto = texto.format(**parametros)
        except (KeyError, IndexError):
            pass
    return texto
