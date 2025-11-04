# Migración de backend Node.js a Python (Flask)

Este backend fue migrado de Node.js/Express a Python/Flask.

## Instalación

1. Instala Python 3.8+
2. Instala dependencias:

```bash
pip install -r requirements.txt
```

## Uso

```bash
python app.py
```

El backend estará disponible en http://localhost:3001

## Endpoints

- `GET /api` — Healthcheck
- `GET /health` — Health check simple
- `GET /api/health` — Health check detallado
- `GET /api/videos` — Devuelve todo el catálogo (`data.json`)
- `GET /api/videos/by-category/<cat>` — Devuelve solo una categoría
- `POST /api/scrape-video-url` — Scrapea la URL de video de una página
- `POST /api/selenium-scrape` — Scrapea con Selenium headless

## Deployment y Troubleshooting

### Scripts de utilidad en VPS:
```bash
# Verificar estado del deployment
./check-deployment.sh

# Reinicio limpio del backend
./restart-backend.sh
```

### Comandos útiles para debugging:
```bash
# Ver logs de PM2
pm2 logs api

# Estado de PM2
pm2 status

# Verificar puerto 3001
lsof -i:3001

# Test de API
curl http://localhost:3001/health
```

### Problemas comunes:

1. **API no responde después del deploy:**
   - Verificar que PM2 esté ejecutando correctamente: `pm2 status`
   - Revisar logs: `pm2 logs api`
   - Usar script de reinicio: `./restart-backend.sh`

2. **Frontend no se conecta al backend:**
   - Verificar que el puerto 3001 esté abierto
   - Comprobar configuración de nginx
   - Verificar CORS en el backend

3. **Procesos duplicados:**
   - Limpiar PM2: `pm2 delete all && pm2 kill`
   - Revisar procesos en puerto: `lsof -i:3001`

## Notas
- El archivo `data.json` debe estar en la raíz del proyecto.
- El scraping usa BeautifulSoup, requests y Selenium.
- Los workflows de GitHub Actions manejan el deployment automático.
- El backend debe estar funcionando antes de que el frontend termine su deployment.