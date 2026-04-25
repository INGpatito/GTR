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

# 5. Reiniciar Servicios con PM2
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

echo -e "${GREEN}✅ ¡Despliegue finalizado con éxito!${NC}"
pm2 status
