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
DB_PARAMS: dict = {
    "host":     os.getenv("DB_HOST",     "192.168.100.61"),
    "port":     int(os.getenv("DB_PORT",  "5432")),
    "database": os.getenv("DB_NAME",     "parking_gtr"),
    "user":     os.getenv("DB_USER",     "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}

# ── Seguridad ──────────────────────────────────────────
JWT_SECRET: str         = os.getenv("JWT_SECRET", "fallback_dev_secret_change_me")
ADMIN_UNLOCK_PASS: str  = os.getenv("ADMIN_UNLOCK_PASS", "admin123")

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
    print("\n" + "═" * 55)
    print(f"  PARKING GTR — {app_name}")
    print("═" * 55)
    if JWT_SECRET in ("fallback_dev_secret_change_me", "your_jwt_secret_here"):
        print("  ⚠️  JWT_SECRET no configurado en admin-panel/.env")
        print("     Copia el valor de backend/.env → JWT_SECRET")
    else:
        masked = JWT_SECRET[:4] + "*" * max(0, len(JWT_SECRET) - 8) + JWT_SECRET[-4:]
        print(f"  ✅ JWT_SECRET cargado: {masked}")
    print("═" * 55 + "\n")
