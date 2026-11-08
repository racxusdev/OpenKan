"""Controles manuais da câmera via v4l2-ctl (obturador, ISO, balanço de branco…).

Cada webcam expõe um conjunto diferente de controles V4L2. Este módulo lê a
lista REAL de controles suportados pelo dispositivo (v4l2-ctl --list-ctrls-menus)
e permite alterá-los (v4l2-ctl --set-ctrl). Nomes conhecidos recebem rótulos
traduzidos; os demais aparecem com o nome técnico do kernel.
"""

from __future__ import annotations

import re
import shutil
import subprocess

# Rótulos traduzidos (chaves do módulo traducao)
MAPA_ROTULOS = {
    "exposure_time_absolute": "controle.shutter",
    "gain": "controle.iso",
    "white_balance_temperature": "controle.balanco_branco",
    "white_balance_temperature_auto": "controle.balanco_auto",
    "exposure_auto": "controle.exposicao_auto",
    "zoom_absolute": "controle.zoom",
    "iris_absolute": "controle.iris",
    "focus_absolute": "controle.foco",
    "focus_auto": "controle.foco_auto",
    "brightness": "controle.brilho",
    "contrast": "controle.contraste",
    "saturation": "controle.saturacao",
    "hue": "controle.matiz",
    "sharpness": "controle.nitidez",
    "gamma": "controle.gamma",
    "backlight_compensation": "controle.luz_fundo",
    "power_line_frequency": "controle.freq_rede",
}

# Rótulos de itens de menu conhecidos do kernel
MENU_ROTULOS_CONHECIDOS = {
    "Disabled": "controle.menu.desativado",
    "Manual Mode": None,          # mantido em inglês (valor técnico)
    "Aperture Priority Mode": None,
}

# Configurações internas de drivers de câmeras VIRTUAIS (Iriun, DroidCam,
# v4l2loopback…) que não dizem respeito ao usuário — ficam fora do painel.
CONTROLES_OCULTOS = {
    "keep_format",
    "sustain_framerate",
    "timeout",
}

_PADRAO_LINHA = re.compile(
    r"^\s*(?P<nome>\S+)\s+0x[0-9a-fA-F]+\s+\((?P<tipo>int|bool|menu|button|integer64|bitmask)\)\s*:\s*(?P<atributos>.*)$"
)
_PADRAO_ITEM_MENU = re.compile(r"^\s*(?P<valor>\d+):\s*(?P<rotulo>.+?)\s*$")


def v4l2_ctl_disponivel() -> bool:
    return shutil.which("v4l2-ctl") is not None


def _atributos(texto: str) -> dict:
    valores = {}
    for chave in ("min", "max", "step", "default", "value"):
        m = re.search(rf"\b{chave}=(\S+)", texto)
        if m:
            bruto = m.group(1).rstrip(",")
            try:
                valores[chave] = int(bruto)
            except ValueError:
                valores[chave] = bruto
    valores["inativo"] = "inactive" in texto or "inactive" in texto.split()
    valores["somente_leitura"] = "flags=read-only" in texto or "read-only" in texto
    return valores


def listar_controles(caminho: str) -> list[dict]:
    """Lista os controles do dispositivo; devolve [] se indisponível.

    Cada controle: {'nome','tipo','min','max','step','padrao','valor',
                    'inativo','itens': {valor: rotulo}}
    """
    if not v4l2_ctl_disponivel():
        return []
    try:
        resultado = subprocess.run(
            ["v4l2-ctl", "-d", caminho, "--list-ctrls-menus"],
            capture_output=True, text=True, timeout=6,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if resultado.returncode != 0:
        return []

    controles: list[dict] = []
    atual: dict | None = None
    for linha in resultado.stdout.splitlines():
        item_menu = _PADRAO_ITEM_MENU.match(linha)
        if item_menu and atual is not None and atual["tipo"] == "menu":
            atual["itens"][int(item_menu.group("valor"))] = item_menu.group("rotulo")
            continue

        m = _PADRAO_LINHA.match(linha)
        if not m:
            continue
        if m.group("nome") in CONTROLES_OCULTOS:
            atual = None  # lixo de driver virtual — fora do painel
            continue
        atributos = _atributos(m.group("atributos"))
        atual = {
            "nome": m.group("nome"),
            "tipo": m.group("tipo"),
            "min": atributos.get("min", 0),
            "max": atributos.get("max", 0),
            "step": atributos.get("step", 1) or 1,
            "padrao": atributos.get("default", 0),
            "valor": atributos.get("value", atributos.get("default", 0)),
            "inativo": atributos.get("inativo", False),
            "itens": {},
        }
        controles.append(atual)
    return controles


def definir_controle(caminho: str, nome: str, valor) -> tuple[bool, str]:
    """Aplica um valor; devolve (ok, mensagem_de_erro)."""
    if not v4l2_ctl_disponivel():
        return False, "v4l2-ctl not found"
    try:
        resultado = subprocess.run(
            ["v4l2-ctl", "-d", caminho, "--set-ctrl", f"{nome}={valor}"],
            capture_output=True, text=True, timeout=6,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    if resultado.returncode != 0:
        return False, (resultado.stderr or resultado.stdout).strip() or "error"
    return True, ""


def restaurar_padroes(caminho: str, controles: list[dict]) -> None:
    """Restaura todos os controles para o valor de fábrica (bloqueante)."""
    for controle in controles:
        if controle["tipo"] in ("int", "bool", "menu"):
            try:
                definir_controle(caminho, controle["nome"], controle["padrao"])
            except Exception:
                pass


def rotulo_de(nome: str) -> str:
    """Chave de tradução do controle (ou None se desconhecido)."""
    return MAPA_ROTULOS.get(nome)


def rotulos_de_menu(nome: str, itens: dict[int, str]) -> dict[int, str]:
    """Rótulos de menu com traduções conhecidas aplicadas."""
    from . import traducao

    traduzidos: dict[int, str] = {}
    for valor, rotulo in itens.items():
        chave = MENU_ROTULOS_CONHECIDOS.get(rotulo)
        traduzidos[valor] = traducao.t(chave) if chave else rotulo
    return traduzidos
