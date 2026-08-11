"""
test_netconf.py — Pruebas unitarias para netconf_client.py

Mocks completos sobre ncclient para no requerir conexión NETCONF real en CI/CD.
"""
from unittest.mock import MagicMock, patch
import pytest
from src.netconf_client import get_capabilities, get_interfaces_netconf, get_hostname_netconf

MOCK_CFG = {
    "host": "192.168.56.101",
    "port": 22,
    "user": "cisco",
    "password": "cisco123!",
}

# Respuesta XML en formato Cisco PI model (cli-config-data-block) — IOS-XE 16.3
MOCK_CONFIG_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <data>
    <cli-config-data-block>
hostname CSR1kv
!
interface GigabitEthernet1
 description Gestionado por DevOps-Final Ansible Automation
 ip address dhcp
 ipv6 address 2001:DB8:ACAD:1::1/64
 ipv6 address FE80::1:1 link-local
!
interface Loopback0
 description Loopback de prueba
!
    </cli-config-data-block>
  </data>
</rpc-reply>"""


def _mock_manager(get_config_xml=None, caps=None):
    """Construye un mock del context manager de ncclient."""
    mock_conn = MagicMock()
    if get_config_xml:
        mock_cfg_resp = MagicMock()
        mock_cfg_resp.__str__ = lambda self: get_config_xml
        mock_conn.get_config.return_value = mock_cfg_resp
    if caps is not None:
        mock_conn.server_capabilities = caps

    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=mock_conn)
    mock_ctx.__exit__ = MagicMock(return_value=False)
    return mock_ctx


class TestGetCapabilities:
    @patch("src.netconf_client.manager.connect")
    def test_returns_list_of_strings(self, mock_connect):
        caps = ["urn:ietf:params:netconf:base:1.0", "urn:ietf:params:netconf:base:1.1"]
        mock_connect.return_value = _mock_manager(caps=iter(caps))

        result = get_capabilities(MOCK_CFG)

        assert isinstance(result, list)
        assert len(result) == 2

    @patch("src.netconf_client.manager.connect")
    def test_returns_empty_when_no_caps(self, mock_connect):
        mock_connect.return_value = _mock_manager(caps=iter([]))

        result = get_capabilities(MOCK_CFG)

        assert result == []


class TestGetInterfacesNetconf:
    @patch("src.netconf_client.manager.connect")
    def test_returns_list_of_interfaces(self, mock_connect):
        mock_connect.return_value = _mock_manager(get_config_xml=MOCK_CONFIG_XML)

        result = get_interfaces_netconf(MOCK_CFG)

        assert isinstance(result, list)
        assert len(result) == 2

    @patch("src.netconf_client.manager.connect")
    def test_interface_has_required_keys(self, mock_connect):
        mock_connect.return_value = _mock_manager(get_config_xml=MOCK_CONFIG_XML)

        result = get_interfaces_netconf(MOCK_CFG)
        iface = result[0]

        assert "nombre" in iface
        assert "descripcion" in iface
        assert "ip_address" in iface

    @patch("src.netconf_client.manager.connect")
    def test_maps_description_correctly(self, mock_connect):
        mock_connect.return_value = _mock_manager(get_config_xml=MOCK_CONFIG_XML)

        result = get_interfaces_netconf(MOCK_CFG)

        assert result[0]["nombre"] == "GigabitEthernet1"
        assert "DevOps-Final" in result[0]["descripcion"]


class TestGetHostnameNetconf:
    @patch("src.netconf_client.manager.connect")
    def test_returns_hostname_string(self, mock_connect):
        mock_connect.return_value = _mock_manager(get_config_xml=MOCK_CONFIG_XML)

        result = get_hostname_netconf(MOCK_CFG)

        assert result == "CSR1kv"

    @patch("src.netconf_client.manager.connect")
    def test_returns_default_on_empty_xml(self, mock_connect):
        empty_xml = '<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"><data/></rpc-reply>'
        mock_connect.return_value = _mock_manager(get_config_xml=empty_xml)

        result = get_hostname_netconf(MOCK_CFG)

        assert result == "desconocido"
