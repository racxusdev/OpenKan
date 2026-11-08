"""Ponto de entrada do OpenKan."""

from __future__ import annotations

import sys


def _silenciar_logs_opencv() -> None:
    """Esconde avisos verbosos do OpenCV (ex.: sondagem de nós de metadados)."""
    try:
        import cv2

        cv2.setLogLevel(cv2.LOG_LEVEL_ERROR)
    except Exception:  # noqa: BLE001 — qualquer falha aqui é inofensiva
        pass


def main() -> int:
    """Cria a aplicação Qt, mostra a janela principal e roda o laço de eventos."""
    _silenciar_logs_opencv()

    from PyQt6.QtWidgets import QApplication

    from qfluentwidgets import Theme, setTheme, setThemeColor
    from PyQt6.QtGui import QColor

    from . import VERSAO
    from .janela import JanelaPrincipal

    app = QApplication(sys.argv)
    app.setApplicationName("OpenKan")
    app.setApplicationDisplayName("OpenKan")
    app.setApplicationVersion(VERSAO)
    app.setOrganizationName("OpenKan")

    # Tema escuro grafite com acento vermelho sangue para os widgets fluentes.
    setTheme(Theme.DARK)
    setThemeColor(QColor("#d0122f"))

    janela = JanelaPrincipal()
    janela.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
