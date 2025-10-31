
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import json
import os
import requests
import re
import time
from urllib.parse import urljoin, unquote
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

PORT = int(os.environ.get('PORT', 3001))
DATA_FILE = os.path.join(os.getcwd(), 'data.json')


# Endpoint para scraping headless con Selenium
@app.route('/api/selenium-scrape', methods=['POST'])
@cross_origin()
def selenium_scrape():
    data = request.get_json()
    page_url = data.get('page_url') or data.get('pageUrl')
    if not page_url:
        return jsonify({'error': 'Missing page_url'}), 400
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(page_url)
        time.sleep(2)
        html = driver.page_source
        driver.quit()
        # Buscar 'logged_user = false' y extraer links
        if 'logged_user = false' not in html:
            return jsonify({'error': "'logged_user = false' not found in HTML"}), 404
        patterns = [
            r"html5player.setVideoUrlLow\(['\"](.*?)['\"]\)",
            r"html5player.setVideoUrlHigh\(['\"](.*?)['\"]\)",
            r"html5player.setVideoHLS\(['\"](.*?)['\"]\)"
        ]
        video_links = []
        for pat in patterns:
            found = re.findall(pat, html)
            video_links.extend(found)
        return jsonify({'video_links': video_links})
    except Exception as e:
        return jsonify({'error': str(e)}), 500



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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)