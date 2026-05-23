"""
Parking GTR — Admin Panel 
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
    main() #have been added to the system path, allowing for relative imports from the ui.admin package. The main function initializes and runs the ParkingAdmin application, which is the admin panel for the Parking GTR system. The script can be executed directly to launch the admin panel.

#The script is straightforward and serves as the entry point for the admin panel. It ensures that the necessary modules are accessible and then starts the application.