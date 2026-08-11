"""
main.py — Punto de entrada de la aplicación de automatización NetDevOps.

Flujo:
  1. Autentica con Cisco DNA Center / Catalyst Center (DevNet Sandbox)
  2. Consulta inventario completo de dispositivos de red
  3. Consulta interfaces del primer dispositivo disponible
  4. Consulta CSR1000v local via NETCONF (RFC 6241 + modelos YANG)
  5. Genera reporte JSON y HTML en reports/
"""
import sys
from src.dnac_client import get_network_devices, get_device_interfaces
from src.netconf_client import get_hostname_netconf, get_interfaces_netconf
from src.report_generator import generate_devices_json, generate_devices_html


def main() -> int:
    print("=" * 60)
    print("  DevOps-Final — Automatización de Red NetDevOps")
    print("=" * 60)

    print("\n[1/5] Autenticando con Cisco DNA Center (Catalyst Center)...")
    print("      Host: sandboxdnac.cisco.com")
    try:
        devices = get_network_devices()
        print(f"      Autenticación exitosa. Inventario recibido.")
    except Exception as exc:
        print(f"      ERROR al conectar con DNA Center: {exc}")
        return 1

    print(f"\n[2/5] Inventario de red: {len(devices)} dispositivos encontrados.")
    for dev in devices:
        print(f"      - {dev['hostname']:<20} {dev['ip_address']:<16} {dev['familia']}")

    print("\n[3/5] Consultando interfaces del primer dispositivo (DNA Center)...")
    interfaces = []
    if devices:
        first_device = devices[0]
        try:
            interfaces = get_device_interfaces(first_device["id"])
            print(f"      {first_device['hostname']}: {len(interfaces)} interfaces encontradas.")
        except Exception as exc:
            print(f"      Advertencia — no se pudieron obtener interfaces: {exc}")

    print("\n[4/5] Consultando CSR1000v local via NETCONF (RFC 6241)...")
    try:
        csr_hostname = get_hostname_netconf()
        csr_interfaces = get_interfaces_netconf()
        print(f"      Hostname: {csr_hostname} | {len(csr_interfaces)} interface(s) encontradas")
        for iface in csr_interfaces:
            ip = iface.get("ip_address") or iface.get("ipv6_address") or "sin IP"
            print(f"      - {iface['nombre']:<25} ip={ip}  descr={iface['descripcion']}")
    except Exception as exc:
        print(f"      Advertencia NETCONF: {exc}")

    print("\n[5/5] Generando reportes automáticos...")
    json_path = generate_devices_json(devices, interfaces)
    html_path = generate_devices_html(devices, interfaces)
    print(f"      JSON → {json_path}")
    print(f"      HTML → {html_path}")

    print("\n  Resumen del inventario:")
    print(f"  {'HOSTNAME':<20} {'IP':<16} {'PLATAFORMA':<20} {'ESTADO'}")
    print(f"  {'-'*20} {'-'*16} {'-'*20} {'-'*12}")
    for dev in devices:
        print(
            f"  {dev['hostname']:<20} "
            f"{dev['ip_address']:<16} "
            f"{dev['plataforma']:<20} "
            f"{dev['estado']}"
        )

    print("\n✓ Automatización completada exitosamente.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
