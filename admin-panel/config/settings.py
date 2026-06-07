"""
Parking GTR — Settings
~~~~~~~~~~~~~~~~~~~~~~
Carga centralizada de variables de entorno y configuración global.
Todas las demás capas importan desde aquí.
"""

import os
from dotenv import load_dotenv

# ── Cargar .env desde la raíz del paquete admin-panel ──
_PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_PACKAGE_DIR, ".env"))

# ── Base de Datos (PostgreSQL en Orange Pi) ────────────
# Candidatos a hosts para autodetectar
_CANDIDATE_HOSTS = [
    ("10.42.0.1", "Hotspot GTR"),
    ("orangepi4pro.local", "mDNS Local"),
    ("192.168.100.16", "Nueva LAN (MiWiFi)"),
    ("100.89.43.30", "Tailscale (VPN)"),
    ("192.168.100.61", "Antigua LAN")
]


def _resolve_db_host() -> str:
    """Intenta conectar a los diferentes candidatos de host en orden.

    Prueba cada host con un socket TCP rápido (timeout 1s).
    Retorna el primer host que responda en el puerto 5432.
    """
    import socket

    env_host = os.getenv("DB_HOST")
    if env_host:
        # Si hay un host explícito en .env, usarlo directamente
        return env_host

    for host, label in _CANDIDATE_HOSTS:
        try:
            sock = socket.create_connection((host, 5432), timeout=1.0)
            sock.close()
            print(f"  [OK] DB conectada via {label}: {host}")
            return host
        except (socket.timeout, ConnectionRefusedError, OSError):
            continue

    # Fallback: si nada responde, usar el mDNS como fallback
    print("  [ERROR] Ningun host de DB disponible, usando orangepi4pro.local como fallback")
    return "orangepi4pro.local"


_DB_HOST = _resolve_db_host()

DB_PARAMS: dict = {
    "host":     _DB_HOST,
    "port":     int(os.getenv("DB_PORT",  "5432")),
    "database": os.getenv("DB_NAME",     "parking_gtr"),
    "user":     os.getenv("DB_USER",     "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}

# ── Seguridad ──────────────────────────────────────────
JWT_SECRET: str         = os.getenv("JWT_SECRET", "fallback_dev_secret_change_me")
ADMIN_UNLOCK_PASS: str  = os.getenv("ADMIN_UNLOCK_PASS", "admin123")
ADMIN_API_KEY: str      = os.getenv("ADMIN_API_KEY", "")

# ── Backend API (para notificar al display Android) ────
def _resolve_api_url() -> str:
    """Resuelve la URL base del API backend usando el mismo host que la DB."""
    explicit = os.getenv("API_BASE_URL")
    if explicit:
        return explicit.rstrip("/")
    port = os.getenv("API_PORT", "3001")
    return f"http://{_DB_HOST}:{port}"

API_BASE_URL: str = _resolve_api_url()

# ── APIs externas ──────────────────────────────────────
CARSXE_API_KEY: str     = os.getenv("CARSXE_API_KEY", "")

# ── EmailJS ────────────────────────────────────────────
EMAILJS_SERVICE_ID: str   = os.getenv("EMAILJS_SERVICE_ID",  "service_h4dij37")
EMAILJS_TEMPLATE_ID: str  = os.getenv("EMAILJS_TEMPLATE_ID", "template_r4gkv6g")
EMAILJS_USER_ID: str      = os.getenv("EMAILJS_USER_ID",     "BaTFzWtSBU0bZ_lKj")
EMAILJS_ACCESS_TOKEN: str = os.getenv("EMAILJS_ACCESS_TOKEN", "oXznojZUyeBLPnRk_GqNj")


# ── Diagnóstico de arranque ────────────────────────────
def print_startup_banner(app_name: str = "Admin Panel") -> None:
    """Imprime el banner de diagnóstico en consola al iniciar."""
    print("\n" + "=" * 55)
    print(f"  PARKING GTR - {app_name}")
    print("=" * 55)
    if JWT_SECRET in ("fallback_dev_secret_change_me", "your_jwt_secret_here"):
        print("  [WARN] JWT_SECRET no configurado en admin-panel/.env")
        print("     Copia el valor de backend/.env -> JWT_SECRET")
    else:
        masked = JWT_SECRET[:4] + "*" * max(0, len(JWT_SECRET) - 8) + JWT_SECRET[-4:]
        print(f"  [OK] JWT_SECRET cargado: {masked}")
    print("=" * 55 + "\n")
