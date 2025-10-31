from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote

app = Flask(__name__)
CORS(app)

PORT = int(os.environ.get('PORT', 3001))
DATA_FILE = os.path.join(os.getcwd(), 'data.json')

@app.route('/api', methods=['GET'])
def healthcheck():
    return jsonify({"ok": True, "message": "API funcionando correctamente ✅"})

@app.route('/api/videos', methods=['GET'])
def get_videos():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        print(f"Error leyendo data.json: {e}")
        return jsonify({"error": "No se pudo leer data.json en el backend"}), 500

@app.route('/api/videos/by-category/<cat>', methods=['GET'])
def get_videos_by_category(cat):
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        cat_key = unquote(cat)
        if cat_key not in data:
            return jsonify({"error": "Categoría no encontrada"}), 404
        return jsonify(data[cat_key])
    except Exception as e:
        print(f"Error leyendo data.json: {e}")
        return jsonify({"error": "No se pudo leer data.json en el backend"}), 500

@app.route('/api/scrape-video-url', methods=['POST'])
def scrape_video_url():
    page_url = request.json.get('page_url')
    if not page_url:
        return jsonify({'error': 'Missing page_url'}), 400
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)'}
        resp = requests.get(page_url, headers=headers, allow_redirects=True, timeout=10)
        html = resp.text
        with open('debug_step1.html', 'w', encoding='utf-8') as f:
            f.write(html)
        # Detect JS redirect
        import re
        js_redirect = re.search(r"window\\.location(?:\\.href|\\.replace)?\\s*=\\s*['\"]([^'\"]+)['\"]", html)
        if js_redirect:
            redirect_url = js_redirect.group(1)
            if not redirect_url.startswith('http'):
                redirect_url = urljoin(page_url, redirect_url)
            resp = requests.get(redirect_url, headers=headers, allow_redirects=True, timeout=10)
            html = resp.text
            with open('debug_step2.html', 'w', encoding='utf-8') as f:
                f.write(html)
        soup = BeautifulSoup(html, 'html.parser')
        video_url = None
        hls_div = soup.find(id='hlsplayer')
        if hls_div:
            video_tag = hls_div.find('video')
            if video_tag and video_tag.get('src'):
                video_url = video_tag['src'].strip()
        if not video_url:
            for script in soup.find_all('script'):
                txt = script.string
                if txt:
                    match = re.search(r"html5player\\.setVideoUrlLow\\('([^']+)'\\)", txt)
                    if match:
                        video_url = match.group(1)
                        break
        if video_url:
            return jsonify({'videoUrl': video_url})
        else:
            return jsonify({'error': 'No se encontró un link de video en la página'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)
