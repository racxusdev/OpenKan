"""Janela principal do OpenKan 2.0.

Interface bilíngue (pt/en) no estilo Webcamoid: barra lateral grafite com as
fontes de vídeo, grade de efeitos e orientação; área de preview com borda
animada durante a gravação; painel de CONTROLES DA CÂMERA (obturador, ISO,
balanço de branco, foco, zoom — lidos direto do driver V4L2 via v4l2-ctl);
ajustes de FOTO (formato/tamanho/pasta) e VÍDEO (contêiner/resolução/áudio/
pasta); botões de gravação e captura. Os widgets interativos (combos,
sliders, interruptores) usam PyQt-Fluent-Widgets com tema escuro e acento
vermelho sangue; notificações são toasts animados (InfoBar). Tudo
traduzível em tempo de execução (retraduzir) e com preferências no QSettings.
"""

from __future__ import annotations

import cv2
import datetime
import os
import threading

from PyQt6.QtCore import (
    QElapsedTimer,
    QPoint,
    QPropertyAnimation,
    QRect,
    QSize,
    Qt,
    QSettings,
    QTimer,
    QUrl,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QAction,
    QDesktopServices,
    QIcon,
    QImage,
    QPixmap,
)
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFileDialog,
    QFrame,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLayout,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    ComboBox,
    InfoBar,
    InfoBarPosition,
    PushButton,
    Slider,
    SwitchButton,
    TransparentToolButton,
)
from qfluentwidgets.common.icon import FluentIcon as FIF

from . import (
    LINK_DISCORD,
    LINK_KOFI,
    VERSAO,
    controles_v4l2,
    efeitos,
    gravacao,
    salvar_foto,
    traducao,
)
from .captura import CameraWorker, LeitorControles, ProcuraCameras
from .traducao import t

ICONE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "recursos", "openkan.svg"
)

INTERVALO_RENDER_MS = 33  # ~30 renderizações por segundo

RESOLUCOES_VIDEO = [
    ("1920×1080", (1920, 1080)),
    ("1280×720", (1280, 720)),
    ("854×480", (854, 480)),
    ("640×360", (640, 360)),
]
TAMANHOS_FOTO = [("1920", 1920), ("1280", 1280), ("640", 640)]

ESTILO = """
* {
    font-family: 'Ubuntu', 'Noto Sans', 'DejaVu Sans', sans-serif;
    font-size: 13px;
}
QMainWindow, QDialog {
    background-color: #131418;
    color: #e9ebee;
}
QWidget {
    background-color: #131418;
    color: #e9ebee;
}
QMenuBar { background-color: #131418; color: #e9ebee; }
QMenuBar::item:selected { background-color: #262a32; border-radius: 4px; }
QMenu {
    background-color: #1a1d23; color: #e9ebee;
    border: 1px solid #2c3038; border-radius: 8px; padding: 4px;
}
QMenu::item { border-radius: 5px; padding: 5px 24px 5px 12px; }
QMenu::item:selected { background-color: #d0122f; color: #ffffff; }
QToolTip {
    background-color: #262a32; color: #e9ebee;
    border: 1px solid #3a3f49; padding: 3px; border-radius: 4px;
}

/* ---------- barra lateral ---------- */
#barraLateral { background-color: #191b21; border-right: 1px solid #24272e; }
#tituloApp { font-size: 20px; font-weight: 800; color: #ffffff; background: transparent; }
#subtituloApp { color: #9aa1ac; font-size: 11px; background: transparent; }
#rotuloSecao {
    color: #9aa1ac; font-size: 11px; font-weight: 700; letter-spacing: 1px;
    background: transparent; padding: 2px 0 2px 8px;
    border-left: 3px solid #d0122f;
}
QListWidget {
    background-color: #1e2127; border: 1px solid #2a2e36; border-radius: 10px;
    padding: 4px; color: #e9ebee;
}
QListWidget::item { border-radius: 8px; margin: 2px; border: 1px solid transparent; }
QListWidget::item:selected { background-color: #2a1216; border: 1px solid #d0122f; }
QListWidget::item:hover:!selected { background-color: #242830; }
QListWidget QWidget { background: transparent; }
#itemNome { background: transparent; font-weight: 600; }
#itemCaminho { background: transparent; color: #b6bcc6; font-size: 11px; }

/* ---------- grade de efeitos (botões custom) ---------- */
#botaoEfeito {
    background-color: #1d2026; color: #d9dce1; font-size: 12px;
    border: 1px solid #2a2e36; border-radius: 9px; padding: 9px 2px;
}
#botaoEfeito:hover { background-color: #262b33; border-color: #3a3f49; }
#botaoEfeito:checked {
    background-color: #2a1216; border: 2px solid #d0122f;
    color: #ff8791; font-weight: 700;
}
#botaoEfeito:disabled { color: #6b7280; }

/* ---------- botões grandes de captura ---------- */
#botaoFoto {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #e01e37, stop:1 #9d0a1f);
    color: #ffffff; font-size: 15px; font-weight: 700;
    padding: 12px 34px; border-radius: 26px; border: 1px solid #57060f;
}
#botaoFoto:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #f22945, stop:1 #b41126);
}
#botaoFoto:pressed { background-color: #8c091b; }
#botaoFoto:disabled { background-color: #34383f; color: #9aa1ab; border: 1px solid #262a32; }
#botaoGravar {
    background-color: #22262d; color: #e9ebee; font-size: 15px; font-weight: 700;
    padding: 12px 26px; border-radius: 26px; border: 1px solid #2f343d;
}
#botaoGravar:hover { background-color: #2b3039; }
#botaoGravar:disabled { background-color: #1d2026; color: #6b7280; }
#botaoGravar[gravando="true"] {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #d0122f, stop:1 #8c091b);
    border: 1px solid #57060f; color: #ffffff;
}
#botaoGravar[gravando="true"]:hover { background-color: #e01e37; }

/* ---------- área de vídeo (borda animada na gravação) ---------- */
#areaPreview {
    background-color: #0a0b0e; border: 1px solid #2a2e36; border-radius: 12px;
    color: #9aa1ac; font-size: 14px;
}
#areaPreview[gravando="true"] { border: 2px solid #d0122f; }
#areaPreview[gravando="true"][pulso="false"] { border: 2px solid #57101c; }
#rotuloInfo { color: #9aa1ac; font-size: 12px; background: transparent; }
#barraAjustes {
    background-color: #1b1e24; border: 1px solid #2a2e36; border-radius: 12px;
}
QStatusBar { background-color: #131418; color: #9aa1ac; }
QStatusBar::item { border: none; }

/* ---------- painel de controles ---------- */
#painelControles { background-color: #191b21; border-left: 1px solid #24272e; }
QScrollArea#areaControles { background: transparent; border: none; }
QWidget#conteudoControles { background: transparent; }
#rotuloControle { color: #c9ced6; font-size: 11px; background: transparent; }
#rotuloValorControle { color: #9aa1ac; font-size: 11px; background: transparent; }
#rotuloControlesVazio { color: #6b7280; font-size: 12px; background: transparent; }

/* ---------- barras de rolagem discretas no tema grafite ---------- */
QScrollBar:vertical { background: transparent; width: 8px; margin: 2px 2px 2px 0; }
QScrollBar::handle:vertical {
    background: #333843; border-radius: 4px; min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: #d0122f; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
QScrollBar:horizontal { background: transparent; height: 8px; margin: 0 2px 2px 2px; }
QScrollBar::handle:horizontal {
    background: #333843; border-radius: 4px; min-width: 30px;
}
QScrollBar::handle:horizontal:hover { background: #d0122f; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: transparent; }
QScrollBarCorner { background: transparent; }

/* ---------- divisores arrastáveis (janela ajustável) ---------- */
QSplitter::handle {
    background-color: #191b21;
}
QSplitter::handle:hover { background-color: #d0122f; }
QSplitter::handle:pressed { background-color: #e01e37; }
QSplitter::handle:horizontal { width: 3px; }

/* ---------- rolagem da barra lateral ---------- */
QScrollArea#rolagemLateral { background: transparent; border: none; }
QWidget#conteudoLateral { background: transparent; }
QScrollArea#rolagemLateral > QWidget > QWidget { background: transparent; }

/* ---------- botão discreto de apoio (Ko-Fi) ---------- */
#botaoDoar {
    background-color: transparent; color: #9aa1ac; font-size: 12px;
    border: 1px solid transparent; border-radius: 8px; padding: 5px 8px;
}
#botaoDoar:hover {
    color: #ff8791; background-color: #2a1216; border: 1px solid #57101c;
}
"""


# ================================================================== #
#   Grade de efeitos em fluxo (se reorganiza com o tamanho da janela)  #
# ================================================================== #

