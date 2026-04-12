# Despliegue a Orange Pi (GTR Platform)

Este repositorio soporta dos métodos de despliegue: mediante un script de automatización local (SSH) y mediante GitHub Actions.

## Método 1: Despliegue Local (Recomendado para Desarrollo)

El archivo `deploy_orangepi.py` permite desplegar cambios directamente desde tu PC a la Orange Pi sin esperar a GitHub.

### Requisitos
- Tener Python instalado.
- Instalar la librería `paramiko`:
  ```bash
  pip install paramiko
  ```

### Procedimiento
1. Realiza tus cambios y haz un `git push` a GitHub.
2. Ejecuta el despachador:
   ```bash
   python deploy_orangepi.py
   ```

### ¿Qué hace el script?
1. Se conecta vía SSH a la Orange Pi (`192.168.100.61`).
2. **Sincroniza el Reloj:** Configura la zona horaria a `America/Mexico_City` y fuerza la actualización de la hora mediante `chrony`.
3. **Actualiza Código:** Ejecuta un `git fetch` y `git reset --hard origin/main` en la carpeta `~/GTR`.
4. **Reinicia Backend:** Instala dependencias con `npm install` y reinicia los procesos con `pm2 restart all`.

---

## Método 2: GitHub Actions (Continuo)

 GitHub Actions para despliegue automático cuando haces un push a `main`.

### Configuración de Runner
Si el runner se detiene, ejecútalo como servicio en la Orange Pi:
```bash
cd ~/actions-runner
sudo ./svc.sh start
```

### Secretos en GitHub
Asegúrate de tener estos secretos en `Settings > Secrets and variables > Actions`:
- `ORANGE_PI_APP_DIR`: `/home/orangepi/GTR`
- `ADMIN_UNLOCK_PASS`: Tu contraseña administrativa.

---

## Mantenimiento del Sistema (Orange Pi)

### Gestión de Procesos (PM2)
Para ver el estado de los servicios del backend en la Orange Pi:
```bash
pm2 status
pm2 logs gtr-backend
```

### Sincronización de Hora
Si el reloj se desincroniza (causando errores en logs), usa estos comandos (ya incluidos en el script de deploy):
```bash
sudo chronyc makestep
timedatectl status
```

### Ubicación de Archivos
- **Frontend/Backend:** `/home/orangepi/GTR`
- **Base de Datos:** PostgreSQL (Puerto 5432)
- **Panel Admin (Python):** `~/GTR/admin-panel`

