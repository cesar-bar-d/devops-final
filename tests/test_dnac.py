"""
test_dnac.py — Pruebas unitarias para dnac_client.py

Mocks completos para no requerir conexión real a DNA Center durante CI/CD.
"""
from unittest.mock import MagicMock, patch
import pytest
import requests as req
from src.dnac_client import get_auth_token, get_network_devices, get_device_interfaces

# ── Datos de prueba ───────────────────────────────────────────────────────────

MOCK_CFG = {
    "host": "sandboxdnac.cisco.com",
    "user": "devnetuser",
    "password": "Cisco123!",
}

MOCK_TOKEN = "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.mock_token"

MOCK_DEVICES_RESPONSE = {
    "response": [
        {
            "id": "abc-123",
            "hostname": "sw1",
            "managementIpAddress": "10.10.20.175",
            "platformId": "C9KV-UADP-8P",
            "family": "Switches and Hubs",
            "series": "Cisco Catalyst 9000 Series",
            "softwareVersion": "17.12.1",
            "reachabilityStatus": "Reachable",
            "role": "ACCESS",
            "serialNumber": "FXS2119Q2SE",
            "upTime": "44 days, 3:20:00",
        }
    ]
}

MOCK_INTERFACES_RESPONSE = {
    "response": [
        {
            "portName": "GigabitEthernet1/0/1",
            "adminStatus": "UP",
            "status": "up",
            "description": "Uplink to core",
            "ipv4Address": None,
            "speed": "1000000",
        },
        {
            "portName": "Vlan1",
            "adminStatus": "UP",
            "status": "up",
            "description": "Management VLAN",
            "ipv4Address": "10.10.20.175",
            "speed": "1000000",
        },
    ]
}


def _mock_post(data: dict, status: int = 200) -> MagicMock:
    m = MagicMock()
    m.status_code = status
    m.json.return_value = data
    m.raise_for_status = MagicMock()
    return m


def _mock_get(data: dict, status: int = 200) -> MagicMock:
    m = MagicMock()
    m.status_code = status
    m.json.return_value = data
    m.raise_for_status = MagicMock()
    return m


# ── Tests: get_auth_token ─────────────────────────────────────────────────────

class TestGetAuthToken:
    @patch("src.dnac_client.requests.post")
    def test_returns_token_string(self, mock_post):
        mock_post.return_value = _mock_post({"Token": MOCK_TOKEN})

        result = get_auth_token(MOCK_CFG)

        assert result == MOCK_TOKEN

    @patch("src.dnac_client.requests.post")
    def test_raises_on_401(self, mock_post):
        mock_resp = _mock_post({}, status=401)
        mock_resp.raise_for_status.side_effect = req.exceptions.HTTPError("401")
        mock_post.return_value = mock_resp

        with pytest.raises(req.exceptions.HTTPError):
            get_auth_token(MOCK_CFG)


# ── Tests: get_network_devices ────────────────────────────────────────────────

class TestGetNetworkDevices:
    @patch("src.dnac_client.requests.post")
    @patch("src.dnac_client.requests.get")
    def test_returns_list_of_devices(self, mock_get, mock_post):
        mock_post.return_value = _mock_post({"Token": MOCK_TOKEN})
        mock_get.return_value = _mock_get(MOCK_DEVICES_RESPONSE)

        result = get_network_devices(MOCK_CFG)

        assert isinstance(result, list)
        assert len(result) == 1

    @patch("src.dnac_client.requests.post")
    @patch("src.dnac_client.requests.get")
    def test_device_has_required_keys(self, mock_get, mock_post):
        mock_post.return_value = _mock_post({"Token": MOCK_TOKEN})
        mock_get.return_value = _mock_get(MOCK_DEVICES_RESPONSE)

        result = get_network_devices(MOCK_CFG)
        device = result[0]

        for key in ["id", "hostname", "ip_address", "plataforma", "familia",
                    "version_sw", "estado", "rol"]:
            assert key in device, f"Falta la clave: {key}"

    @patch("src.dnac_client.requests.post")
    @patch("src.dnac_client.requests.get")
    def test_maps_fields_correctly(self, mock_get, mock_post):
        mock_post.return_value = _mock_post({"Token": MOCK_TOKEN})
        mock_get.return_value = _mock_get(MOCK_DEVICES_RESPONSE)

        result = get_network_devices(MOCK_CFG)

        assert result[0]["hostname"] == "sw1"
        assert result[0]["ip_address"] == "10.10.20.175"
        assert result[0]["estado"] == "Reachable"


# ── Tests: get_device_interfaces ──────────────────────────────────────────────

class TestGetDeviceInterfaces:
    @patch("src.dnac_client.requests.post")
    @patch("src.dnac_client.requests.get")
    def test_returns_list_of_interfaces(self, mock_get, mock_post):
        mock_post.return_value = _mock_post({"Token": MOCK_TOKEN})
        mock_get.return_value = _mock_get(MOCK_INTERFACES_RESPONSE)

        result = get_device_interfaces("abc-123", MOCK_CFG)

        assert isinstance(result, list)
        assert len(result) == 2

    @patch("src.dnac_client.requests.post")
    @patch("src.dnac_client.requests.get")
    def test_ip_address_mapped_to_empty_string_when_none(self, mock_get, mock_post):
        mock_post.return_value = _mock_post({"Token": MOCK_TOKEN})
        mock_get.return_value = _mock_get(MOCK_INTERFACES_RESPONSE)

        result = get_device_interfaces("abc-123", MOCK_CFG)

        # First interface has no IP (None → "")
        assert result[0]["ip_address"] == ""
        # Second has IP
        assert result[1]["ip_address"] == "10.10.20.175"
