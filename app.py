
# --- Mover este endpoint después de la creación de app ---
from flask import Flask, request, jsonify

from flask_cors import CORS, cross_origin
import json
import os
import requests

from urllib.parse import urljoin, unquote

from scraper import extract_video_and_thumb


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

PORT = int(os.environ.get('PORT', 3001))
DATA_FILE = os.path.join(os.getcwd(), 'data.json')

@app.route('/api/videos', methods=['GET', 'OPTIONS'])
@cross_origin()
def get_videos():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api', methods=['GET', 'OPTIONS'])
@cross_origin()
def healthcheck():
    return jsonify({"ok": True, "message": "API funcionando correctamente ✅"})



@app.route('/api/scrape-video-url', methods=['POST', 'OPTIONS'])
@cross_origin()
def scrape_video_url():
    page_url = request.json.get('pageUrl') or request.json.get('page_url')
    if not page_url:
        return jsonify({'error': 'Missing page_url'}), 400
    try:
        print(f"[scrape_video_url] URL recibida: {page_url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Referer': 'https://www.xvideos.com/',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        resp = requests.get(page_url, headers=headers, allow_redirects=True, timeout=10)
        html = resp.text
        print(f"[scrape_video_url] HTML recibido (primeros 500 chars): {html[:500]}")
        # Detecta redirección JS
        js_redirect = re.search(r"window\\.location(?:\\.href|\\.replace)?\\s*=\\s*['\"]([^'\"]+)['\"]", html)
        if js_redirect:
            redirect_url = js_redirect.group(1)
            if not redirect_url.startswith('http'):
                redirect_url = urljoin(page_url, redirect_url)
            print(f"[scrape_video_url] Redirigiendo a: {redirect_url}")
            resp = requests.get(redirect_url, headers=headers, allow_redirects=True, timeout=10)
            html = resp.text
            print(f"[scrape_video_url] HTML tras redirección (primeros 500 chars): {html[:500]}")
        video_url, thumb_url = extract_video_and_thumb(html)
        print(f"[scrape_video_url] video_url: {video_url}, thumb_url: {thumb_url}")
        if video_url:
            return jsonify({'videoUrl': video_url, 'thumbnail': thumb_url})
        else:
            return jsonify({'error': 'No se encontró un link de video en la página'}), 404
    except Exception as e:
        print(f"[scrape_video_url] Error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)


# Endpoint proxy para servir videos remotos con CORS (solo para pruebas)
from flask import Response, request as flask_request

@app.route('/api/proxy-video', methods=['GET', 'OPTIONS'])
@cross_origin()
def proxy_video():
    video_url = flask_request.args.get('url')
    if not video_url:
        return jsonify({'error': 'Missing url'}), 400
    try:
        r = requests.get(video_url, stream=True, timeout=10)
        def generate():
            for chunk in r.iter_content(chunk_size=8192):
                yield chunk
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Content-Type': r.headers.get('Content-Type', 'video/mp4')
        }
        return Response(generate(), headers=headers)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
