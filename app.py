from flask import Flask, request, jsonify, Response
from flask_cors import CORS, cross_origin
import json
import os
import requests
import re
import time
from urllib.parse import urljoin, unquote
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from datetime import datetime, timedelta
from pathlib import Path

# Import sitemap generator
try:
    from generate_sitemap import SitemapGenerator
    SITEMAP_AVAILABLE = True
except ImportError:
    SITEMAP_AVAILABLE = False
    print("Warning: Sitemap generator not available")

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

PORT = int(os.environ.get('PORT', 3001))
DATA_FILE = os.path.join(os.getcwd(), 'data.json')

# Sitemap cache and configuration
sitemap_cache = {}
sitemap_cache_duration = timedelta(hours=1)

def get_sitemap_generator():
    """Get configured sitemap generator."""
    if not SITEMAP_AVAILABLE:
        return None
    config_path = os.path.join(os.path.dirname(__file__), 'sitemap.config.json')
    return SitemapGenerator(config_path)

def serve_sitemap_cached(cache_key: str, generator_func):
    """Serve sitemap with caching."""
    now = datetime.now()
    
    # Check cache
    if cache_key in sitemap_cache:
        content, timestamp = sitemap_cache[cache_key]
        if now - timestamp < sitemap_cache_duration:
            return Response(content, mimetype='application/xml')
    
    # Generate new content
    try:
        generator = get_sitemap_generator()
        if not generator:
            return Response("Sitemap generator not available", status=500)
            
        content = generator_func(generator)
        sitemap_cache[cache_key] = (content, now)
        
        return Response(content, mimetype='application/xml')
    except Exception as e:
        return Response(f"Error generating sitemap: {e}", status=500)


# Endpoint para scraping headless con Selenium
@app.route('/api/selenium-scrape', methods=['POST'])
@cross_origin()
def selenium_scrape():
    data = request.get_json()
    page_url = data.get('page_url') or data.get('pageUrl')
    print(f"[SCRAPER] Recibido page_url: {page_url}")
    if not page_url:
        print("[SCRAPER] Error: Missing page_url")
        return jsonify({'error': 'Missing page_url'}), 400
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(options=chrome_options)
        print(f"[SCRAPER] Abriendo página: {page_url}")
        driver.get(page_url)
        time.sleep(2)
        html = driver.page_source
        driver.quit()
        print(f"[SCRAPER] HTML obtenido, longitud: {len(html)}")
        # Buscar 'logged_user = false' y extraer links
        if 'logged_user = false' not in html:
            print("[SCRAPER] 'logged_user = false' no encontrado en HTML")
            return jsonify({'error': "'logged_user = false' not found in HTML"}), 404
        print("[SCRAPER] 'logged_user = false' encontrado, buscando enlaces de video...")
        patterns = [
            r"html5player.setVideoUrlLow\(['\"](.*?)['\"]\)",
            r"html5player.setVideoUrlHigh\(['\"](.*?)['\"]\)",
            r"html5player.setVideoHLS\(['\"](.*?)['\"]\)"
        ]
        video_links = []
        for pat in patterns:
            found = re.findall(pat, html)
            print(f"[SCRAPER] Pattern {pat}: {len(found)} coincidencias")
            if found:
                for link in found:
                    print(f"[SCRAPER] Enlace extraído: {link}")
            video_links.extend(found)
        print(f"[SCRAPER] Total enlaces extraídos: {len(video_links)}")
        return jsonify({'video_links': video_links})
    except Exception as e:
        print(f"[SCRAPER] Error en scraping: {e}")
        return jsonify({'error': str(e)}), 500



