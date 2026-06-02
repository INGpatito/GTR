"""
╔══════════════════════════════════════════════════════╗
║          PARKING GTR — ADMIN PANEL v2.0              ║
║   Gestión de socios, membresías y reservaciones      ║
╚══════════════════════════════════════════════════════╝

Uso:
    python run_admin.py

Requisitos:
    pip install customtkinter psycopg2-binary python-dotenv bcrypt
"""

import sys
import os

# Agregar el directorio del paquete al path para imports relativos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import print_startup_banner


def main():
    # Banner de diagnóstico (DB host, JWT_SECRET)
    print_startup_banner("Admin Panel")

    from ui.admin.app import ParkingAdmin

    app = ParkingAdmin()
    app.mainloop()


if __name__ == "__main__":
    main()