class GradeFluxo(QLayout):
    """Layout de fluxo: reparte os botões em linhas conforme a largura.

    Substitui a grade fixa de 2 colunas — ao estreitar a barra lateral os
    botões caem para 1 por linha; ao alargar, distribuem o espaço restante
    igualmente na linha. Nada fica cortado em nenhum tamanho de janela.
    """

    def __init__(self, parent=None, espacamento: int = 8) -> None:
        super().__init__(parent)
        self._espacamento = espacamento
        self._itens: list = []

    def addItem(self, item) -> None:  # noqa: N802 (API do Qt)
        self._itens.append(item)

    def count(self) -> int:  # noqa: N802
        return len(self._itens)

    def itemAt(self, indice):  # noqa: N802
        if 0 <= indice < len(self._itens):
            return self._itens[indice]
        return None

    def takeAt(self, indice):  # noqa: N802
        if 0 <= indice < len(self._itens):
            return self._itens.pop(indice)
        return None

    def expandingDirections(self):  # noqa: N802
        return Qt.Orientation(0)

    def hasHeightForWidth(self) -> bool:  # noqa: N802
        return True

    def heightForWidth(self, largura: int) -> int:  # noqa: N802
        return self._dispor(QRect(0, 0, largura, 0), testar=True)

    def setGeometry(self, retangulo) -> None:  # noqa: N802
        super().setGeometry(retangulo)
        self._dispor(retangulo, testar=False)

    def sizeHint(self) -> QSize:  # noqa: N802
        return self.minimumSize()

    def minimumSize(self) -> QSize:  # noqa: N802
        tamanho = QSize()
        for item in self._itens:
            tamanho = tamanho.expandedTo(item.minimumSize())
        margens = self.contentsMargins()
        return tamanho + QSize(
            margens.left() + margens.right(), margens.top() + margens.bottom()
        )

    # -------------------------------------------------- interno

    def _linhas(self, area: QRect) -> list[list]:
        """Quebra os itens em linhas que caibam na largura da área."""
        linhas: list[list] = []
        atual: list = []
        x = area.x()
        for item in self._itens:
            largura = item.sizeHint().width()
            proximo_x = x + largura + self._espacamento
            if atual and proximo_x - self._espacamento > area.right() + 1:
                linhas.append(atual)
                atual = []
                x = area.x()
                proximo_x = x + largura + self._espacamento
            atual.append(item)
            x = proximo_x
        if atual:
            linhas.append(atual)
        return linhas

    def _dispor(self, retangulo: QRect, testar: bool) -> int:
        margens = self.contentsMargins()
        area = retangulo.adjusted(
            margens.left(), margens.top(), -margens.right(), -margens.bottom()
        )
        y = area.y()
        for linha in self._linhas(area):
            largura_dica = sum(i.sizeHint().width() for i in linha)
            extra = area.width() - largura_dica - self._espacamento * (len(linha) - 1)
            crescimento = max(0, extra) // len(linha) if not testar else 0
            x = area.x()
            altura_linha = 0
            for item in linha:
                dica = item.sizeHint()
                if not testar:
                    item.setGeometry(
                        QRect(QPoint(x, y), QSize(dica.width() + crescimento, dica.height()))
                    )
                x += dica.width() + crescimento + self._espacamento
                altura_linha = max(altura_linha, dica.height())
            y += altura_linha + self._espacamento
        altura_total = y - self._espacamento - area.y() + margens.top() + margens.bottom()
        return max(altura_total, self.minimumSize().height())


# ================================================================== #
#  Painel de controles da câmera (obturador, ISO, balanço de branco…) #
# ================================================================== #

