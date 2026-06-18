#!/usr/bin/env python3
"""
Script de despliegue para corregir el Access Point GTR en la Orange Pi.
Espera hasta que la Orange Pi esté disponible y luego despliega los cambios.
"""
import subprocess
import time
import sys

ORANGE_PI_IPS = [
    "100.89.43.30",   # Tailscale
    "192.168.100.61", # LAN antigua
    "192.168.100.16", # LAN nueva (MiWiFi)
]
USER = "orangepi"
PASS = "orangepi"

def ssh_cmd(ip, command, timeout=15):
    """Ejecuta un comando SSH en la Orange Pi."""
    result = subprocess.run(
        ["sshpass", "-p", PASS, "ssh",
         "-o", "StrictHostKeyChecking=no",
         "-o", f"ConnectTimeout={timeout}",
         f"{USER}@{ip}", command],
        capture_output=True, text=True, timeout=timeout + 5
    )
    return result

def scp_file(ip, local, remote):
    """Copia un archivo a la Orange Pi via SCP."""
    result = subprocess.run(
        ["sshpass", "-p", PASS, "scp",
         "-o", "StrictHostKeyChecking=no",
         "-o", "ConnectTimeout=10",
         local, f"{USER}@{ip}:{remote}"],
        capture_output=True, text=True, timeout=30
    )
    return result

def find_online_ip():
    """Encuentra la primera IP de la Orange Pi que responde."""
    for ip in ORANGE_PI_IPS:
        try:
            result = subprocess.run(
                ["ping", "-c", "1", "-W", "2", ip],
                capture_output=True, timeout=5
            )
            if result.returncode == 0:
                return ip
        except Exception:
            pass
    return None

def deploy():
    print("🔍 Buscando Orange Pi en la red...")
    ip = None
    for attempt in range(30):  # hasta 5 minutos
        ip = find_online_ip()
        if ip:
            print(f"✅ Orange Pi encontrada en: {ip}")
            break
        print(f"  ⏳ Intento {attempt + 1}/30 — Sin respuesta, esperando 10s...")
        time.sleep(10)

    if not ip:
        print("❌ No se pudo conectar a la Orange Pi después de 5 minutos.")
        sys.exit(1)

    # Dar 5s extra para que SSH arranque completamente
    time.sleep(5)

    print("\n📂 Paso 1: Copiando network.js corregido...")
    r = scp_file(ip,
        "backend/routes/network.js",
        "/home/orangepi/GTR/backend/routes/network.js"
    )
    if r.returncode == 0:
        print("  ✅ network.js copiado correctamente.")
    else:
        print(f"  ❌ Error copiando: {r.stderr}")
        sys.exit(1)

    print("\n🔄 Paso 2: Reiniciando backend (pm2)...")
    r = ssh_cmd(ip, "pm2 restart all")
    if r.returncode == 0:
        print("  ✅ Backend reiniciado.")
    else:
        print(f"  ⚠️  pm2 output: {r.stdout} {r.stderr}")

    print("\n📡 Paso 3: Verificando que el Hotspot GTR se puede activar...")
    r = ssh_cmd(ip, "echo 'orangepi' | sudo -S nmcli connection show HotspotLocal | grep 'connection.interface-name'")
    print(f"  Interface: {r.stdout.strip()}")

    print("\n✅ Hotspot: Activando Access Point GTR...")
    r = ssh_cmd(ip,
        "echo 'orangepi' | sudo -S nmcli connection down Totalplay-ACA8-5G 2>/dev/null; "
        "echo 'orangepi' | sudo -S nmcli connection down MiWiFi 2>/dev/null; "
        "echo 'orangepi' | sudo -S nmcli connection up HotspotLocal",
        timeout=20
    )
    print(f"  {r.stdout.strip() or r.stderr.strip()}")
    if "successfully activated" in r.stdout or "successfully activated" in r.stderr:
        print("  ✅ ¡Access Point GTR activado correctamente!")
    else:
        print("  ℹ️  Resultado de activación mostrado arriba.")

    print("\n🎉 ¡Despliegue completado!")
    print(f"   → Panel de red: http://10.42.0.1/admin-network.html")
    print(f"   → Backend API:  http://10.42.0.1:3000/api/network/status")

if __name__ == "__main__":
    deploy()
