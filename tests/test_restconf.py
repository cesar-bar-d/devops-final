"""
test_restconf.py — Pruebas unitarias para restconf_client.py

Se usan mocks para no depender de conexión de red durante las pruebas.
Esto permite que los tests corran en cualquier entorno (local, CI/CD).
"""
import json
from unittest.mock import MagicMock, patch
import pytest
from src.restconf_client import get_hostname, get_interfaces

# ── Datos de prueba (fixtures) ────────────────────────────────────────────────

MOCK_HOSTNAME_RESPONSE = {"Cisco-IOS-XE-native:hostname": "csr1000v-sandbox"}

MOCK_INTERFACES_RESPONSE = {
    "Cisco-IOS-XE-interfaces-oper:interfaces": {
        "interface": [
            {
                "name": "GigabitEthernet1",
                "admin-status": "if-state-up",
                "oper-status": "if-oper-state-ready",
                "description": "MGMT Interface",
                "ipv4": {
                    "addresses": {
                        "address": [{"ip": "10.10.20.48"}]
                    }
                },
            },
            {
                "name": "Loopback0",
                "admin-status": "if-state-up",
                "oper-status": "if-oper-state-ready",
                "description": "",
                "ipv4": {},
            },
        ]
    }
}

MOCK_CFG = {
    "host": "ios-xe-mgmt-latest.cisco.com",
    "port": 443,
    "user": "developer",
    "password": "C1sco12345",
}

# ── Helper ────────────────────────────────────────────────────────────────────

def _mock_response(data: dict, status: int = 200) -> MagicMock:
    """Crea un objeto response mock con .json() y .raise_for_status()."""
    mock_resp = MagicMock()
    mock_resp.status_code = status
    mock_resp.json.return_value = data
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestGetHostname:
    @patch("src.restconf_client.requests.Session")
    def test_returns_hostname_string(self, mock_session_cls):
        mock_session = MagicMock()
        mock_session.get.return_value = _mock_response(MOCK_HOSTNAME_RESPONSE)
        mock_session_cls.return_value = mock_session

        result = get_hostname(MOCK_CFG)

        assert result == "csr1000v-sandbox"

    @patch("src.restconf_client.requests.Session")
    def test_returns_unknown_on_missing_key(self, mock_session_cls):
        mock_session = MagicMock()
        mock_session.get.return_value = _mock_response({})
        mock_session_cls.return_value = mock_session

        result = get_hostname(MOCK_CFG)

        assert result == "desconocido"

    @patch("src.restconf_client.requests.Session")
    def test_raises_on_http_error(self, mock_session_cls):
        import requests as req
        mock_session = MagicMock()
        mock_resp = _mock_response({}, status=401)
        mock_resp.raise_for_status.side_effect = req.exceptions.HTTPError("401 Unauthorized")
        mock_session.get.return_value = mock_resp
        mock_session_cls.return_value = mock_session

        with pytest.raises(req.exceptions.HTTPError):
            get_hostname(MOCK_CFG)


class TestGetInterfaces:
    @patch("src.restconf_client.requests.Session")
    def test_returns_list_of_interfaces(self, mock_session_cls):
        mock_session = MagicMock()
        mock_session.get.return_value = _mock_response(MOCK_INTERFACES_RESPONSE)
        mock_session_cls.return_value = mock_session

        result = get_interfaces(MOCK_CFG)

        assert isinstance(result, list)
        assert len(result) == 2

    @patch("src.restconf_client.requests.Session")
    def test_interface_has_required_keys(self, mock_session_cls):
        mock_session = MagicMock()
        mock_session.get.return_value = _mock_response(MOCK_INTERFACES_RESPONSE)
        mock_session_cls.return_value = mock_session

        result = get_interfaces(MOCK_CFG)
        iface = result[0]

        assert "nombre" in iface
        assert "estado_admin" in iface
        assert "estado_oper" in iface
        assert "ip_address" in iface

    @patch("src.restconf_client.requests.Session")
    def test_extracts_ip_address_correctly(self, mock_session_cls):
        mock_session = MagicMock()
        mock_session.get.return_value = _mock_response(MOCK_INTERFACES_RESPONSE)
        mock_session_cls.return_value = mock_session

        result = get_interfaces(MOCK_CFG)

        assert result[0]["ip_address"] == "10.10.20.48"
        assert result[1]["ip_address"] == ""

    @patch("src.restconf_client.requests.Session")
    def test_returns_empty_list_when_no_interfaces(self, mock_session_cls):
        mock_session = MagicMock()
        mock_session.get.return_value = _mock_response(
            {"Cisco-IOS-XE-interfaces-oper:interfaces": {}}
        )
        mock_session_cls.return_value = mock_session

        result = get_interfaces(MOCK_CFG)

        assert result == []
