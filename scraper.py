import re
from bs4 import BeautifulSoup

VIDEO_URL_RE = re.compile(r"html5player\\.setVideoUrlLow\('([^']+)'\)", re.IGNORECASE)
THUMB_URL_RE = re.compile(r"html5player\\.setThumbUrl169\('([^']+)'\)", re.IGNORECASE)

def extract_video_and_thumb(html):
    soup = BeautifulSoup(html, 'html.parser')
    hls_div = soup.find("div", id="hlsplayer")
    video_url = None
    thumb_url = None
    if hls_div:
        video_tag = hls_div.find("video")
        if video_tag and video_tag.get("src"):
            video_url = video_tag.get("src").strip()
        pic_div = hls_div.find("div", class_="video-pic")
        if pic_div:
            img_tag = pic_div.find("img")
            if img_tag and img_tag.get("src"):
                thumb_url = img_tag.get("src").strip()
    return video_url, thumb_url
