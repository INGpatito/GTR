"""
Parking GTR — Member Scanner Launcher
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Ejecuta el scanner de socios.

Uso:
    python run_scanner.py
"""

import sys
import os

# Agregar el directorio del paquete al path para imports relativos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.scanner.app import MemberScanner


def main():
    app = MemberScanner()
    app.mainloop()


if __name__ == "__main__":
    main()
