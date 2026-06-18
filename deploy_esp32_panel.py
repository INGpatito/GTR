#!/usr/bin/env python3
"""
Script de despliegue para el Panel ESP32 en la Orange Pi.
Espera hasta que la Orange Pi esté disponible y luego despliega los archivos del panel.
"""
import subprocess
import time
import sys

ORANGE_PI_IPS = [
    "100.89.43.30",   # Tailscale
    "192.168.100.61", # LAN antigua
    "192.168.100.16", # LAN nueva
]
USER = "orangepi"
PASS = "orangepi"

def ssh_cmd(ip, command, timeout=15):
    result = subprocess.run(
        ["sshpass", "-p", PASS, "ssh",
         "-o", "StrictHostKeyChecking=no",
         "-o", f"ConnectTimeout={timeout}",
         f"{USER}@{ip}", command],
        capture_output=True, text=True, timeout=timeout + 5
    )
    return result

def scp_file(ip, local, remote):
    result = subprocess.run(
        ["sshpass", "-p", PASS, "scp",
         "-o", "StrictHostKeyChecking=no",
         "-o", "ConnectTimeout=10",
         local, f"{USER}@{ip}:{remote}"],
        capture_output=True, text=True, timeout=30
    )
    return result

def find_online_ip():
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
    print("🔍 Esperando a que la Orange Pi se conecte a Internet (Tailscale/LAN)...")
    print("   (Por favor, conéctate a la red GTR y apaga el hotspot desde el panel de red)")
    ip = None
    for attempt in range(120):  # hasta 20 minutos
        ip = find_online_ip()
        if ip:
            print(f"\n✅ Orange Pi encontrada en: {ip}")
            break
        time.sleep(10)

    if not ip:
        print("❌ Timeout.")
        sys.exit(1)

    time.sleep(5)

    print("📂 Paso 1: Copiando esp32.js (rutas API)...")
    scp_file(ip, "backend/routes/esp32.js", "/home/orangepi/GTR/backend/routes/esp32.js")
    
    print("📂 Paso 2: Copiando server.js (backend actualizado)...")
    scp_file(ip, "backend/server.js", "/home/orangepi/GTR/backend/server.js")
    
    print("📂 Paso 3: Copiando esp32-panel.html (panel de control)...")
    scp_file(ip, "esp32-panel.html", "/home/orangepi/GTR/esp32-panel.html")

    print("🔄 Paso 4: Reiniciando backend (pm2)...")
    ssh_cmd(ip, "pm2 restart all")

    print("\n🎉 ¡Panel ESP32 desplegado con éxito en la Orange Pi!")
    print(f"   Puedes acceder en: http://{ip}:3000/esp32-panel")

if __name__ == "__main__":
    deploy()