@app.route('/api/videos', methods=['GET', 'OPTIONS'])
@cross_origin()
def get_videos():
    try:
        # Obtener parámetros de paginación y filtrado
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 20))
        category = request.args.get('category')
        video_id = request.args.get('videoId')
        print(f"[DEBUG] Parámetro category recibido: {category}")
        print(f"[DEBUG] Parámetro videoId recibido: {video_id}")
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Si se solicita por videoId, buscar y devolver solo ese video
        if video_id:
            # Buscar en todas las categorías si es dict
            found = None
            if isinstance(data, dict):
                for vids in data.values():
                    found = next((v for v in vids if str(v.get('id')) == str(video_id)), None)
                    if found:
                        break
            elif isinstance(data, list):
                found = next((v for v in data if str(v.get('id')) == str(video_id)), None)
            else:
                return jsonify({'error': 'Formato de data.json no soportado'}), 500
            if found:
                print(f"[DEBUG] Video encontrado por videoId: {video_id}")
                return jsonify({'videos': [found], 'total': 1, 'page': 1, 'size': 1, 'category': found.get('category')})
            else:
                print(f"[DEBUG] No se encontró video con videoId: {video_id}")
                return jsonify({'videos': [], 'total': 0, 'page': 1, 'size': 1, 'category': None})

        # Filtrar por categoría si se especifica
        if category:
            if isinstance(data, dict):
                videos = data.get(category, [])
            elif isinstance(data, list):
                videos = [v for v in data if v.get('category') == category]
            else:
                return jsonify({'error': 'Formato de data.json no soportado'}), 500
            print(f"[DEBUG] Videos filtrados por categoría '{category}': {len(videos)}")
        else:
            if isinstance(data, dict):
                videos = []
                for vids in data.values():
                    videos.extend(vids)
            elif isinstance(data, list):
                videos = data
            else:
                return jsonify({'error': 'Formato de data.json no soportado'}), 500
            print(f"[DEBUG] Videos sin filtrar (todas las categorías): {len(videos)}")

        # --- Popularidad: likes + views ---
        def parse_votes(v):
            # Convierte '1,4K' o '433' a int
            s = str(v).replace('.', '').replace(' votos', '').replace('K', '000').replace(',', '')
            try:
                return int(s)
            except:
                return 0

        for vid in videos:
            likes = parse_votes(vid.get('good_votes', 0))
            views = parse_votes(vid.get('total_votes', 0))
            vid['_popularity'] = likes + views

        # Ordena por popularidad descendente
        videos.sort(key=lambda v: v.get('_popularity', 0), reverse=True)

        # Mezclar todos los videos filtrados
        import random
        random.shuffle(videos)

        total = len(videos)  # Total real de videos filtrados
        start = (page - 1) * size
        end = start + size
        paginated = videos[start:end] if videos else []
        print(f"[DEBUG] Paginando: start={start}, end={end}, paginated={len(paginated)}, total={total}")
        response = jsonify({
            'videos': paginated,
            'total': total,
            'page': page,
            'size': size,
            'category': category
        })
        response.headers['Cache-Control'] = 'no-store'
        return response
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api', methods=['GET', 'OPTIONS'])
@cross_origin()
def healthcheck():
    return jsonify({"ok": True, "message": "API funcionando correctamente ✅"})

@app.route('/health', methods=['GET'])
@cross_origin()
def health():
    return jsonify({"status": "healthy", "timestamp": time.time()})

@app.route('/api/health', methods=['GET'])
@cross_origin()
def api_health():
    return jsonify({"status": "healthy", "service": "backend-api", "timestamp": time.time()})



@app.route('/api/scrape-video-url', methods=['POST', 'OPTIONS'])
@cross_origin()
def scrape_video_url():
    page_url = request.json.get('pageUrl') or request.json.get('page_url')
    if not page_url:
        return jsonify({'error': 'Missing page_url'}), 400
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Buscar el objeto que tenga pageUrl igual al recibido
        video_obj = next((item for item in data if item.get('pageUrl') == page_url or item.get('page_url') == page_url), None)
        if video_obj and video_obj.get('url'):
            return jsonify({'videoUrl': video_obj['url'], 'thumbnail': video_obj.get('thumbnail')})
        else:
            return jsonify({'error': 'No se encontró el video para esa página'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==========================================
# SITEMAP ROUTES
# ==========================================

@app.route('/sitemap.xml', methods=['GET'])
@cross_origin()
def main_sitemap():
    """Serve main sitemap index."""
    return serve_sitemap_cached('main', lambda gen: gen.generate_main_sitemap())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)
