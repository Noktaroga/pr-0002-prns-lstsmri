#!/bin/bash

# Script para limpiar conflictos de git en el VPS
# Uso: ./fix-git-conflicts.sh

echo "=== LIMPIEZA DE CONFLICTOS GIT EN VPS ==="
echo

cd /var/app/backend || {
    echo "Error: No se pudo acceder a /var/app/backend"
    exit 1
}

echo "1. Deteniendo servicios..."
pm2 stop api || true

echo "2. Respaldando archivos importantes..."
if [ -f "data.json" ]; then
    cp data.json data.json.backup.$(date +%s)
    echo "✓ data.json respaldado"
fi

echo "3. Limpiando entorno virtual y archivos temporales..."
if [ -d "venv" ]; then
    echo "Eliminando venv actual..."
    rm -rf venv
fi

rm -rf __pycache__
rm -f *.log
rm -f *.pyc

echo "4. Limpiando estado de git..."
git fetch origin main
git reset --hard origin/main
git clean -fd

echo "5. Recreando entorno virtual..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "6. Reiniciando servicios..."
pm2 start app.py --name api --interpreter /var/app/backend/venv/bin/python --instances 1

echo "7. Verificando estado..."
sleep 5
pm2 status
curl -s http://localhost:3001/health || echo "API no responde aún"

echo
echo "=== LIMPIEZA COMPLETADA ==="