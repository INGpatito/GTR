#!/bin/bash

# Script para iniciar rápidamente el Scanner de Parking GTR
# Usando directamente el binario de Python del entorno virtual (.venv)

# Cambiar al directorio del panel de administración
cd /mnt/windows/Linux/GTR/admin-panel

# Ejecutar el scanner con el python local
.venv/bin/python run_scanner.py