class PainelControles(QFrame):
    """Coluna direita: ajustes de imagem (software) + controles V4L2 do driver.

    Os AJUSTES DE IMAGEM (ganho digital/ISO, brilho, contraste, saturação) são
    processados pelo próprio OpenKan e funcionam com qualquer câmera — inclusive
    as virtuais (Iriun, DroidCam), que não oferecem controles de hardware. Já a
    seção CONTROLES DO HARDWARE lista exatamente o que o driver V4L2 expõe; se
    o driver não expõe nada, um texto explica o motivo.
    """

    aplicacao_falhou = pyqtSignal(str, str)  # (nome do controle, mensagem de erro)
    leitura_pedida = pyqtSignal(str)         # painel pede nova leitura (após restaurar)
    ajuste_alterado = pyqtSignal(str, float)  # (chave, valor real) — emitido ao vivo

    # chave → (mín, máx, passo, neutro, escala→real, formato do valor exibido)
    AJUSTES = {
        "ganho":     (100, 400, 5, 100, 0.01, "×{:.1f}"),
        "brilho":    (-100, 100, 2, 0, 1.0, "{:+d}"),
        "contraste": (50, 150, 2, 100, 0.01, "×{:.1f}"),
        "saturacao": (0, 200, 5, 100, 0.01, "×{:.1f}"),
    }

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("painelControles")
        self.setMinimumWidth(268)
        self.setMaximumWidth(470)

        self._caminho: str | None = None
        self._leitor: LeitorControles | None = None
        self._controles: list[dict] = []
        self._widgets: dict[str, dict] = {}
        self._sliders_ajustes: dict[str, dict] = {}
        self._estado = "vazio"  # 'carregando' | 'vazio' | 'pronto'

        coluna = QVBoxLayout(self)
        coluna.setContentsMargins(12, 12, 12, 12)
        coluna.setSpacing(8)

        self._rotulo_titulo = QLabel(t("controles.titulo"))
        self._rotulo_titulo.setObjectName("rotuloSecao")
        self._rotulo_titulo.setWordWrap(True)
        coluna.addWidget(self._rotulo_titulo)

        self._area = QScrollArea()
        self._area.setObjectName("areaControles")
        self._area.setWidgetResizable(True)
        self._area.setFrameShape(QFrame.Shape.NoFrame)
        self._area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._conteudo = QWidget()
        self._conteudo.setObjectName("conteudoControles")
        caixa_conteudo = QVBoxLayout(self._conteudo)
        caixa_conteudo.setContentsMargins(2, 2, 6, 2)
        caixa_conteudo.setSpacing(10)

        # ---- seção permanente: ajustes de imagem por software
        self._rotulo_ajustes = QLabel(t("ajustes.titulo"))
        self._rotulo_ajustes.setObjectName("rotuloSecao")
        self._rotulo_ajustes.setToolTip(t("ajustes.dica"))
        self._rotulo_ajustes.setWordWrap(True)
        caixa_conteudo.addWidget(self._rotulo_ajustes)
        for chave, (mn, mx, passo, neutro, escala, fmt) in self.AJUSTES.items():
            caixa_conteudo.addWidget(
                self._linha_ajuste(chave, mn, mx, passo, neutro, escala, fmt)
            )
        caixa_conteudo.addSpacing(8)

        # ---- seção recarregada por câmera: controles do driver
        self._rotulo_driver = QLabel(t("controles.driver_titulo"))
        self._rotulo_driver.setObjectName("rotuloSecao")
        self._rotulo_driver.setWordWrap(True)
        caixa_conteudo.addWidget(self._rotulo_driver)
        self._linhas = QVBoxLayout()
        self._linhas.setContentsMargins(0, 0, 0, 0)
        self._linhas.setSpacing(10)
        caixa_conteudo.addLayout(self._linhas)
        caixa_conteudo.addStretch(1)

        self._area.setWidget(self._conteudo)
        coluna.addWidget(self._area, 1)

        self._rotulo_vazio = QLabel()
        self._rotulo_vazio.setObjectName("rotuloControlesVazio")
        self._rotulo_vazio.setWordWrap(True)
        self._rotulo_vazio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        coluna.addWidget(self._rotulo_vazio)

        self._botao_restaurar = PushButton(t("controles.restaurar"))
        self._botao_restaurar.setObjectName("botaoRestaurar")
        self._botao_restaurar.setCursor(Qt.CursorShape.PointingHandCursor)
        self._botao_restaurar.clicked.connect(self._restaurar)
        coluna.addWidget(self._botao_restaurar)

        self._mostrar_estado()

    # ------------------------------------------- ajustes de imagem (software)

    def _texto_ajuste(self, chave: str, bruto: int) -> str:
        _mn, _mx, _passo, _neutro, escala, fmt = self.AJUSTES[chave]
        if "d" in fmt:
            return fmt.format(int(bruto))
        return fmt.format(bruto * escala)

    def _linha_ajuste(self, chave: str, mn: int, mx: int, passo: int, neutro: int,
                      escala: float, fmt: str) -> QWidget:
        caixa = QWidget()
        coluna = QVBoxLayout(caixa)
        coluna.setContentsMargins(0, 0, 0, 0)
        coluna.setSpacing(2)

        rotulo = QLabel(t(f"ajustes.{chave}"))
        rotulo.setObjectName("rotuloControle")
        rotulo.setWordWrap(True)
        coluna.addWidget(rotulo)

        linha = QHBoxLayout()
        slider = Slider(Qt.Orientation.Horizontal)
        slider.setMinimum(mn)
        slider.setMaximum(mx)
        slider.setSingleStep(passo)
        slider.setPageStep(passo * 10)
        slider.setValue(neutro)
        valor = QLabel(self._texto_ajuste(chave, neutro))
        valor.setObjectName("rotuloValorControle")
        valor.setMinimumWidth(44)
        valor.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        linha.addWidget(slider, 1)
        linha.addWidget(valor)
        coluna.addLayout(linha)

        slider.valueChanged.connect(
            lambda v, c=chave: self._ao_slider_ajuste(c, v)
        )
        self._sliders_ajustes[chave] = {
            "slider": slider, "valor": valor, "rotulo": rotulo, "neutro": neutro,
        }
        return caixa

    def _ao_slider_ajuste(self, chave: str, bruto: int) -> None:
        entrada = self._sliders_ajustes.get(chave)
        if entrada:
            entrada["valor"].setText(self._texto_ajuste(chave, bruto))
        escala = self.AJUSTES[chave][4]
        self.ajuste_alterado.emit(chave, float(bruto) * escala)

    def definir_ajustes_iniciais(self, brutos: dict[str, int]) -> None:
        """Posiciona os sliders de software nos valores salvos (sem emitir)."""
        for chave, bruto in brutos.items():
            entrada = self._sliders_ajustes.get(chave)
            if not entrada:
                continue
            slider = entrada["slider"]
            slider.blockSignals(True)
            slider.setValue(int(bruto))
            slider.blockSignals(False)
            entrada["valor"].setText(self._texto_ajuste(chave, int(bruto)))

    # ------------------------------------------------ ciclo de vida

    def definir_camera(self, caminho: str | None) -> None:
        """Troca a câmera observada e relê os controles em segundo plano."""
        self._caminho = caminho
        self._limpar()
        if not caminho:
            self._estado = "vazio"
            self._mostrar_estado()
            return
        self._estado = "carregando"
        self._mostrar_estado()
        self._leitor = LeitorControles(caminho, self)
        self._leitor.controles_prontos.connect(self._ao_controles_prontos)
        self._leitor.start()

    def _ao_controles_prontos(self, caminho: str, lista: list) -> None:
        if caminho != self._caminho:
            return
        self._limpar()
        self._controles = list(lista)
        if not self._controles:
            self._estado = "vazio"
            self._mostrar_estado()
            return
        self._estado = "pronto"
        self._mostrar_estado()
        for controle in self._controles:
            if controle["tipo"] == "int":
                self._linha_inteiro(controle)
            elif controle["tipo"] == "bool":
                self._linha_booleano(controle)
            elif controle["tipo"] == "menu":
                self._linha_menu(controle)
        self._atualizar_ligacoes()

    def _limpar(self) -> None:
        while self._linhas.count():
            item = self._linhas.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            elif item.layout() is not None:
                sub = item.layout()
                while sub.count():
                    filho = sub.takeAt(0)
                    if filho.widget() is not None:
                        filho.widget().deleteLater()
        self._widgets = {}
        self._controles = []

    def _mostrar_estado(self) -> None:
        vazio_visivel = self._estado != "pronto"
        self._rotulo_vazio.setVisible(vazio_visivel)
        if self._estado == "carregando":
            self._rotulo_vazio.setText(t("controles.carregando"))
        elif self._estado == "vazio":
            self._rotulo_vazio.setText(t("controles.indisponiveis"))

    # ------------------------------------------------ linhas por tipo

    def _rotulo_do(self, controle: dict) -> str:
        chave = controles_v4l2.rotulo_de(controle["nome"])
        return t(chave) if chave else controle["nome"]

    def _linha_inteiro(self, controle: dict) -> None:
        caixa = QWidget()
        coluna = QVBoxLayout(caixa)
        coluna.setContentsMargins(0, 0, 0, 0)
        coluna.setSpacing(2)

        rotulo = QLabel(self._rotulo_do(controle))
        rotulo.setObjectName("rotuloControle")
        rotulo.setWordWrap(True)
        coluna.addWidget(rotulo)

        linha = QHBoxLayout()
        slider = Slider(Qt.Orientation.Horizontal)
        passo = max(1, int(controle["step"]))
        slider.setMinimum(int(controle["min"]))
        slider.setMaximum(int(controle["max"]))
        slider.setSingleStep(passo)
        slider.setPageStep(passo * 10)
        try:
            slider.setValue(int(controle["valor"]))
        except (TypeError, ValueError):
            pass
        slider.setEnabled(not controle["inativo"])
        valor = QLabel(str(controle["valor"]))
        valor.setObjectName("rotuloValorControle")
        valor.setMinimumWidth(44)
        valor.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        linha.addWidget(slider, 1)
        linha.addWidget(valor)
        coluna.addLayout(linha)

        slider.valueChanged.connect(lambda v: valor.setText(str(v)))
        slider.sliderReleased.connect(
            lambda: self._aplicar(controle["nome"], slider.value())
        )

        self._linhas.addWidget(caixa)
        self._widgets[controle["nome"]] = {
            "controle": controle, "slider": slider, "valor": valor, "rotulo": rotulo,
        }

    def _linha_booleano(self, controle: dict) -> None:
        caixa = QWidget()
        coluna = QVBoxLayout(caixa)
        coluna.setContentsMargins(0, 0, 0, 0)
        coluna.setSpacing(2)
        caixa_verificacao = SwitchButton(self._rotulo_do(controle))
        caixa_verificacao.setChecked(bool(controle["valor"]))
        caixa_verificacao.setEnabled(not controle["inativo"])
        caixa_verificacao.checkedChanged.connect(
            lambda ligado: self._aplicar(controle["nome"], int(ligado))
        )
        coluna.addWidget(caixa_verificacao)
        self._linhas.addWidget(caixa)
        self._widgets[controle["nome"]] = {
            "controle": controle, "check": caixa_verificacao, "rotulo": caixa_verificacao,
        }

    def _linha_menu(self, controle: dict) -> None:
        caixa = QWidget()
        coluna = QVBoxLayout(caixa)
        coluna.setContentsMargins(0, 0, 0, 0)
        coluna.setSpacing(2)
        rotulo = QLabel(self._rotulo_do(controle))
        rotulo.setObjectName("rotuloControle")
        rotulo.setWordWrap(True)
        coluna.addWidget(rotulo)

        combo = ComboBox()
        rotulos = controles_v4l2.rotulos_de_menu(controle["nome"], controle["itens"])
        for valor_menu in sorted(controle["itens"]):
            combo.addItem(rotulos.get(valor_menu, str(valor_menu)), userData=valor_menu)
        indice = combo.findData(controle["valor"])
        if indice >= 0:
            combo.setCurrentIndex(indice)
        combo.setEnabled(not controle["inativo"])
        combo.currentIndexChanged.connect(
            lambda _i: self._aplicar(controle["nome"], combo.currentData())
        )
        coluna.addWidget(combo)
        self._linhas.addWidget(caixa)
        self._widgets[controle["nome"]] = {
            "controle": controle, "combo": combo, "rotulo": rotulo,
        }

    # ------------------------------------------------ aplicar / ligações

    def _aplicar(self, nome: str, valor) -> None:
        """Aplica o controle em uma thread própria (não trava a interface)."""
        controle = self._widgets.get(nome, {}).get("controle")
        if controle is not None:
            controle["valor"] = valor

        def trabalho():
            ok, erro = controles_v4l2.definir_controle(self._caminho or "", nome, valor)
            if not ok:
                self.aplicacao_falhou.emit(nome, erro)

        threading.Thread(target=trabalho, daemon=True).start()
        self._atualizar_ligacoes()

    def _atualizar_ligacoes(self) -> None:
        """Controles automáticos desativam o manual correspondente."""
        def valor_de(nome, padrao=None):
            entrada = self._widgets.get(nome)
            if not entrada:
                return padrao, False
            return entrada["controle"]["valor"], True

        ligar = [
            # (nome do automático, nomes manuais que ele desativa)
            ("white_balance_temperature_auto", ["white_balance_temperature"]),
            ("focus_auto", ["focus_absolute"]),
        ]
        for automatico, manuais in ligar:
            valor, existe = valor_de(automatico)
            if existe:
                for manual in manuais:
                    widget = self._widgets.get(manual)
                    if widget:
                        if "slider" in widget:
                            widget["slider"].setEnabled(not bool(valor))
                        if "combo" in widget:
                            widget["combo"].setEnabled(not bool(valor))

        entrada = self._widgets.get("exposure_auto")
        if entrada and "combo" in entrada:
            modo = entrada["controle"]["valor"]
            widget_shutter = self._widgets.get("exposure_time_absolute")
            if widget_shutter and "slider" in widget_shutter:
                widget_shutter["slider"].setEnabled(modo == 1)

    def _restaurar(self) -> None:
        # Ajustes de software voltam ao neutro (o setValue emite e a janela
        # aplica/persiste cada mudança).
        for entrada in self._sliders_ajustes.values():
            entrada["slider"].setValue(entrada["neutro"])

        if not self._caminho or not self._controles:
            return
        caminho, controles = self._caminho, list(self._controles)

        def trabalho():
            controles_v4l2.restaurar_padroes(caminho, controles)
            self.leitura_pedida.emit(caminho)

        threading.Thread(target=trabalho, daemon=True).start()

    # ------------------------------------------------ retradução

    def retraduzir(self) -> None:
        self._rotulo_titulo.setText(t("controles.titulo"))
        self._rotulo_ajustes.setText(t("ajustes.titulo"))
        self._rotulo_ajustes.setToolTip(t("ajustes.dica"))
        self._rotulo_driver.setText(t("controles.driver_titulo"))
        self._botao_restaurar.setText(t("controles.restaurar"))
        for chave, entrada in self._sliders_ajustes.items():
            entrada["rotulo"].setText(t(f"ajustes.{chave}"))
        for nome, entrada in self._widgets.items():
            controle = entrada["controle"]
            rotulo_traduzido = self._rotulo_do(controle)
            rotulo = entrada.get("rotulo")
            if isinstance(rotulo, QLabel):
                rotulo.setText(rotulo_traduzido)
            elif isinstance(rotulo, SwitchButton):
                rotulo.setText(rotulo_traduzido)
            if "combo" in entrada:
                combo = entrada["combo"]
                rotulos = controles_v4l2.rotulos_de_menu(controle["nome"], controle["itens"])
                for i in range(combo.count()):
                    dado = combo.itemData(i)
                    combo.setItemText(i, rotulos.get(dado, str(dado)))
        self._mostrar_estado()


# ================================================================== #
#                     Janela principal                                #
# ================================================================== #

