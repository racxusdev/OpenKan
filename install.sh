#!/usr/bin/env bash
# =====================================================================
#  OpenKan — instalador para Ubuntu 22.04/24.04 e derivados
#
#  Uso (dentro da pasta do projeto):
#      bash install.sh
#
#  O que ele faz:
#    1. Instala as dependências de sistema via apt (se necessário);
#    2. Cria um ambiente virtual Python em ~/.local/share/openkan/venv;
#    3. Instala PyQt6, PyQt-Fluent-Widgets, OpenCV e NumPy no ambiente;
#    4. Copia o aplicativo para ~/.local/share/openkan/app;
#    5. Cria o comando "openkan" em ~/.local/bin;
#    6. Cria o atalho "OpenKan" no menu de aplicativos (com ícone).
# =====================================================================
set -euo pipefail

COR_VERDE='\033[1;32m'
COR_AMARELO='\033[1;33m'
COR_VERMELHA='\033[1;31m'
COR_RESET='\033[0m'

info()  { echo -e "${COR_VERDE}[info]${COR_RESET} $*"; }
aviso() { echo -e "${COR_AMARELO}[aviso]${COR_RESET} $*"; }
erro()  { echo -e "${COR_VERMELHA}[erro]${COR_RESET} $*" >&2; }

PASTA_ORIGEM="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESTINO="${HOME}/.local/share/openkan"
VENV="${DESTINO}/venv"
APP_DEST="${DESTINO}/app"
BIN_LOCAL="${HOME}/.local/bin"
DESKTOP_LOCAL="${HOME}/.local/share/applications"
ICONS_LOCAL="${HOME}/.local/share/icons/hicolor/scalable/apps"

echo "=============================================="
echo "   OpenKan — instalação"
echo "=============================================="

# ------------------------------------------------- 0) Instalação antiga?
if [[ -d "${HOME}/.local/share/ubuntucam" ]]; then
    aviso "Detectei uma instalação antiga do UbuntuCam."
    aviso "O OpenKan é o novo nome do aplicativo e não conflita com ela."
    aviso "Para liberar espaço, você pode remover a antiga depois com:"
    echo "    rm -rf ~/.local/share/ubuntucam ~/.local/bin/ubuntucam"
    echo "    rm -f ~/.local/share/applications/ubuntucam.desktop"
    echo "    rm -f ~/.local/share/icons/hicolor/scalable/apps/ubuntucam.svg"
    echo ""
fi

# ---------------------------------------------------------------- 1) Python
if ! command -v python3 >/dev/null 2>&1; then
    erro "Python 3 não encontrado."
    erro "Instale com:  sudo apt install python3 python3-venv python3-pip"
    exit 1
fi
VERSAO_PY=$(python3 -c 'import sys; print("{}.{}".format(*sys.version_info[:2]))')
MENOR=$(python3 -c 'import sys; print(1 if sys.version_info < (3, 9) else 0)')
if [[ "${MENOR}" == "1" ]]; then
    erro "Python ${VERSAO_PY} é muito antigo. O OpenKan precisa de Python 3.9+."
    exit 1
fi
info "Python ${VERSAO_PY} encontrado."

# ------------------------------------------------- 2) Pacotes de sistema
PACOTES_APT=(python3-venv python3-pip libgl1 libegl1 libxcb-cursor0 libxkbcommon0 libdbus-1-3 libfontconfig1 v4l-utils ffmpeg pulseaudio-utils)
if [[ "${OPENKAN_SKIP_APT:-0}" == "1" ]]; then
    aviso "OPENKAN_SKIP_APT=1 — instalando pacotes do sistema por conta própria."
