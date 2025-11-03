#!/bin/bash

# Script para reinicio limpio del backend
# Uso: ./restart-backend.sh

echo "=== REINICIO LIMPIO DEL BACKEND ==="
echo

echo "1. Deteniendo procesos existentes..."
if pm2 describe api > /dev/null 2>&1; then
    echo "Deteniendo proceso PM2 'api'..."
    pm2 stop api
    pm2 delete api
else
    echo "No hay proceso PM2 'api' activo"
fi

echo "2. Liberando puerto 3001..."
if lsof -i:3001 > /dev/null 2>&1; then
    echo "Terminando procesos en puerto 3001..."
    lsof -ti:3001 | xargs kill -9 || true
    sleep 2
else
    echo "Puerto 3001 ya está libre"
fi

echo "3. Activando entorno virtual..."
cd /var/app/backend
source venv/bin/activate || {
    echo "Error: No se pudo activar el entorno virtual"
    exit 1
}

echo "4. Iniciando nueva instancia..."
pm2 start app.py --name api --interpreter /var/app/backend/venv/bin/python --instances 1

echo "5. Esperando que la API esté lista..."
for i in {1..30}; do
    if curl -s http://localhost:3001/health > /dev/null 2>&1; then
        echo "✓ API respondiendo correctamente"
        break
    fi
    echo "Esperando... ($i/30)"
    sleep 2
done

echo "6. Guardando configuración PM2..."
pm2 save

echo "7. Estado final:"
pm2 status
echo

echo "=== REINICIO COMPLETADO ==="