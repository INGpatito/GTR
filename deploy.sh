#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
#  PARKING GTR — UNIVERSAL DEPLOYMENT SCRIPT (v2.0)
# ═══════════════════════════════════════════════════════════════════════════
set -e

# Colores para la terminal
GOLD='\033[0;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GOLD}🔹 Iniciando despliegue de Parking GTR...${NC}"

# 1. Sincronizar Reloj (Crucial para logs y JWT)
echo -e "🕒 Sincronizando reloj del sistema..."
sudo timedatectl set-timezone America/Mexico_City || true
sudo chronyc makestep || true

# 2. Instalar dependencias del backend
echo -e "📦 Actualizando dependencias de Node.js..."
cd backend
npm install --production

# 3. Aplicar Migraciones de Base de Datos
echo -e "🗄️ Aplicando migraciones de base de datos..."
# Extraer contraseña del .env si existe, o usar postgres por defecto
DB_PWD=$(grep DB_PASSWORD .env | cut -d= -f2 || echo "")
DB_NAME=$(grep DB_NAME .env | cut -d= -f2 || echo "parking_gtr")

export PGPASSWORD=$DB_PWD

# Ejecutar archivos SQL (el orden importa)
psql -h localhost -U postgres -d "$DB_NAME" -f db/schema.sql > /dev/null
psql -h localhost -U postgres -d "$DB_NAME" -f db/migration_password_hash.sql > /dev/null
psql -h localhost -U postgres -d "$DB_NAME" -f db/migration_vehicles.sql > /dev/null
psql -h localhost -U postgres -d "$DB_NAME" -f db/migration_users.sql > /dev/null

unset PGPASSWORD

# 4. Asegurar dependencias de Python (para el Member Scanner)
echo -e "🐍 Verificando dependencias de Python..."
cd ../admin-panel
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --break-system-packages || pip install customtkinter psycopg2-binary python-dotenv bcrypt --break-system-packages
fi
cd ..

# 5. Configurar Backup Automático
echo -e "💾 Configurando backup automático de la base de datos..."
BACKUP_DIR="/home/orangepi/backups"
mkdir -p "$BACKUP_DIR"

# Crear script de backup
cat << 'EOF' > "$BACKUP_DIR/backup.sh"
#!/bin/bash
DB_NAME="parking_gtr"
BACKUP_DIR="/home/orangepi/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql.gz"

echo "Iniciando backup de $DB_NAME..."
sudo -u postgres pg_dump "$DB_NAME" | gzip > "$BACKUP_FILE"
echo "Backup completado: $BACKUP_FILE"

# Eliminar backups de más de 7 días
find "$BACKUP_DIR" -name "*.sql.gz" -type f -mtime +7 -delete
echo "Limpieza completada."
EOF
chmod +x "$BACKUP_DIR/backup.sh"

# Añadir a cron si no existe
CRON_JOB="0 3 * * * $BACKUP_DIR/backup.sh >> $BACKUP_DIR/backup.log 2>&1"
(crontab -l 2>/dev/null | grep -v "$BACKUP_DIR/backup.sh"; echo "$CRON_JOB") | crontab -
echo -e "  ✅ Backup diario programado a las 3:00 AM"

# 6. Reiniciar Servicios con PM2
echo -e "🚀 Reiniciando procesos en PM2..."
# Intentar usar el ecosistema si existe, si no, usar el nombre directo
if [ -f "backend/ecosystem.config.js" ]; then
    cd backend && pm2 start ecosystem.config.js --env production || pm2 reload all --env production
    cd ..
else
    pm2 restart gtr-backend || pm2 start backend/server.js --name gtr-backend
fi

# Guardar estado para persistencia tras reinicio de la placa
pm2 save

# 7. Verificación de Salud
echo -e "⏳ Verificando salud del backend..."
sleep 3
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/api/health)
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ Backend respondiendo correctamente (HTTP $HTTP_CODE)${NC}"
else
    echo -e "${RED}❌ Backend NO responde (HTTP $HTTP_CODE). Revisa: pm2 logs${NC}"
    # No fallamos el script entero aquí, solo alertamos
fi

echo -e "${GREEN}✅ ¡Despliegue finalizado con éxito!${NC}"
pm2 status
