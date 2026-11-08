#!/usr/bin/env bash
# OpenKan — desinstalador
# Remove o programa; as fotos e vídeos salvos são preservados.
# Uso:  bash uninstall.sh
#       bash uninstall.sh --remover-ubuntucam-antigo   (remove também o UbuntuCam v1)
set -euo pipefail

DESTINO="${HOME}/.local/share/openkan"

rm -rf "${DESTINO}"
rm -f  "${HOME}/.local/bin/openkan"
rm -f  "${HOME}/.local/share/applications/openkan.desktop"
rm -f  "${HOME}/.local/share/icons/hicolor/scalable/apps/openkan.svg"

if [[ "${1:-}" == "--remover-ubuntucam-antigo" ]]; then
    rm -rf "${HOME}/.local/share/ubuntucam"
    rm -f  "${HOME}/.local/bin/ubuntucam"
    rm -f  "${HOME}/.local/share/applications/ubuntucam.desktop"
    rm -f  "${HOME}/.local/share/icons/hicolor/scalable/apps/ubuntucam.svg"
    echo "Instalação antiga do UbuntuCam também removida."
fi

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "${HOME}/.local/share/applications" 2>/dev/null || true
fi

echo "OpenKan removido."
echo "Suas fotos continuam na pasta de fotos que você usava."
