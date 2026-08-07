"""
config.py — Carga segura de credenciales desde .env
Las credenciales NUNCA se escriben directamente en el código (no hardcoded).
"""
import os
from dotenv import load_dotenv

# Busca el archivo .env en el directorio raíz del proyecto
load_dotenv()


def get_iosxe_config() -> dict:
    """Retorna la configuración del router IOS-XE desde variables de entorno."""
    return {
        "host": os.environ["IOSXE_HOST"],
        "port": int(os.getenv("IOSXE_PORT", "443")),
        "user": os.environ["IOSXE_USER"],
        "password": os.environ["IOSXE_PASS"],
    }


def get_dnac_config() -> dict:
    """Retorna la configuración de DNA Center desde variables de entorno."""
    return {
        "host": os.environ["DNAC_HOST"],
        "user": os.environ["DNAC_USER"],
        "password": os.environ["DNAC_PASS"],
    }


def get_webex_config() -> dict:
    """Retorna la configuración de Webex desde variables de entorno."""
    return {
        "token": os.getenv("WEBEX_TOKEN", ""),
        "room_id": os.getenv("WEBEX_ROOM_ID", ""),
    }
