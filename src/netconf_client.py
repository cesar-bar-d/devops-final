"""
netconf_client.py — Consulta de configuración de red via NETCONF (RFC 6241).

NETCONF usa XML sobre SSH para gestionar dispositivos de red de forma segura.

Conexión: CSR1000v en 192.168.56.101 vía 'netconf ssh' (port 22, IOS-XE 16.3).
Este router usa el modelo de datos Cisco PI (cli-config-data-block), que retorna
la configuración en formato CLI dentro de un envelope XML (RFC 6241 base:1.0).
No incluye capabilities YANG avanzadas (propio de IOS-XE 16.3 con 'netconf ssh').
"""
import re
import xml.etree.ElementTree as ET
from ncclient import manager
from typing import Optional
from src.config import get_csr_config

# Tag con namespace del bloque CLI retornado por IOS-XE 16.3 (Cisco PI model)
_CLI_BLOCK_TAG = "{urn:ietf:params:xml:ns:netconf:base:1.0}cli-config-data-block"


def _connect(cfg: dict):
    """Crea una sesión NETCONF con el dispositivo."""
    return manager.connect(
        host=cfg["host"],
        port=cfg["port"],
        username=cfg["user"],
        password=cfg["password"],
        hostkey_verify=False,
        device_params={"name": "iosxe"},
        timeout=15,
    )


def get_capabilities(cfg: Optional[dict] = None) -> list:
    """Retorna las capabilities YANG anunciadas por el dispositivo."""
    if cfg is None:
        cfg = get_csr_config()
    with _connect(cfg) as conn:
        return list(conn.server_capabilities)


def _get_config_text(response_xml: str) -> str:
    """Extrae el texto CLI del envelope XML retornado por IOS-XE 16.3 (Cisco PI model)."""
    root = ET.fromstring(response_xml)
    block = root.find(".//" + _CLI_BLOCK_TAG)
    if block is not None and block.text:
        return block.text
    # Fallback: buscar sin namespace
    for elem in root.iter():
        if "cli-config-data-block" in elem.tag and elem.text:
            return elem.text
    return ""


def get_interfaces_netconf(cfg: Optional[dict] = None) -> list:
    """
    Obtiene interfaces via NETCONF (RFC 6241).
    Usa get-config sobre el datastore 'running' y parsea las secciones
    'interface' del bloque CLI retornado por IOS-XE 16.3 (Cisco PI model).
    """
    if cfg is None:
        cfg = get_csr_config()

    with _connect(cfg) as conn:
        response = conn.get_config(source="running")

    config_text = _get_config_text(str(response))

    result = []
    current: Optional[dict] = None
    for line in config_text.splitlines():
        stripped = line.rstrip()
        if stripped.startswith("interface "):
            current = {
                "nombre": stripped[len("interface "):].strip(),
                "descripcion": "",
                "ip_address": "",
                "ipv6_address": "",
            }
            result.append(current)
        elif current is not None:
            inner = stripped.strip()
            if inner.startswith("description "):
                current["descripcion"] = inner[len("description "):]
            elif inner.startswith("ip address "):
                current["ip_address"] = inner[len("ip address "):]
            elif inner.startswith("ipv6 address ") and not inner.endswith("link-local"):
                current["ipv6_address"] = inner[len("ipv6 address "):]
            elif stripped and not stripped.startswith(" "):
                current = None

    return result


def get_hostname_netconf(cfg: Optional[dict] = None) -> str:
    """Obtiene el hostname del dispositivo via NETCONF (RFC 6241) usando get-config."""
    if cfg is None:
        cfg = get_csr_config()

    with _connect(cfg) as conn:
        response = conn.get_config(source="running")

    config_text = _get_config_text(str(response))
    match = re.search(r"^hostname\s+(\S+)", config_text, re.MULTILINE)
    if match:
        return match.group(1)
    return "desconocido"
