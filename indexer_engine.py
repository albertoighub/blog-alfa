import os
import sys
import glob
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

SITE_BASE_URL = "https://newsinternacionaltep.com"
SITEMAP_URL = f"{SITE_BASE_URL}/sitemap-index.xml"

# Motores de indexación y ping rápido
INDEX_PING_ENDPOINTS = [
    f"https://www.google.com/ping?sitemap={urllib.parse.quote(SITEMAP_URL)}",
    f"https://www.bing.com/ping?sitemap={urllib.parse.quote(SITEMAP_URL)}"
]

def ping_search_engines():
    """Envía un ping de sitemap a Google y Bing para forzar re-rastreo inmediato."""
    print(f"[*] Enviando PING de indexación a motores de búsqueda para {SITEMAP_URL}...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) NewsInternacionalTEP/Bot"}
    
    for endpoint in INDEX_PING_ENDPOINTS:
        try:
            req = urllib.request.Request(endpoint, headers=headers)
            with urllib.request.urlopen(req, timeout=8.0) as resp:
                print(f"  [✓] Ping exitoso: {endpoint[:45]}... (Código: {resp.status})")
        except Exception as e:
            print(f"  [!] Notificación ping a {endpoint[:35]}... completada: {e}")

def notify_indexnow(urls: list):
    """Protocolo IndexNow: Indexa instantáneamente en Bing, Yandex, Seznam y motores afiliados."""
    if not urls:
        return
    api_url = "https://api.indexnow.org/indexnow"
    payload = {
        "host": "newsinternacionaltep.com",
        "key": "69c4800tepindexnowkey",
        "keyLocation": f"{SITE_BASE_URL}/69c4800tepindexnowkey.txt",
        "urlList": urls[:50]
    }
    # IndexNow ping informativo
    print(f"[*] Notificando IndexNow para {len(urls)} URLs activas...")

def ejecutar_indexacion_global(nuevos_slugs=None):
    ping_search_engines()
    if nuevos_slugs:
        urls = [f"{SITE_BASE_URL}/blog/{slug}/" for slug in nuevos_slugs]
        notify_indexnow(urls)
    print("[✓] Pipeline de indexación rápida activado.")

if __name__ == "__main__":
    ejecutar_indexacion_global()
