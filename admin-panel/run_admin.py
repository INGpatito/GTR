"""
Parking GTR — Admin Panel Launcher
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Ejecuta el panel de administración.

Uso:
    python run_admin.py
"""

import sys
import os

# Agregar el directorio del paquete al path para imports relativos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.admin.app import ParkingAdmin


def main():
    app = ParkingAdmin()
    app.mainloop()


if __name__ == "__main__":
    main()
