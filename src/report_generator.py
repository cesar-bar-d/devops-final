"""
report_generator.py — Genera reportes automáticos en JSON y HTML.

Consolida el inventario de red consultado via Cisco DNA Center API
y lo persiste en reports/ para auditoría y documentación.
"""
import json
import os
from datetime import datetime, timezone
from typing import List

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "reports")


def _ensure_reports_dir() -> str:
    path = os.path.abspath(REPORTS_DIR)
    os.makedirs(path, exist_ok=True)
    return path


def generate_devices_json(devices: List[dict], interfaces: List[dict]) -> str:
    """
    Genera reports/reporte_interfaces.json con inventario completo de red.
    Retorna la ruta absoluta del archivo generado.
    """
    reports_path = _ensure_reports_dir()
    timestamp = datetime.now(timezone.utc).isoformat()

    payload = {
        "metadata": {
            "generado_en": timestamp,
            "fuente": "Cisco DNA Center / Catalyst Center API",
            "sandbox": "sandboxdnac.cisco.com",
            "total_dispositivos": len(devices),
            "total_interfaces_consultadas": len(interfaces),
        },
        "dispositivos": devices,
        "interfaces_primer_dispositivo": interfaces,
    }

    output_file = os.path.join(reports_path, "reporte_interfaces.json")
    with open(output_file, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)

    return output_file


def generate_devices_html(devices: List[dict], interfaces: List[dict]) -> str:
    """
    Genera reports/reporte_interfaces.html con tablas formateadas.
    Retorna la ruta absoluta del archivo generado.
    """
    reports_path = _ensure_reports_dir()
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    device_rows = ""
    for dev in devices:
        status_color = "green" if dev["estado"] == "Reachable" else "red"
        device_rows += (
            f"<tr>"
            f"<td>{dev['hostname']}</td>"
            f"<td>{dev['ip_address']}</td>"
            f"<td>{dev['plataforma']}</td>"
            f"<td>{dev['familia']}</td>"
            f"<td>{dev['version_sw']}</td>"
            f"<td style='color:{status_color}'>{dev['estado']}</td>"
            f"<td>{dev['rol']}</td>"
            f"</tr>\n"
        )

    iface_rows = ""
    for iface in interfaces:
        status_color = "green" if iface["estado_oper"] == "up" else "orange"
        iface_rows += (
            f"<tr>"
            f"<td>{iface['nombre']}</td>"
            f"<td>{iface['descripcion'] or '—'}</td>"
            f"<td style='color:{status_color}'>{iface['estado_oper']}</td>"
            f"<td>{iface['estado_admin']}</td>"
            f"<td>{iface['ip_address'] or '—'}</td>"
            f"</tr>\n"
        )

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Reporte de Red — DNA Center</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 2rem; }}
    h1, h2 {{ color: #003087; }}
    table {{ border-collapse: collapse; width: 100%; margin-bottom: 2rem; }}
    th, td {{ border: 1px solid #ccc; padding: 8px 12px; text-align: left; }}
    th {{ background: #003087; color: white; }}
    tr:nth-child(even) {{ background: #f5f5f5; }}
    .footer {{ margin-top: 1rem; font-size: 0.85rem; color: #666; }}
    .badge {{ padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; }}
  </style>
</head>
<body>
  <h1>Reporte Automático de Infraestructura de Red</h1>
  <p><strong>Fuente:</strong> Cisco DNA Center / Catalyst Center API</p>
  <p><strong>Sandbox:</strong> sandboxdnac.cisco.com</p>
  <p><strong>Generado:</strong> {timestamp}</p>
  <p><strong>Total dispositivos:</strong> {len(devices)}</p>

  <h2>Inventario de Dispositivos</h2>
  <table>
    <thead>
      <tr>
        <th>Hostname</th><th>IP Mgmt</th><th>Plataforma</th>
        <th>Familia</th><th>Versión SW</th><th>Estado</th><th>Rol</th>
      </tr>
    </thead>
    <tbody>
{device_rows}
    </tbody>
  </table>

  <h2>Interfaces — Primer Dispositivo</h2>
  <table>
    <thead>
      <tr>
        <th>Nombre</th><th>Descripción</th><th>Estado Oper.</th>
        <th>Estado Admin.</th><th>Dirección IP</th>
      </tr>
    </thead>
    <tbody>
{iface_rows if iface_rows else '<tr><td colspan="5">Sin datos de interfaces</td></tr>'}
    </tbody>
  </table>

  <p class="footer">
    Generado automáticamente por DevOps-Final Automation Suite |
    Fuente: Cisco DNA Center Intent API v1
  </p>
</body>
</html>"""

    output_file = os.path.join(reports_path, "reporte_interfaces.html")
    with open(output_file, "w", encoding="utf-8") as fh:
        fh.write(html)

    return output_file


# ── Alias para compatibilidad con restconf_client (módulo de referencia) ──────
def generate_json(hostname: str, interfaces: List[dict]) -> str:
    """Alias: genera reporte desde datos RESTCONF (módulo de referencia)."""
    return generate_devices_json(
        [{"hostname": hostname, "ip_address": "", "plataforma": "", "familia": "",
          "serie": "", "version_sw": "", "estado": "N/A", "rol": "",
          "numero_serie": "", "uptime": "", "id": ""}],
        interfaces,
    )


def generate_html(hostname: str, interfaces: List[dict]) -> str:
    """Alias: genera HTML desde datos RESTCONF (módulo de referencia)."""
    return generate_devices_html(
        [{"hostname": hostname, "ip_address": "", "plataforma": "", "familia": "",
          "serie": "", "version_sw": "", "estado": "N/A", "rol": "",
          "numero_serie": "", "uptime": "", "id": ""}],
        interfaces,
    )
