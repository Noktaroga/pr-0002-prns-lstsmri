#!/bin/bash

# Script para verificar el estado del deployment en el VPS
# Uso: ./check-deployment.sh

echo "=== VERIFICACIÓN DE ESTADO DEL DEPLOYMENT ==="
echo

# Verificar PM2
echo "1. Estado de PM2:"
pm2 status | grep -E "(api|online|stopped|errored)" || echo "No hay procesos PM2 activos"
echo

# Verificar puerto 3001
echo "2. Verificando puerto 3001:"
if lsof -i:3001 > /dev/null 2>&1; then
    echo "✓ Puerto 3001 está en uso por:"
    lsof -i:3001
else
    echo "✗ Puerto 3001 no está en uso"
fi
echo

# Verificar API health
echo "3. Verificando API health:"
if curl -s -w "Tiempo respuesta: %{time_total}s\n" http://localhost:3001/health > /dev/null 2>&1; then
    echo "✓ API respondiendo en /health"
    curl -s http://localhost:3001/health | jq . 2>/dev/null || curl -s http://localhost:3001/health
else
    echo "✗ API no responde en /health"
fi
echo

# Verificar endpoint principal
echo "4. Verificando endpoint principal:"
if curl -s http://localhost:3001/api > /dev/null 2>&1; then
    echo "✓ API respondiendo en /api"
    curl -s http://localhost:3001/api | jq . 2>/dev/null || curl -s http://localhost:3001/api
else
    echo "✗ API no responde en /api"
fi
echo

# Verificar logs recientes de PM2
echo "5. Logs recientes de PM2 (últimas 20 líneas):"
pm2 logs api --lines 20 --nostream 2>/dev/null || echo "No se pudieron obtener logs de PM2"
echo

echo "=== FIN DE VERIFICACIÓN ==="