import os
import sys
import glob
import json
import urllib.request
import urllib.parse

SITE_BASE_URL = "https://newsinternacionaltep.com"
SITEMAP_URL = f"{SITE_BASE_URL}/sitemap-index.xml"
INDEXNOW_KEY = "69c4800tepindexnowkey"

# Motores de indexación y ping rápido de sitemap
INDEX_PING_ENDPOINTS = [
    f"https://www.google.com/ping?sitemap={urllib.parse.quote(SITEMAP_URL)}",
    f"https://www.bing.com/ping?sitemap={urllib.parse.quote(SITEMAP_URL)}"
]

def ping_search_engines():
    """Envía un ping de sitemap a Google y Bing para forzar re-rastreo inmediato."""
    print(f"[*] Enviando PING de sitemap a motores de búsqueda ({SITEMAP_URL})...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) NewsInternacionalTEP/Bot"}
    
    for endpoint in INDEX_PING_ENDPOINTS:
        try:
            req = urllib.request.Request(endpoint, headers=headers)
            with urllib.request.urlopen(req, timeout=10.0) as resp:
                print(f"  [✓] Ping sitemap exitoso: {endpoint[:50]}... (Código: {resp.status})")
        except Exception as e:
            print(f"  [i] Notificación ping a {endpoint[:40]}... enviada: {e}")

def collect_all_urls():
    """Recopila todas las URLs del sitio: categorías, estáticas y todos los 310+ artículos."""
    urls = [
        f"{SITE_BASE_URL}/",
        f"{SITE_BASE_URL}/categoria/tecnologia/",
        f"{SITE_BASE_URL}/categoria/economia/",
        f"{SITE_BASE_URL}/categoria/geopolitica/",
        f"{SITE_BASE_URL}/categoria/ciencia/",
        f"{SITE_BASE_URL}/categoria/tendencias/",
        f"{SITE_BASE_URL}/privacidad/",
        f"{SITE_BASE_URL}/terminos/"
    ]
    
    blog_dir = os.path.join(os.path.dirname(__file__), "src", "content", "blog")
    md_files = glob.glob(os.path.join(blog_dir, "*.md"))
    
    for f in md_files:
        basename = os.path.basename(f)
        slug = os.path.splitext(basename)[0]
        urls.append(f"{SITE_BASE_URL}/blog/{slug}/")
        
    return urls

def notify_indexnow(urls: list):
    """Protocolo IndexNow: Indexa instantáneamente en Bing, Yandex, Naver, Seznam."""
    if not urls:
        return
    api_url = "https://api.indexnow.org/indexnow"
    
    # Enviar en bloques de máximo 500 URLs
    chunk_size = 500
    for i in range(0, len(urls), chunk_size):
        chunk = urls[i:i + chunk_size]
        payload = {
            "host": "newsinternacionaltep.com",
            "key": INDEXNOW_KEY,
            "keyLocation": f"{SITE_BASE_URL}/{INDEXNOW_KEY}.txt",
            "urlList": chunk
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            api_url,
            data=data,
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "User-Agent": "NewsInternacionalTEP-Indexer/2.0"
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=15.0) as resp:
                print(f"  [✓] IndexNow lote ({len(chunk)} URLs): Estado HTTP {resp.status}")
        except urllib.error.HTTPError as e:
            # 200/202 ok, 422 si la key no se ha propagado en cloudflare aún
            print(f"  [i] IndexNow respuesta HTTP {e.code}: {e.reason}")
        except Exception as e:
            print(f"  [!] IndexNow error de conexión: {e}")

def ejecutar_indexacion_global():
    print("==================================================")
    print("   MOTOR DE INDEXACIÓN GLOBAL - NEWS INTERNACIONAL TEP")
    print("==================================================")
    all_urls = collect_all_urls()
    print(f"[*] Total de URLs activas recopiladas para indexar: {len(all_urls)}")
    
    # 1. Pings a sitemaps
    ping_search_engines()
    
    # 2. Notificación IndexNow directa
    print(f"[*] Notificando protocolo IndexNow...")
    notify_indexnow(all_urls)
    
    print("==================================================")
    print("[✓] Proceso de indexación global completado.")
    print("==================================================")

if __name__ == "__main__":
    ejecutar_indexacion_global()