class JanelaPrincipal(QMainWindow):
    """Janela principal: preview + fontes + efeitos + controles + captura."""

    def __init__(self) -> None:
        super().__init__()
        self.config = QSettings()
        self.setWindowTitle("OpenKan")
        self.setWindowIcon(QIcon(ICONE))
        self.resize(1280, 720)
        self.setMinimumSize(980, 560)
        geometria = self.config.value("geometria")
        if geometria is not None:
            self.restoreGeometry(geometria)

        traducao.definir_idioma(
            self.config.value("idioma", "", type=str) or traducao.idioma_do_sistema()
        )
        self.idioma = traducao.idioma_atual()

        # ---- estado
        self.worker: CameraWorker | None = None
        self.gravador: gravacao.GravadorVideo | None = None
        self._procura: ProcuraCameras | None = None
        self._cameras: list[dict] = []
        self.camera_atual: str | None = None
        self.nome_camera = ""
        self.info_camera = ""
        self.indice_efeito = self.config.value("efeito", 0, type=int)
        if not 0 <= self.indice_efeito < len(efeitos.EFEITOS):
            self.indice_efeito = 0
        self._rotacao = self.config.value("rotacao", 0, type=int)
        self._espelhar_h = self.config.value("espelho_h", False, type=bool)
        self._espelhar_v = self.config.value("espelho_v", False, type=bool)
        # Ajustes de imagem por software (funcionam com qualquer câmera):
        # guardados em unidades do slider (100 = ×1,0 / 0 = neutro).
        self._ajustes_img = {
            "ganho": self.config.value("ajuste_ganho", 100, type=int) * 0.01,
            "brilho": float(self.config.value("ajuste_brilho", 0, type=int)),
            "contraste": self.config.value("ajuste_contraste", 100, type=int) * 0.01,
            "saturacao": self.config.value("ajuste_saturacao", 100, type=int) * 0.01,
        }
        self._qps = self.config.value("qps", 0, type=int)  # 0 = nativa
        self._fontes_audio: list[str] = []
        self._estado_preview = "procurando"
        self._gravando = False
        self._gravacao_parando = False
        self._pulso_atual = True
        self._animacao_preview = None
        self._fps_contador = 0
        self._cronometro_fps = QElapsedTimer()
        self._cronometro_gravacao = QElapsedTimer()
        self._trabalhos_foto: list[salvar_foto.FotoTrabalho] = []

        self._montar_menu()
        self._montar_ui()
        self._montar_timer()
        self.setStyleSheet(ESTILO)
        self._aplicar_preferencias_iniciais()
        self.atualizar_lista_cameras()

    # ================================================== menu

    def _montar_menu(self) -> None:
        menu_arquivo = self.menuBar().addMenu(t("menu.arquivo"))
        self._menu_arquivo = menu_arquivo

        self._acao_salvar = QAction(t("menu.salvar_foto_como"), self)
        self._acao_salvar.setShortcut("Ctrl+Shift+S")
        self._acao_salvar.triggered.connect(self.salvar_foto_como)
        menu_arquivo.addAction(self._acao_salvar)

        self._acao_abrir_fotos = QAction(t("menu.abrir_fotos"), self)
        self._acao_abrir_fotos.triggered.connect(lambda: self._abrir_pasta("fotos"))
        menu_arquivo.addAction(self._acao_abrir_fotos)

        self._acao_abrir_videos = QAction(t("menu.abrir_videos"), self)
        self._acao_abrir_videos.triggered.connect(lambda: self._abrir_pasta("videos"))
        menu_arquivo.addAction(self._acao_abrir_videos)

        menu_arquivo.addSeparator()

        self._acao_sair = QAction(t("menu.sair"), self)
        self._acao_sair.setShortcut("Ctrl+Q")
        self._acao_sair.triggered.connect(self.close)
        menu_arquivo.addAction(self._acao_sair)

        menu_idioma = self.menuBar().addMenu(t("menu.idioma"))
        self._menu_idioma = menu_idioma
        self._acoes_idioma: dict[str, QAction] = {}
        for codigo, nome in traducao.IDIOMAS.items():
            acao = QAction(nome, self)
            acao.setCheckable(True)
            acao.setChecked(codigo == traducao.idioma_atual())
            acao.triggered.connect(lambda _=False, c=codigo: self._definir_idioma(c))
            menu_idioma.addAction(acao)
            self._acoes_idioma[codigo] = acao

        menu_ajuda = self.menuBar().addMenu(t("menu.ajuda"))
        self._menu_ajuda = menu_ajuda
        acao_sobre = QAction(t("menu.sobre"), self)
        acao_sobre.setShortcut("F1")
        acao_sobre.triggered.connect(self._mostrar_sobre)
        menu_ajuda.addAction(acao_sobre)

        menu_ajuda.addSeparator()
        self._acao_apoiar = QAction(t("menu.apoiar"), self)
        self._acao_apoiar.triggered.connect(
            lambda: QDesktopServices.openUrl(QUrl(LINK_KOFI))
        )
        menu_ajuda.addAction(self._acao_apoiar)
        self._acao_discord = QAction(t("menu.discord"), self)
        self._acao_discord.triggered.connect(
            lambda: QDesktopServices.openUrl(QUrl(LINK_DISCORD))
        )
        menu_ajuda.addAction(self._acao_discord)

    # ================================================== construção da UI

    def _montar_ui(self) -> None:
        central = QWidget()
        raiz = QHBoxLayout(central)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(0)

        # Divisor arrastável: barra lateral | vídeo | painel de controles.
        # O usuário pode redimensionar cada coluna; as posições são lembradas.
        self._divisor = QSplitter(Qt.Orientation.Horizontal)
        self._divisor.setObjectName("divisorPrincipal")
        self._divisor.setHandleWidth(3)
        self._divisor.setChildrenCollapsible(False)
        self._divisor.addWidget(self._montar_barra_lateral())
        self._divisor.addWidget(self._montar_area_central())

        self.painel_controles = PainelControles()
        self.painel_controles.aplicacao_falhou.connect(
            lambda nome, erro: self.statusBar().showMessage(
                t("controles.falha_aplicar", nome=nome, erro=erro), 6000
            )
        )
        self.painel_controles.leitura_pedida.connect(self._reler_controles)
        self.painel_controles.ajuste_alterado.connect(self._ao_ajuste_software)
        self.painel_controles.definir_ajustes_iniciais(self._brutos_ajustes())
        self._divisor.addWidget(self.painel_controles)

        self._divisor.setStretchFactor(0, 0)
        self._divisor.setStretchFactor(1, 1)
        self._divisor.setStretchFactor(2, 0)
        self._divisor.setSizes([300, 640, 312])
        divisores_salvos = self.config.value("divisores")
        if divisores_salvos is not None:
            self._divisor.restoreState(divisores_salvos)
        self._divisor.splitterMoved.connect(lambda *_: self._remostrar_quadro())

        raiz.addWidget(self._divisor, 1)
        self.setCentralWidget(central)

        self._rotulo_status = QLabel("—")
        self.statusBar().addPermanentWidget(self._rotulo_status)
        self.statusBar().showMessage(t("status.bemvindo"))

    def _montar_barra_lateral(self) -> QFrame:
        barra = QFrame()
        barra.setObjectName("barraLateral")
        barra.setMinimumWidth(252)
        barra.setMaximumWidth(430)

        conteudo = QWidget()
        conteudo.setObjectName("conteudoLateral")
        coluna = QVBoxLayout(conteudo)
        coluna.setContentsMargins(14, 14, 14, 14)
        coluna.setSpacing(10)

        titulo = QLabel("OpenKan")
        titulo.setObjectName("tituloApp")
        self._subtitulo = QLabel(t("app.subtitulo"))
        self._subtitulo.setObjectName("subtituloApp")
        coluna.addWidget(titulo)
        coluna.addWidget(self._subtitulo)
        coluna.addSpacing(6)

        linha_fontes = QHBoxLayout()
        self._rotulo_fontes = QLabel(t("fontes.titulo"))
        self._rotulo_fontes.setObjectName("rotuloSecao")
        linha_fontes.addWidget(self._rotulo_fontes)
        linha_fontes.addStretch(1)
        self.botao_atualizar = PushButton(FIF.SYNC, t("fontes.atualizar"))
        self.botao_atualizar.setObjectName("botaoAtualizar")
        self.botao_atualizar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.botao_atualizar.clicked.connect(self.atualizar_lista_cameras)
        linha_fontes.addWidget(self.botao_atualizar)
        coluna.addLayout(linha_fontes)

        self.lista_cameras = QListWidget()
        self.lista_cameras.currentRowChanged.connect(self._ao_trocar_linha)
        self.lista_cameras.setMinimumHeight(110)
        coluna.addWidget(self.lista_cameras, 1)

        self._rotulo_efeitos = QLabel(t("efeitos.titulo"))
        self._rotulo_efeitos.setObjectName("rotuloSecao")
        coluna.addWidget(self._rotulo_efeitos)

        grade = GradeFluxo(espacamento=8)
        self._grupo_efeitos = QButtonGroup(self)
        self._grupo_efeitos.setExclusive(True)
        self._botoes_efeito: list[QPushButton] = []
        for indice, (_chave, chave_traducao, _funcao) in enumerate(efeitos.EFEITOS):
            botao = QPushButton(t(chave_traducao))
            botao.setObjectName("botaoEfeito")
            botao.setMinimumSize(104, 36)
            botao.setCheckable(True)
            botao.setCursor(Qt.CursorShape.PointingHandCursor)
            botao.setToolTip(t("efeito.tooltip", nome=t(chave_traducao)))
            botao.clicked.connect(
                lambda _=False, i=indice: self.definir_efeito(i)
            )
            self._grupo_efeitos.addButton(botao, indice)
            self._botoes_efeito.append(botao)
            grade.addWidget(botao)
        self._grupo_efeitos.button(self.indice_efeito).setChecked(True)
        coluna.addLayout(grade)

        self._rotulo_orientacao = QLabel(t("orientacao.titulo"))
        self._rotulo_orientacao.setObjectName("rotuloSecao")
        coluna.addWidget(self._rotulo_orientacao)

        linha_orientacao = QHBoxLayout()
        self._combo_rotacao = ComboBox()
        for valor in (0, 90, 180, 270):
            self._combo_rotacao.addItem(f"{valor}°", userData=valor)
        self._combo_rotacao.currentIndexChanged.connect(self._ao_mudar_rotacao)
        linha_orientacao.addWidget(self._combo_rotacao, 1)

        self._check_espelhar_h = SwitchButton("H")
        self._check_espelhar_h.setToolTip(t("orientacao.espelhar_h"))
        self._check_espelhar_h.setChecked(self._espelhar_h)
        self._check_espelhar_h.checkedChanged.connect(
            lambda _ligado: self._ao_mudar_espelho()
        )
        linha_orientacao.addWidget(self._check_espelhar_h)

        self._check_espelhar_v = SwitchButton("V")
        self._check_espelhar_v.setToolTip(t("orientacao.espelhar_v"))
        self._check_espelhar_v.setChecked(self._espelhar_v)
        self._check_espelhar_v.checkedChanged.connect(
            lambda _ligado: self._ao_mudar_espelho()
        )
        linha_orientacao.addWidget(self._check_espelhar_v)
        coluna.addLayout(linha_orientacao)

        # ---- captura: taxa de quadros pedida ao driver
        self._rotulo_captura = QLabel(t("captura.titulo"))
        self._rotulo_captura.setObjectName("rotuloSecao")
        coluna.addWidget(self._rotulo_captura)

        linha_qps = QHBoxLayout()
        self._rotulo_qps = QLabel(t("captura.qps"))
        self._rotulo_qps.setToolTip(t("captura.qps_tooltip"))
        linha_qps.addWidget(self._rotulo_qps)
        self._combo_qps = ComboBox()
        self._combo_qps.addItem(t("captura.nativa"), userData=0)
        for valor_qps in (15, 20, 24, 30, 60):
            self._combo_qps.addItem(str(valor_qps), userData=valor_qps)
        self._combo_qps.setToolTip(t("captura.qps_tooltip"))
        indice_qps = self._combo_qps.findData(self._qps)
        if indice_qps >= 0:
            self._combo_qps.setCurrentIndex(indice_qps)
        self._combo_qps.currentIndexChanged.connect(self._ao_mudar_qps)
        linha_qps.addWidget(self._combo_qps, 1)
        coluna.addLayout(linha_qps)

        # ---- apoio ao projeto (discreto, no rodapé da barra lateral)
        coluna.addSpacing(4)
        self.botao_doar = QPushButton(t("apoio.botao"))
        self.botao_doar.setObjectName("botaoDoar")
        self.botao_doar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.botao_doar.setToolTip(t("apoio.dica"))
        self.botao_doar.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(LINK_KOFI))
        )
        coluna.addWidget(self.botao_doar)

        # ---- rolagem: a barra lateral inteira se adapta a janelas baixas
        rolagem = QScrollArea()
        rolagem.setObjectName("rolagemLateral")
        rolagem.setWidgetResizable(True)
        rolagem.setFrameShape(QFrame.Shape.NoFrame)
        rolagem.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        rolagem.setWidget(conteudo)
        caixa = QVBoxLayout(barra)
        caixa.setContentsMargins(0, 0, 0, 0)
        caixa.addWidget(rolagem)
        return barra

    def _montar_area_central(self) -> QWidget:
        area = QVBoxLayout()
        area.setContentsMargins(16, 16, 16, 12)
        area.setSpacing(8)

        self._rotulo_preview = QLabel(t("fontes.procurando"))
        self._rotulo_preview.setObjectName("areaPreview")
        self._rotulo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._rotulo_preview.setWordWrap(True)
        self._rotulo_preview.setMinimumSize(240, 170)
        self._rotulo_preview.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        area.addWidget(self._rotulo_preview, 1)

        # Flash branco da captura de foto (animação de opacidade)
        self._flash = QLabel(self._rotulo_preview)
        self._flash.setObjectName("flashFoto")
        self._flash.setStyleSheet(
            "#flashFoto { background: rgba(255,255,255,0.92); border-radius: 12px; }"
        )
        self._flash.hide()

        self._rotulo_info = QLabel(t("fontes.sem_camera"))
        self._rotulo_info.setObjectName("rotuloInfo")
        self._rotulo_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._rotulo_info.setWordWrap(True)
        area.addWidget(self._rotulo_info)

        area.addWidget(self._montar_barra_ajustes())

        linha_botoes = QHBoxLayout()
        linha_botoes.addStretch(1)
        self.botao_gravar = QPushButton(t("captura.video_botao"))
        self.botao_gravar.setObjectName("botaoGravar")
        self.botao_gravar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.botao_gravar.setEnabled(False)
        self.botao_gravar.clicked.connect(self._alternar_gravacao)
        linha_botoes.addWidget(self.botao_gravar)

        linha_botoes.addSpacing(14)

        self.botao_foto = QPushButton(t("captura.foto_botao"))
        self.botao_foto.setObjectName("botaoFoto")
        self.botao_foto.setCursor(Qt.CursorShape.PointingHandCursor)
        self.botao_foto.setEnabled(False)
        self.botao_foto.clicked.connect(self.capturar_foto)
        linha_botoes.addWidget(self.botao_foto)
        linha_botoes.addStretch(1)
        area.addLayout(linha_botoes)

        conteudo = QWidget()
        conteudo.setLayout(area)
        return conteudo

    def _montar_barra_ajustes(self) -> QFrame:
        barra = QFrame()
        barra.setObjectName("barraAjustes")
        grade = QGridLayout(barra)
        grade.setContentsMargins(10, 8, 10, 8)
        grade.setHorizontalSpacing(6)
        grade.setVerticalSpacing(6)

        def pequeno_rotulo(texto: str) -> QLabel:
            rotulo = QLabel(texto)
            rotulo.setObjectName("rotuloSecao")
            return rotulo

        # ---- linha 1: FOTO
        self._secao_foto = pequeno_rotulo(t("captura.secao_foto"))
        grade.addWidget(self._secao_foto, 0, 0)

        self._rotulo_formato = QLabel(t("captura.formato") + ":")
        grade.addWidget(self._rotulo_formato, 0, 1)
        self._combo_foto_formato = ComboBox()
        self._combo_foto_formato.addItem("PNG", userData="png")
        self._combo_foto_formato.addItem("JPEG", userData="jpg")
        self._combo_foto_formato.setMinimumWidth(88)
        self._combo_foto_formato.currentIndexChanged.connect(self._salvar_ajustes)
        grade.addWidget(self._combo_foto_formato, 0, 2)

        self._rotulo_tamanho = QLabel(t("captura.tamanho") + ":")
        grade.addWidget(self._rotulo_tamanho, 0, 3)
        self._combo_foto_tamanho = ComboBox()
        self._combo_foto_tamanho.setMinimumWidth(88)
        self._combo_foto_tamanho.currentIndexChanged.connect(self._salvar_ajustes)
        grade.addWidget(self._combo_foto_tamanho, 0, 4)

        self._botao_pasta_foto = TransparentToolButton(FIF.FOLDER_ADD)
        self._botao_pasta_foto.setCursor(Qt.CursorShape.PointingHandCursor)
        self._botao_pasta_foto.clicked.connect(self._escolher_pasta_foto)
        grade.addWidget(self._botao_pasta_foto, 0, 5)
        grade.setColumnStretch(6, 1)

        # ---- linha 2: VÍDEO
        self._secao_video = pequeno_rotulo(t("captura.secao_video"))
        grade.addWidget(self._secao_video, 1, 0)

        self._rotulo_contenedor = QLabel(t("captura.formato") + ":")
        grade.addWidget(self._rotulo_contenedor, 1, 1)
        self._combo_contenedor = ComboBox()
        self._combo_contenedor.addItem("MP4", userData="mp4")
        self._combo_contenedor.addItem("MKV", userData="mkv")
        self._combo_contenedor.addItem("AVI", userData="avi")
        self._combo_contenedor.addItem("WebM", userData="webm")
        self._combo_contenedor.setMinimumWidth(88)
        self._combo_contenedor.currentIndexChanged.connect(self._salvar_ajustes)
        grade.addWidget(self._combo_contenedor, 1, 2)

        self._rotulo_resolucao = QLabel(t("captura.resolucao") + ":")
        grade.addWidget(self._rotulo_resolucao, 1, 3)
        self._combo_resolucao = ComboBox()
        self._combo_resolucao.setMinimumWidth(96)
        self._combo_resolucao.currentIndexChanged.connect(self._salvar_ajustes)
        grade.addWidget(self._combo_resolucao, 1, 4)

        self._botao_pasta_video = TransparentToolButton(FIF.FOLDER_ADD)
        self._botao_pasta_video.setCursor(Qt.CursorShape.PointingHandCursor)
        self._botao_pasta_video.clicked.connect(self._escolher_pasta_video)
        grade.addWidget(self._botao_pasta_video, 1, 5)

        # ---- linha 3: áudio da gravação (linha própria = cabível em janelas estreitas)
        self._rotulo_audio = QLabel(t("captura.audio") + ":")
        grade.addWidget(self._rotulo_audio, 2, 0)
        self._combo_audio = ComboBox()
        self._combo_audio.setMinimumWidth(110)
        self._combo_audio.currentIndexChanged.connect(self._salvar_ajustes)
        grade.addWidget(self._combo_audio, 2, 1, 1, 5)
        grade.setColumnStretch(6, 1)

        # Combos esticam nos espaços disponíveis (janela larga) e continuam
        # usáveis em janelas estreitas.
        for combo in (
            self._combo_foto_formato, self._combo_foto_tamanho,
            self._combo_contenedor, self._combo_resolucao, self._combo_audio,
        ):
            combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        grade.setColumnStretch(2, 2)
        grade.setColumnStretch(4, 2)

        self._preencher_combos_ajustes()
        return barra

    # ================================================== ajustes (combos)

    def _preencher_combos_ajustes(self) -> None:
        itens_tamanho = [(t("captura.nativa"), 0)] + TAMANHOS_FOTO
        self._preencher_combo(
            self._combo_foto_tamanho, itens_tamanho,
            self.config.value("foto_tamanho", 0, type=int),
        )

        itens_resolucao = [(t("captura.nativa"), None)] + RESOLUCOES_VIDEO
        valor_salvo = self.config.value("video_resolucao", "", type=str)
        atual = None
        if valor_salvo:
            try:
                larg, alt = valor_salvo.split("x")
                atual = (int(larg), int(alt))
            except ValueError:
                atual = None
        self._preencher_combo(self._combo_resolucao, itens_resolucao, atual)

        indice_formato = self._combo_foto_formato.findData(
            self.config.value("foto_formato", "png", type=str)
        )
        if indice_formato >= 0:
            self._combo_foto_formato.setCurrentIndex(indice_formato)
        indice_contenedor = self._combo_contenedor.findData(
            self.config.value("video_contenedor", "mp4", type=str)
        )
        if indice_contenedor >= 0:
            self._combo_contenedor.setCurrentIndex(indice_contenedor)

        self._atualizar_fontes_audio()

    def _preencher_combo(self, combo: ComboBox, itens: list, dado_atual) -> None:
        combo.blockSignals(True)
        combo.clear()
        indice_selecao = 0
        for i, (rotulo, dado) in enumerate(itens):
            combo.addItem(rotulo, userData=dado)
            if dado == dado_atual:
                indice_selecao = i
        combo.setCurrentIndex(indice_selecao)
        combo.blockSignals(False)

    def _atualizar_fontes_audio(self) -> None:
        self._fontes_audio = gravacao.listar_fontes_audio()
        fonte_salva = self.config.value("audio_fonte", "", type=str)
        itens = [(t("captura.audio_sem"), "")]
        for fonte in self._fontes_audio:
            rotulo = (
                t("captura.audio_monitor", nome=fonte)
                if fonte.endswith(".monitor")
                else fonte
            )
            itens.append((rotulo, fonte))
        self._preencher_combo(self._combo_audio, itens, fonte_salva)

    def _salvar_ajustes(self) -> None:
        self.config.setValue("foto_formato", self._combo_foto_formato.currentData())
        self.config.setValue("foto_tamanho", self._combo_foto_tamanho.currentData() or 0)
        self.config.setValue("video_contenedor", self._combo_contenedor.currentData())
        resolucao = self._combo_resolucao.currentData()
        self.config.setValue(
            "video_resolucao", f"{resolucao[0]}x{resolucao[1]}" if resolucao else ""
        )
        self.config.setValue("audio_fonte", self._combo_audio.currentData() or "")

    def _aplicar_preferencias_iniciais(self) -> None:
        self._atualizar_tooltips_pasta()

    # ================================================== pastas de mídia

    def _pasta_fotos_atual(self) -> str:
        """Pasta de fotos: a escolhida ou a padrão (<Imagens>/OpenKan)."""
        custom = self.config.value("pasta_fotos", "", type=str) or None
        try:
            return salvar_foto.pasta_fotos(custom)
        except OSError:
            return salvar_foto.pasta_fotos()

    def _pasta_videos_atual(self) -> str:
        """Pasta de vídeos: a escolhida ou a padrão (<Vídeos>/OpenKan)."""
        custom = self.config.value("pasta_videos", "", type=str) or None
        try:
            return salvar_foto.pasta_videos(custom)
        except OSError:
            return salvar_foto.pasta_videos()

    def _atualizar_tooltips_pasta(self) -> None:
        self._botao_pasta_foto.setToolTip(
            t("captura.pasta_foto") + "\n" + t("captura.pasta_atual", pasta=self._pasta_fotos_atual())
        )
        self._botao_pasta_video.setToolTip(
            t("captura.pasta_video") + "\n" + t("captura.pasta_atual", pasta=self._pasta_videos_atual())
        )

    def _escolher_pasta_foto(self) -> None:
        pasta = QFileDialog.getExistingDirectory(
            self, t("captura.pasta_foto"), self._pasta_fotos_atual()
        )
        if not pasta:
            return
        self.config.setValue("pasta_fotos", pasta)
        self._atualizar_tooltips_pasta()
        InfoBar.success(
            t("info.pasta_ok"), pasta, duration=3000,
            position=InfoBarPosition.TOP, parent=self,
        )

    def _escolher_pasta_video(self) -> None:
        pasta = QFileDialog.getExistingDirectory(
            self, t("captura.pasta_video"), self._pasta_videos_atual()
        )
        if not pasta:
            return
        self.config.setValue("pasta_videos", pasta)
        self._atualizar_tooltips_pasta()
        InfoBar.success(
            t("info.pasta_ok"), pasta, duration=3000,
            position=InfoBarPosition.TOP, parent=self,
        )

    def _abrir_pasta(self, tipo: str) -> None:
        """Abre no gerenciador de arquivos a pasta de fotos ou de vídeos."""
        pasta = self._pasta_fotos_atual() if tipo == "fotos" else self._pasta_videos_atual()
        try:
            os.makedirs(pasta, exist_ok=True)
        except OSError:
            pass
        QDesktopServices.openUrl(QUrl.fromLocalFile(pasta))

    # ================================================== câmeras

    def atualizar_lista_cameras(self) -> None:
        if self._procura is not None and self._procura.isRunning():
            return
        self.botao_atualizar.setEnabled(False)
        self.lista_cameras.blockSignals(True)
        self.lista_cameras.clear()
        self.lista_cameras.blockSignals(False)
        self._cameras = []
        self._definir_estado_preview("procurando")
        self._atualizar_fontes_audio()
        self._procura = ProcuraCameras(self)
        self._procura.cameras_prontas.connect(self._ao_achar_cameras)
        self._procura.start()

    def _ao_achar_cameras(self, cameras: list) -> None:
        self.botao_atualizar.setEnabled(True)
        self._cameras = list(cameras)

        if not self._cameras:
            self._definir_estado_preview("nenhuma")
            self._rotulo_info.setText(t("fontes.sem_camera"))
            self._rotulo_status.setText("—")
            self.painel_controles.definir_camera(None)
            return

        self.lista_cameras.blockSignals(True)
        for cam in self._cameras:
            self._adicionar_item_camera(cam)
        self.lista_cameras.blockSignals(False)

        camera_salva = self.config.value("camera", "", type=str)
        linha = 0
        for i, cam in enumerate(self._cameras):
            if cam["caminho"] == camera_salva:
                linha = i
                break
        self.lista_cameras.setCurrentRow(linha)

    def _adicionar_item_camera(self, cam: dict) -> None:
        item = QListWidgetItem()
        widget = QWidget()
        coluna = QVBoxLayout(widget)
        coluna.setContentsMargins(8, 6, 8, 6)
        coluna.setSpacing(0)
        nome = QLabel(cam["nome"])
        nome.setObjectName("itemNome")
        caminho = QLabel(cam["caminho"])
        caminho.setObjectName("itemCaminho")
        coluna.addWidget(nome)
        coluna.addWidget(caminho)
        item.setSizeHint(widget.sizeHint())
        self.lista_cameras.addItem(item)
        self.lista_cameras.setItemWidget(item, widget)

    def _ao_trocar_linha(self, linha: int) -> None:
        if 0 <= linha < len(self._cameras):
            self.trocar_camera(self._cameras[linha])

    def trocar_camera(self, cam: dict) -> None:
        if (
            self.camera_atual == cam["caminho"]
            and self.worker is not None
            and self.worker.isRunning()
        ):
            return

        self.camera_atual = cam["caminho"]
        self.nome_camera = cam["nome"]
        self.config.setValue("camera", cam["caminho"])
        if self.worker is not None:
            self.worker.receptor = None
            self.worker.parar()
            self.worker = None

        self._definir_estado_preview("iniciando")
        self.painel_controles.definir_camera(cam["caminho"])
        self._atualizar_info()

        self.worker = CameraWorker(
            cam, self.indice_efeito, self,
            qps_alvo=float(self._qps) if self._qps else None,
        )
        self.worker.definir_orientacao(self._rotacao, self._espelhar_h, self._espelhar_v)
        self.worker.definir_ajustes(dict(self._ajustes_img))
        self.worker.camera_pronta.connect(self._ao_camera_pronta)
        self.worker.falha.connect(self._ao_falha_camera)
        self.worker.start()

    def _ao_camera_pronta(self, descricao: str) -> None:
        self.info_camera = descricao
        self.botao_foto.setEnabled(True)
        self.botao_gravar.setEnabled(not self._gravando)
        self._definir_estado_preview("pronto")
        self._atualizar_info()
        self._rotulo_status.setText(descricao)
        self.statusBar().showMessage(t("status.camera_iniciada"), 3000)
        self._animar_entrada_preview()

    def _animar_entrada_preview(self) -> None:
        """Pequeno fade-in do preview quando a câmera fica pronta."""
        efeito = QGraphicsOpacityEffect(self._rotulo_preview)
        animacao = QPropertyAnimation(efeito, b"opacity", self)
        animacao.setDuration(300)
        animacao.setStartValue(0.0)
        animacao.setEndValue(1.0)
        self._rotulo_preview.setGraphicsEffect(efeito)
        self._animacao_preview = animacao  # evita coleta antes do fim
        animacao.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

    def _ao_falha_camera(self, codigo: str) -> None:
        caminho = self.camera_atual or ""
        if self.worker is not None:
            self.worker.parar()
            self.worker = None
        self.camera_atual = None
        self.info_camera = ""
        self._rotulo_status.setText("—")
        self._definir_estado_preview("falha")
        self._rotulo_info.setText(t("fontes.sem_camera"))
        if self.gravador is not None:
            self.gravador.parar()
        textos = {
            "abrir": "erro.camera_abrir",
            "quadros": "erro.camera_quadros",
            "parou": "erro.camera_parou",
        }
        chave = textos.get(codigo, "fontes.falha")
        QMessageBox.warning(self, "OpenKan", t(chave, caminho=caminho))

    def _definir_estado_preview(self, estado: str) -> None:
        self._estado_preview = estado
        if estado == "pronto":
            return
        textos = {
            "procurando": "fontes.procurando",
            "nenhuma": "fontes.nenhuma",
            "iniciando": "fontes.iniciando",
            "falha": "fontes.falha",
        }
        self._rotulo_preview.clear()
        self._rotulo_preview.setText(t(textos[estado]))
        self.botao_foto.setEnabled(False)
        if not self._gravando:
            self.botao_gravar.setEnabled(False)

    def _atualizar_info(self) -> None:
        partes = []
        if self.nome_camera:
            partes.append(self.nome_camera)
        if self.camera_atual:
            partes.append(self.camera_atual)
        if self.info_camera:
            partes.append(self.info_camera)
        self._rotulo_info.setText(" • ".join(partes) if partes else t("fontes.sem_camera"))

    def _reler_controles(self, caminho: str) -> None:
        if caminho == self.camera_atual:
            self.painel_controles.definir_camera(caminho)

    # ================================================== efeitos e orientação

    def definir_efeito(self, indice: int) -> None:
        self.indice_efeito = indice
        self.config.setValue("efeito", indice)
        if self.worker is not None:
            self.worker.definir_efeito(indice)
        chave = efeitos.EFEITOS[indice][1]
        self.statusBar().showMessage(t("status.efeito", nome=t(chave)), 3000)

    def _ao_mudar_rotacao(self, _indice: int) -> None:
        self._rotacao = int(self._combo_rotacao.currentData() or 0)
        self.config.setValue("rotacao", self._rotacao)
        if self.worker is not None:
            self.worker.definir_orientacao(self._rotacao, self._espelhar_h, self._espelhar_v)

    def _ao_mudar_espelho(self) -> None:
        self._espelhar_h = self._check_espelhar_h.isChecked()
        self._espelhar_v = self._check_espelhar_v.isChecked()
        self.config.setValue("espelho_h", self._espelhar_h)
        self.config.setValue("espelho_v", self._espelhar_v)
        if self.worker is not None:
            self.worker.definir_orientacao(self._rotacao, self._espelhar_h, self._espelhar_v)

    # ================================================== captura (qps) e ajustes

    def _ao_mudar_qps(self, _indice: int) -> None:
        self._qps = int(self._combo_qps.currentData() or 0)
        self.config.setValue("qps", self._qps)
        self._reiniciar_worker()

    def _reiniciar_worker(self) -> None:
        """Reinicia a câmera ativa (ex.: nova taxa de quadros pedida)."""
        if self.worker is None or not self.camera_atual:
            return
        if self._procura is not None and self._procura.isRunning():
            return
        cam = next(
            (c for c in self._cameras if c["caminho"] == self.camera_atual), None
        )
        if cam is None:
            return
        self.worker.parar()
        self.worker = None
        self.trocar_camera(cam)

    def _brutos_ajustes(self) -> dict[str, int]:
        """Ajustes de software em unidades de slider (100 = ×1,0)."""
        return {
            "ganho": int(round(self._ajustes_img["ganho"] * 100)),
            "brilho": int(round(self._ajustes_img["brilho"])),
            "contraste": int(round(self._ajustes_img["contraste"] * 100)),
            "saturacao": int(round(self._ajustes_img["saturacao"] * 100)),
        }

    def _ao_ajuste_software(self, chave: str, valor: float) -> None:
        """Slider de imagem mexido: aplica ao worker ao vivo e persiste."""
        self._ajustes_img[chave] = valor
        bruto = int(round(valor * (1.0 if chave == "brilho" else 100.0)))
        self.config.setValue(f"ajuste_{chave}", bruto)
        if self.worker is not None:
            self.worker.definir_ajustes(dict(self._ajustes_img))

    # ================================================== renderização

    def _montar_timer(self) -> None:
        self._timer = QTimer(self)
        self._timer.setInterval(INTERVALO_RENDER_MS)
        self._timer.timeout.connect(self._ao_tique)
        self._timer.start()

    def _ao_tique(self) -> None:
        quadro = self.worker.ultimo_quadro() if self.worker is not None else None
        if quadro is not None:
            self._mostrar_quadro(quadro)
            self._fps_contador += 1
            if not self._cronometro_fps.isValid():
                self._cronometro_fps.start()
            elif self._cronometro_fps.elapsed() >= 1000:
                qps = self._fps_contador * 1000.0 / self._cronometro_fps.elapsed()
                base = self.info_camera or "—"
                self._rotulo_status.setText(f"{base} • {qps:.0f} {t('qps')}")
                self._cronometro_fps.restart()
                self._fps_contador = 0

        if self._gravando and self._cronometro_gravacao.isValid():
            segundos = int(self._cronometro_gravacao.elapsed() / 1000)
            tempo = f"{segundos // 60}:{segundos % 60:02d}"
            self.botao_gravar.setText(f"{t('captura.video_parar')} ({tempo})")
            # Pulso da borda do preview: alterna a cada 500 ms entre o
            # vermelho sangue vivo e o tom escuro (propriedade QSS).
            pulso = (self._cronometro_gravacao.elapsed() // 500) % 2 == 0
            if pulso != self._pulso_atual:
                self._pulso_atual = pulso
                self._rotulo_preview.setProperty("pulso", pulso)
                self._reestilizar(self._rotulo_preview)

    def _mostrar_quadro(self, quadro: np.ndarray) -> None:
        altura, largura = quadro.shape[:2]
        rgb = cv2.cvtColor(quadro, cv2.COLOR_BGR2RGB)
        imagem = QImage(
            rgb.data, largura, altura, largura * 3, QImage.Format.Format_RGB888
        )
        pixmap = QPixmap.fromImage(imagem)
        self._rotulo_preview.setText("")
        self._rotulo_preview.setPixmap(
            pixmap.scaled(
                self._rotulo_preview.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def resizeEvent(self, evento) -> None:  # noqa: N802 (API do Qt)
        super().resizeEvent(evento)
        self._remostrar_quadro()

    def _remostrar_quadro(self, *_args) -> None:
        """Redesenha o último quadro (janela redimensionada ou divisor movido)."""
        if self.worker is not None:
            quadro = self.worker.ultimo_quadro()
            if quadro is not None:
                self._mostrar_quadro(quadro)

    # ================================================== fotos

    def quadro_atual(self):
        return self.worker.ultimo_quadro() if self.worker is not None else None

    def capturar_foto(self) -> None:
        quadro = self.quadro_atual()
        if quadro is None:
            InfoBar.warning(
                t("info.aviso_titulo"), t("info.sem_imagem"), duration=4000,
                position=InfoBarPosition.TOP, parent=self,
            )
            return
        formato = self._combo_foto_formato.currentData() or "png"
        lado_max = self._combo_foto_tamanho.currentData() or 0
        trabalho = salvar_foto.FotoTrabalho(
            quadro, formato, lado_max,
            pasta=self._pasta_fotos_atual(), parent=self,
        )
        trabalho.concluida.connect(self._ao_foto_salva)
        trabalho.falhou.connect(self._ao_foto_falhou)
        self._trabalhos_foto.append(trabalho)
        trabalho.start()

    def _ao_foto_salva(self, caminho: str) -> None:
        self.statusBar().showMessage(t("status.foto_salva", caminho=caminho), 10000)
        InfoBar.success(
            t("info.foto_titulo"), os.path.basename(caminho), duration=5000,
            position=InfoBarPosition.TOP, parent=self,
        )
        self._piscar_flash()

    def _ao_foto_falhou(self, erro: str) -> None:
        self.statusBar().showMessage(t("erro.foto", erro=erro), 10000)
        InfoBar.error(
            t("info.erro_titulo"), t("erro.foto", erro=erro), duration=8000,
            position=InfoBarPosition.TOP, parent=self,
        )

    def salvar_foto_como(self) -> None:
        quadro = self.quadro_atual()
        if quadro is None:
            InfoBar.warning(
                t("info.aviso_titulo"), t("info.sem_imagem"), duration=4000,
                position=InfoBarPosition.TOP, parent=self,
            )
            return
        formato = self._combo_foto_formato.currentData() or "png"
        sugestao = os.path.join(
            salvar_foto.pasta_fotos(),
            datetime.datetime.now().strftime("foto_%Y%m%d_%H%M%S")
            + salvar_foto.extensao_de(formato),
        )
        caminho, _ = QFileDialog.getSaveFileName(
            self,
            t("menu.salvar_foto_como").replace("&", "").replace("…", ""),
            sugestao,
            "Imagens (*.png *.jpg *.jpeg)",
        )
        if not caminho:
            return
        trabalho = salvar_foto.FotoTrabalho(quadro, caminho=caminho, parent=self)
        trabalho.concluida.connect(self._ao_foto_salva)
        trabalho.falhou.connect(self._ao_foto_falhou)
        self._trabalhos_foto.append(trabalho)
        trabalho.start()

    # ================================================== gravação de vídeo

    def _alternar_gravacao(self) -> None:
        if self.gravador is not None:
            # está gravando → parar
            self._gravacao_parando = True
            self.botao_gravar.setText(t("captura.video_parando"))
            self.botao_gravar.setEnabled(False)
            self.gravador.parar()
            return

        if self.worker is None or not self.worker.isRunning():
            InfoBar.warning(
                t("info.aviso_titulo"), t("info.sem_camera_gravar"), duration=4000,
                position=InfoBarPosition.TOP, parent=self,
            )
            return

        fonte_audio = self._combo_audio.currentData() or None
        contenedor = self._combo_contenedor.currentData() or "mp4"
        resolucao = self._combo_resolucao.currentData()
        qps = self.worker.qps_atual() or 30.0

        pasta = self._pasta_videos_atual()
        self.gravador = gravacao.GravadorVideo(
            pasta, contenedor, resolucao, fonte_audio, qps, parent=self
        )
        self.gravador.gravacao_finalizada.connect(self._ao_gravacao_finalizada)
        self.worker.receptor = self.gravador.aceitar_quadro
        self.gravador.start()

        self._gravando = True
        self._gravacao_parando = False
        self._cronometro_gravacao.restart()
        self._combo_qps.setEnabled(False)  # trocar QPS reiniciaria a câmera
        self.botao_gravar.setProperty("gravando", True)
        self._reestilizar(self.botao_gravar)
        self._rotulo_preview.setProperty("gravando", True)
        self._rotulo_preview.setProperty("pulso", True)
        self._reestilizar(self._rotulo_preview)
        self.statusBar().showMessage(t("status.gravando", tempo="0:00"))

    def _ao_gravacao_finalizada(self, caminho: str, mensagem: str) -> None:
        if self.worker is not None:
            self.worker.receptor = None
        self.gravador = None
        self._gravando = False
        self._gravacao_parando = False
        self.botao_gravar.setProperty("gravando", False)
        self._reestilizar(self.botao_gravar)
        self._rotulo_preview.setProperty("gravando", False)
        self._reestilizar(self._rotulo_preview)
        self.botao_gravar.setText(t("captura.video_botao"))
        self.botao_gravar.setEnabled(self.worker is not None and self.info_camera != "")
        self._combo_qps.setEnabled(True)

        if not caminho:
            QMessageBox.warning(self, "OpenKan", t("erro.gravacao", erro=mensagem))
        elif mensagem:
            self.statusBar().showMessage(
                t("status.gravacao_aviso", caminho=caminho, aviso=mensagem), 12000
            )
            InfoBar.warning(
                t("info.video_titulo"),
                os.path.basename(caminho) + " — " + mensagem,
                duration=8000, position=InfoBarPosition.TOP, parent=self,
            )
        else:
            self.statusBar().showMessage(
                t("status.gravacao_salva", caminho=caminho), 10000
            )
            InfoBar.success(
                t("info.video_titulo"), os.path.basename(caminho), duration=5000,
                position=InfoBarPosition.TOP, parent=self,
            )

    def _piscar_flash(self) -> None:
        """Animação de flash branco no preview ao salvar uma foto."""
        if self._flash is None:
            return
        self._flash.setGeometry(self._rotulo_preview.rect())
        efeito = QGraphicsOpacityEffect(self._flash)
        animacao = QPropertyAnimation(efeito, b"opacity", self._flash)
        animacao.setDuration(220)
        animacao.setStartValue(0.9)
        animacao.setEndValue(0.0)
        animacao.finished.connect(self._flash.hide)
        self._flash.setGraphicsEffect(efeito)
        self._flash.show()
        self._flash.raise_()
        animacao.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

    def _reestilizar(self, widget: QWidget) -> None:
        estilo = widget.style()
        estilo.unpolish(widget)
        estilo.polish(widget)

    # ================================================== idioma e miscelânea

    def _definir_idioma(self, codigo: str) -> None:
        traducao.definir_idioma(codigo)
        self.config.setValue("idioma", codigo)
        self.retraduzir()

    def retraduzir(self) -> None:
        self.idioma = traducao.idioma_atual()
        self.setWindowTitle("OpenKan")
        self._subtitulo.setText(t("app.subtitulo"))
        self._menu_arquivo.setTitle(t("menu.arquivo"))
        self._acao_salvar.setText(t("menu.salvar_foto_como"))
        self._acao_abrir_fotos.setText(t("menu.abrir_fotos"))
        self._acao_abrir_videos.setText(t("menu.abrir_videos"))
        self._acao_sair.setText(t("menu.sair"))
        self._acao_apoiar.setText(t("menu.apoiar"))
        self._acao_discord.setText(t("menu.discord"))
        self._menu_idioma.setTitle(t("menu.idioma"))
        self._menu_ajuda.setTitle(t("menu.ajuda"))
        for codigo, acao in self._acoes_idioma.items():
            acao.setChecked(codigo == self.idioma)
        self._rotulo_fontes.setText(t("fontes.titulo"))
        self.botao_atualizar.setText(t("fontes.atualizar"))
        self.botao_doar.setText(t("apoio.botao"))
        self.botao_doar.setToolTip(t("apoio.dica"))
        self._rotulo_efeitos.setText(t("efeitos.titulo"))
        self._rotulo_orientacao.setText(t("orientacao.titulo"))
        self._rotulo_captura.setText(t("captura.titulo"))
        self._rotulo_qps.setText(t("captura.qps"))
        self._rotulo_qps.setToolTip(t("captura.qps_tooltip"))
        self._combo_qps.setToolTip(t("captura.qps_tooltip"))
        self._combo_qps.setItemText(0, t("captura.nativa"))
        self._check_espelhar_h.setToolTip(t("orientacao.espelhar_h"))
        self._check_espelhar_v.setToolTip(t("orientacao.espelhar_v"))
        for indice, (_chave, chave_traducao, _funcao) in enumerate(efeitos.EFEITOS):
            botao = self._botoes_efeito[indice]
            botao.setText(t(chave_traducao))
            botao.setToolTip(t("efeito.tooltip", nome=t(chave_traducao)))
        self._secao_foto.setText(t("captura.secao_foto"))
        self._secao_video.setText(t("captura.secao_video"))
        self._rotulo_formato.setText(t("captura.formato") + ":")
        self._rotulo_tamanho.setText(t("captura.tamanho") + ":")
        self._rotulo_contenedor.setText(t("captura.formato") + ":")
        self._rotulo_resolucao.setText(t("captura.resolucao") + ":")
        self._rotulo_audio.setText(t("captura.audio") + ":")
        self._atualizar_tooltips_pasta()
        self._preencher_combo(
            self._combo_foto_tamanho,
            [(t("captura.nativa"), 0)] + TAMANHOS_FOTO,
            self._combo_foto_tamanho.currentData(),
        )
        self._preencher_combo(
            self._combo_resolucao,
            [(t("captura.nativa"), None)] + RESOLUCOES_VIDEO,
            self._combo_resolucao.currentData(),
        )
        fonte_atual = self._combo_audio.currentData() or ""
        itens = [(t("captura.audio_sem"), "")]
        for fonte in self._fontes_audio:
            rotulo = (
                t("captura.audio_monitor", nome=fonte)
                if fonte.endswith(".monitor")
                else fonte
            )
            itens.append((rotulo, fonte))
        self._preencher_combo(self._combo_audio, itens, fonte_atual)
        self.botao_foto.setText(t("captura.foto_botao"))
        if not self._gravando and not self._gravacao_parando:
            self.botao_gravar.setText(t("captura.video_botao"))
        self._atualizar_info()
        if self._estado_preview != "pronto":
            self._definir_estado_preview(self._estado_preview)
        self.statusBar().showMessage(t("status.bemvindo"))
        self.painel_controles.retraduzir()

    def _mostrar_sobre(self) -> None:
        QMessageBox.about(self, "OpenKan", t("sobre.texto", versao=VERSAO))

    def closeEvent(self, evento) -> None:  # noqa: N802 (API do Qt)
        self.config.setValue("geometria", self.saveGeometry())
        self.config.setValue("divisores", self._divisor.saveState())
        if self.gravador is not None:
            self.gravador.parar()
            self.gravador.wait(10000)
        if self.worker is not None:
            self.worker.receptor = None
            self.worker.parar()
            self.worker = None
        if self._procura is not None and self._procura.isRunning():
            self._procura.wait(3000)
        super().closeEvent(evento)
