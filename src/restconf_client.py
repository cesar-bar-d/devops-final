"""
restconf_client.py — Consulta y configuración de router IOS-XE via RESTCONF.

RESTCONF (RFC 8040) es una API REST sobre HTTPS que expone modelos YANG.
Sandbox utilizado: Cisco DevNet Always-On IOS-XE
  Host: ios-xe-mgmt-latest.cisco.com  |  Puerto: 443
  Credenciales: ver .env.example
"""
import requests
import urllib3
from typing import Optional
from src.config import get_iosxe_config

# El sandbox DevNet usa un certificado autofirmado; suprimimos la advertencia
# En producción se debe usar verify=True con el certificado correcto
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

RESTCONF_BASE = "https://{host}:{port}/restconf/data"
HEADERS = {
    "Accept": "application/yang-data+json",
    "Content-Type": "application/yang-data+json",
}


def _session(user: str, password: str) -> requests.Session:
    """Crea una sesión HTTP con autenticación básica."""
    s = requests.Session()
    s.auth = (user, password)
    s.headers.update(HEADERS)
    s.verify = False  # Sandbox usa cert autofirmado
    return s


def get_interfaces(cfg: Optional[dict] = None) -> list:
    """
    Obtiene la lista de interfaces del router IOS-XE via RESTCONF.

    Modelo YANG: Cisco-IOS-XE-interfaces-oper:interfaces/interface
    Retorna una lista de dicts con nombre, estado y direcciones IP.
    """
    if cfg is None:
        cfg = get_iosxe_config()

    base = RESTCONF_BASE.format(host=cfg["host"], port=cfg["port"])
    url = f"{base}/Cisco-IOS-XE-interfaces-oper:interfaces"

    session = _session(cfg["user"], cfg["password"])
    response = session.get(url, timeout=15)
    response.raise_for_status()

    raw = response.json()
    interfaces_raw = raw.get("Cisco-IOS-XE-interfaces-oper:interfaces", {})
    iface_list = interfaces_raw.get("interface", [])

    result = []
    for iface in iface_list:
        entry = {
            "nombre": iface.get("name", ""),
            "estado_admin": iface.get("admin-status", ""),
            "estado_oper": iface.get("oper-status", ""),
            "descripcion": iface.get("description", ""),
            "ip_address": "",
        }
        # Extraer la primera IP v4 si existe
        ipv4_info = iface.get("ipv4", {})
        addresses = ipv4_info.get("addresses", {}).get("address", [])
        if isinstance(addresses, list) and addresses:
            entry["ip_address"] = addresses[0].get("ip", "")
        elif isinstance(addresses, dict):
            entry["ip_address"] = addresses.get("ip", "")

        result.append(entry)

    return result


def get_hostname(cfg: Optional[dict] = None) -> str:
    """Obtiene el hostname del router via RESTCONF."""
    if cfg is None:
        cfg = get_iosxe_config()

    base = RESTCONF_BASE.format(host=cfg["host"], port=cfg["port"])
    url = f"{base}/Cisco-IOS-XE-native:native/hostname"

    session = _session(cfg["user"], cfg["password"])
    response = session.get(url, timeout=15)
    response.raise_for_status()

    data = response.json()
    return data.get("Cisco-IOS-XE-native:hostname", "desconocido")
