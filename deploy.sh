#!/usr/bin/env bash
set -e

echo "🔹 Iniciando despliegue de Parking GTR..."

# Instalar dependencias del backend
echo "📦 Instalando dependencias (Backend)..."
cd backend
npm install --production

# Levantar o reiniciar la aplicación con PM2 usando el ecosistema
echo "🚀 Reiniciando servidor en Orange Pi..."
pm2 start ecosystem.config.js --env production || pm2 reload gtr-backend --env production

# Guardar la lista de procesos de PM2 para que arranquen si se reinicia la placa
pm2 save

echo "✅ ¡Despliegue finalizado con éxito!"
