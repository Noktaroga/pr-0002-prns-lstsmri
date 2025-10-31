import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup

# Configuración de Selenium para modo headless
chrome_options = Options()
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

# Cambia el path si usas otro navegador o driver
DRIVER_PATH = 'chromedriver'  # Asegúrate de tener chromedriver en tu PATH

DATA_FILE = 'data.json'

# Leer las URLs desde data.json
def get_page_urls():
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    urls = []
    # data es un dict: {categoria: [video, video, ...], ...}
    for categoria, videos in data.items():
        if isinstance(videos, list):
            for video in videos:
                if isinstance(video, dict):
                    url = video.get('page_url') or video.get('pageUrl')
                    if url:
                        urls.append(url)
    return urls

def extract_script_content(html):
    # Buscar cualquier ocurrencia de 'logged_user = false' en el HTML completo
    matches = []
    video_links = []
    search_str = 'logged_user = false'
    idx = 0
    while True:
        idx = html.find(search_str, idx)
        if idx == -1:
            break
        # Extraer contexto alrededor de la coincidencia
        start = max(0, idx - 100)
        end = min(len(html), idx + 200)
        context = html[start:end]
        matches.append(context)
        idx += len(search_str)

    # Si se encontró al menos una coincidencia, buscar los links de video
    if matches:
        import re
        # Buscar los links bajo el esquema html5player.setVideoUrlLow('...'), setVideoUrlHigh('...'), setVideoHLS('...')
        patterns = [
            r"html5player.setVideoUrlLow\(['\"](.*?)['\"]\)",
            r"html5player.setVideoUrlHigh\(['\"](.*?)['\"]\)",
            r"html5player.setVideoHLS\(['\"](.*?)['\"]\)"
        ]
        for pat in patterns:
            found = re.findall(pat, html)
            video_links.extend(found)
    return matches, video_links

def main():
    urls = get_page_urls()
    if not urls:
        print('No se encontraron URLs en data.json')
        return
    driver = webdriver.Chrome(options=chrome_options)
    for url in urls:
        print(f'Accediendo a: {url}')
        try:
            driver.get(url)
            time.sleep(2)  # Espera a que cargue la página
            html = driver.page_source
            matches, video_links = extract_script_content(html)
            if matches:
                print(f"--- {len(matches)} OCURRENCIA(S) DE 'logged_user = false' ENCONTRADA(S) ---")
                for i, context in enumerate(matches, 1):
                    print(f"[Match {i}]:\n{context}\n")
                print('---------------------------------------------')
                if video_links:
                    print('Links de video encontrados:')
                    for link in video_links:
                        print(link)
                else:
                    print('No se encontraron links de video bajo el esquema esperado.')
                print('\n')
            else:
                print("No se encontró 'logged_user = false' en el HTML.\n")
        except Exception as e:
            print(f'Error accediendo a {url}: {e}')
    driver.quit()

if __name__ == '__main__':
    main()
