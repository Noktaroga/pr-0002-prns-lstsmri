#!/bin/bash

# Script para limpiar completamente el directorio backend en VPS
# Uso: ./clean-backend-directory.sh

echo "=== LIMPIEZA COMPLETA DEL DIRECTORIO BACKEND ==="
echo

cd /var/app/backend || {
    echo "Error: No se pudo acceder a /var/app/backend"
    exit 1
}

echo "1. Configurando PATH para herramientas..."
export PATH=/root/.nvm/versions/node/v24.11.0/bin:$PATH

echo "2. Deteniendo todos los servicios PM2..."
pm2 stop all || true
pm2 delete all || true
pm2 kill || true

echo "3. Liberando puerto 3001..."
if lsof -i:3001 > /dev/null 2>&1; then
    echo "Terminando procesos en puerto 3001..."
    lsof -ti:3001 | xargs kill -9 || true
    sleep 3
fi

echo "4. Respaldando archivos importantes..."
if [ -f "data.json" ]; then
    cp data.json data.json.backup.$(date +%s)
    echo "✓ data.json respaldado"
fi

echo "5. Limpieza completa del directorio..."
# Mantener solo archivos esenciales
find . -maxdepth 1 ! -name '.' ! -name '..' ! -name '.git' ! -name 'data.json' -exec rm -rf {} +

echo "6. Reinicializando repositorio..."
git fetch origin main
git reset --hard origin/main
git clean -fd

echo "7. Creando nuevo entorno Python..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "8. Iniciando servicios..."
pm2 start app.py --name api --interpreter /var/app/backend/venv/bin/python --instances 1
pm2 save

echo "9. Verificando estado..."
sleep 5
echo "Estado PM2:"
pm2 status
echo
echo "Test API:"
curl -s http://localhost:3001/health || echo "API no responde aún"

echo
echo "=== LIMPIEZA COMPLETA FINALIZADA ==="