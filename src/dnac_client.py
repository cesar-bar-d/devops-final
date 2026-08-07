"""
dnac_client.py — Consulta de inventario de red usando Cisco DNA Center / Catalyst Center API.

DNA Center (ahora Catalyst Center) es la plataforma de gestión de red de Cisco
que provee una API REST unificada para administrar toda la infraestructura.

Sandbox utilizado: Cisco DevNet Always-On Catalyst Center
  Host: sandboxdnac.cisco.com
  Credenciales: ver .env.example
"""
import requests
import urllib3
from typing import Optional
from src.config import get_dnac_config

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

AUTH_URL = "https://{host}/dna/system/api/v1/auth/token"
DEVICES_URL = "https://{host}/dna/intent/api/v1/network-device"
INTERFACES_URL = "https://{host}/dna/intent/api/v1/interface/network-device/{device_id}"
SITES_URL = "https://{host}/dna/intent/api/v1/site"


def get_auth_token(cfg: Optional[dict] = None) -> str:
    """
    Obtiene el token de autenticación de DNA Center.
    DNA Center usa autenticación basada en tokens (JWT).
    """
    if cfg is None:
        cfg = get_dnac_config()

    response = requests.post(
        AUTH_URL.format(host=cfg["host"]),
        auth=(cfg["user"], cfg["password"]),
        verify=False,
        timeout=15,
    )
    response.raise_for_status()
    return response.json()["Token"]


def get_network_devices(cfg: Optional[dict] = None) -> list:
    """
    Obtiene el inventario completo de dispositivos de red gestionados por DNA Center.
    Retorna lista de dicts con hostname, IP, plataforma, versión de SW y estado.
    """
    if cfg is None:
        cfg = get_dnac_config()

    token = get_auth_token(cfg)
    headers = {"x-auth-token": token, "Content-Type": "application/json"}

    response = requests.get(
        DEVICES_URL.format(host=cfg["host"]),
        headers=headers,
        verify=False,
        timeout=15,
    )
    response.raise_for_status()

    devices_raw = response.json().get("response", [])
    result = []
    for dev in devices_raw:
        result.append({
            "id": dev.get("id", ""),
            "hostname": dev.get("hostname", ""),
            "ip_address": dev.get("managementIpAddress", ""),
            "plataforma": dev.get("platformId", ""),
            "familia": dev.get("family", ""),
            "serie": dev.get("series", ""),
            "version_sw": dev.get("softwareVersion", ""),
            "estado": dev.get("reachabilityStatus", ""),
            "rol": dev.get("role", ""),
            "numero_serie": dev.get("serialNumber", ""),
            "uptime": dev.get("upTime", ""),
        })

    return result


def get_device_interfaces(device_id: str, cfg: Optional[dict] = None) -> list:
    """
    Obtiene las interfaces de un dispositivo específico via DNA Center API.
    Equivalente funcional a RESTCONF para entornos gestionados por DNA Center.
    """
    if cfg is None:
        cfg = get_dnac_config()

    token = get_auth_token(cfg)
    headers = {"x-auth-token": token, "Content-Type": "application/json"}

    response = requests.get(
        INTERFACES_URL.format(host=cfg["host"], device_id=device_id),
        headers=headers,
        verify=False,
        timeout=15,
    )
    response.raise_for_status()

    interfaces_raw = response.json().get("response", [])
    result = []
    for iface in interfaces_raw:
        result.append({
            "nombre": iface.get("portName", ""),
            "estado_admin": iface.get("adminStatus", ""),
            "estado_oper": iface.get("status", ""),
            "descripcion": iface.get("description", ""),
            "ip_address": iface.get("ipv4Address", "") or "",
            "velocidad": iface.get("speed", ""),
        })

    return result
