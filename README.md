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
- `GET /api/videos` — Devuelve todo el catálogo (`data.json`)
- `GET /api/videos/by-category/<cat>` — Devuelve solo una categoría
- `POST /api/scrape-video-url` — Scrapea la URL de video de una página (ver body en server.js original)

## Notas
- El archivo `data.json` debe estar en la raíz del proyecto.
- El scraping usa BeautifulSoup y requests.