elif command -v apt-get >/dev/null 2>&1; then
    faltam=()
    for pacote in "${PACOTES_APT[@]}"; do
        dpkg -s "${pacote}" >/dev/null 2>&1 || faltam+=("${pacote}")
    done
    if [[ ${#faltam[@]} -gt 0 ]]; then
        SUDO=""
        if [[ ${EUID} -ne 0 ]] && command -v sudo >/dev/null 2>&1; then
            SUDO="sudo"
        fi
        info "Instalando dependências de sistema: ${faltam[*]}"
        info "(pode pedir sua senha — é necessário para o apt)"
        ${SUDO} apt-get update -y
        DEBIAN_FRONTEND=noninteractive ${SUDO} apt-get install -y "${faltam[@]}"
    else
        info "Dependências de sistema já presentes."
    fi
else
    aviso "apt-get não encontrado (não parece ser Ubuntu/Debian)."
    aviso "Seguindo sem instalar pacotes de sistema — se algo faltar, instale manualmente."
fi

# ------------------------------------------------- 3) Ambiente virtual
info "Criando ambiente virtual em ${VENV}"
if ! python3 -m venv "${VENV}" 2>/dev/null; then
    erro "Não foi possível criar o ambiente virtual."
    erro "No Ubuntu, instale o pacote:  sudo apt install python3-venv"
    exit 1
fi

export PIP_DISABLE_PIP_VERSION_CHECK=1
export PIP_DEFAULT_TIMEOUT=120
info "Atualizando o pip do ambiente…"
"${VENV}/bin/pip" install --upgrade pip >/dev/null

info "Instalando bibliotecas Python (PyQt6, Fluent-Widgets, OpenCV, NumPy)…"
if ! "${VENV}/bin/pip" install -r "${PASTA_ORIGEM}/requirements.txt"; then
    erro "Falha ao instalar as bibliotecas Python."
    erro "Verifique sua conexão com a internet e rode o instalador novamente."
    exit 1
fi

# ------------------------------------------------- 4) Copiar o aplicativo
info "Copiando o aplicativo para ${APP_DEST}"
mkdir -p "${DESTINO}"
rm -rf "${APP_DEST}"
mkdir -p "${APP_DEST}"
cp -r "${PASTA_ORIGEM}/openkan" "${APP_DEST}/"
cp "${PASTA_ORIGEM}/run.py" "${APP_DEST}/" 2>/dev/null || true
rm -rf "${APP_DEST}/openkan/__pycache__"

# ------------------------------------------------- 5) Comando "openkan"
mkdir -p "${BIN_LOCAL}"
cp "${PASTA_ORIGEM}/openkan-launcher" "${BIN_LOCAL}/openkan"
chmod +x "${BIN_LOCAL}/openkan"

# ------------------------------------------------- 6) Menu e ícone
mkdir -p "${DESKTOP_LOCAL}" "${ICONS_LOCAL}"
cp "${PASTA_ORIGEM}/openkan/recursos/openkan.svg" "${ICONS_LOCAL}/openkan.svg"
sed -e "s|^Exec=.*|Exec=${BIN_LOCAL}/openkan|" \
    -e "s|^TryExec=.*|TryExec=${BIN_LOCAL}/openkan|" \
    -e "s|^Icon=.*|Icon=${ICONS_LOCAL}/openkan.svg|" \
    "${PASTA_ORIGEM}/openkan.desktop" > "${DESKTOP_LOCAL}/openkan.desktop"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "${DESKTOP_LOCAL}" 2>/dev/null || true
fi

# ------------------------------------------------- 7) PATH
case ":${PATH}:" in
    *":${BIN_LOCAL}:"*) ;;
    *)
        aviso "~/.local/bin não está no seu PATH."
        aviso "Para usar o comando 'openkan' no terminal, adicione ao ~/.bashrc:"
        echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
        ;;
esac

echo ""
info "Instalação concluída!"
info "Como abrir:"
info "  • Menu de aplicativos do Ubuntu  ->  OpenKan"
info "  • Ou no terminal:  openkan"
info "Fotos: por padrão em ~/Imagens/OpenKan (trocável na interface)."
info "Vídeos: por padrão em ~/Vídeos/OpenKan (trocável na interface)."
echo ""
