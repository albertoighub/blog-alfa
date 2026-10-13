import os
import json
import html
import time
import random
import urllib.request
import urllib.error
from datetime import datetime
from slugify import slugify
import feedparser
from google import genai
from google.genai import types

# 1. Configuración de API y Canales
client = genai.Client()
MODELO = "gemini-3.5-flash-lite"
OUTPUT_DIR = os.path.join("src", "content", "blog")
HISTORY_FILE = "history.json"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8637388923:AAHl2omIwOIV5dd6uOd_Ho3stAsSMXTNMTY")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "-1004371603591")
SITE_BASE_URL = "https://newsinternacionaltep.com"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# 2. Malla Masiva Seleccionada del Directorio Global de 165 Medios
FEEDS = {
    "Geopolítica": [
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://rss.politico.com/politics-news.xml",
        "https://thehill.com/feed/",
        "https://www.aljazeera.com/xml/rss/all.xml",
        "https://www.theguardian.com/world/rss",
        "https://www.scmp.com/rss/91/feed",
        "https://kyivindependent.com/feed/",
        "https://thediplomat.com/feed/",
        "https://www.france24.com/es/rss",
    ],
    "Economía": [
        "https://feeds.content.dowjones.io/public/rss/mw_topstories",
        "https://search.cnbc.com/rs/search/view.html?partnerId=2000&keywords=markets&sort=date&type=rss",
        "https://search.cnbc.com/rs/search/view.html?partnerId=2000&keywords=economy&sort=date&type=rss",
        "https://finance.yahoo.com/news/rssindex",
        "https://www.investing.com/rss/news_25.rss",
        "https://asia.nikkei.com/rss/feed/category/business",
        "https://www.economist.com/finance-and-economics/rss.xml",
        "https://cincodias.elpais.com/seccion/rss/mercados/",
    ],
    "Tecnología": [
        "https://techcrunch.com/feed/",
        "https://feeds.arstechnica.com/arstechnica/index",
        "https://www.wired.com/feed/category/business/latest/rss",
        "https://www.theverge.com/rss/index.xml",
        "https://spectrum.ieee.org/rss/rocs/robotics",
        "https://venturebeat.com/feed/",
        "https://www.technologyreview.com/feed/",
        "https://krebsonsecurity.com/feed/",
        "https://www.bleepingcomputer.com/feed/",
    ],
}

IMAGENES_EDITORIALES = {
    "Geopolítica": [
        "https://images.unsplash.com/photo-1541872703-74c5e44368f9?auto=format&fit=crop&w=1400&q=80",
        "https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?auto=format&fit=crop&w=1400&q=80",
        "https://images.unsplash.com/photo-1577495508048-b635879837f1?auto=format&fit=crop&w=1400&q=80",
        "https://images.unsplash.com/photo-1509062522246-3755977927d7?auto=format&fit=crop&w=1400&q=80",
    ],
    "Economía": [
        "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1400&q=80",
        "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=1400&q=80",
        "https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=1400&q=80",
        "https://images.unsplash.com/photo-1559526324-4b87b5e36e44?auto=format&fit=crop&w=1400&q=80",
    ],
    "Tecnología": [
        "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=1400&q=80",
        "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1400&q=80",
        "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?auto=format&fit=crop&w=1400&q=80",
        "https://images.unsplash.com/photo-1531297484001-80022131f5a1?auto=format&fit=crop&w=1400&q=80",
    ],
}

# 3. Directriz Editorial de Revista Científica y Arbitraje de Inteligencia
SYSTEM_INSTRUCTION = """Actúa como el Director de un Instituto Científico de Inteligencia y Revista de Prospectiva Internacional (al nivel de 'Foreign Affairs', 'Nature' y 'Financial Times').
Tu objetivo es tomar datos noticiosos crudos y transformarlos en un Paper Científico / Reporte de Inteligencia Estructural de máxima densidad, rigor y originalidad.

REGLAS DE ARBITRAJE CIENTÍFICO:
1. CERO PLAGIO Y REESCRITURA TOTAL: Nunca repitas la estructura ni las frases de los cables. Reformula, amplía y profundiza con vocabulario formal, técnico y analítico.
2. DENSIDAD Y CAUSALIDAD: Explica las variables independientes, los mecanismos de transmisión de la crisis y los factores detonantes.
3. DATOS DUROS Y PARÁMETROS OPERATIVOS: Extrae cifras exactas (PIB, tasas base, volúmenes de capital, nodos tecnológicos, cronogramas).
4. SINERGIA E IMPACTO SISTÉMICO GLOBAL: Analiza las repercusiones cruzadas (ej. cómo una decisión política altera los suministros tecnológicos y la liquidez bursátil).
5. FORMATO DE PUBLICACIÓN:
   - "title": Titular formal de impacto estructural (sin amarillismo).
   - "description": Abstract académico estructurado (140 a 160 caracteres).
   - "category": 'Geopolítica', 'Economía' o 'Tecnología'.
   - "tags": 4 o 5 descriptores temáticos científicos.
   - "metrics": Lista con 3 viñetas cuantificadas detallando variables clave.
   - "content": Cuerpo del paper en Markdown estructurado en secciones con subtítulos ## (ej: '## Mecanismos Estructurales y Contexto', '## Análisis de Fuerzas y Contraste de Actores', '## Sinergia e Impacto en Cadenas Globales').
   - "prospectiva": Dos párrafos de proyección a 12-24 meses evaluando escenarios de equilibrio o ruptura.
   - "methodology": Resumen de triangulación de fuentes y verificación."""

def cargar_historial() -> list:
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def guardar_historial(historial: list):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(historial, f, indent=2, ensure_ascii=False)

def broadcast_telegram(data: dict, post_slug: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL_ID:
        return

    article_url = f"{SITE_BASE_URL}/blog/{post_slug}/"
    category = html.escape(data.get("category", "Noticias"))
    title = html.escape(data.get("title", ""))
    description = html.escape(data.get("description", ""))

    raw_tags = data.get("tags", [])
    hashtags = " ".join([f"#{slugify(t, separator='')}" for t in raw_tags]) if raw_tags else ""

    message = (
        f"🔬 <b>DOSSIER CIENTÍFICO | {category.upper()}</b>\n\n"
        f"<b>{title}</b>\n\n"
        f"<i>{description}</i>\n\n"
        f"📊 <a href='{article_url}'>Acceder al Paper Completo & Métricas</a>\n\n"
        f"{hashtags}"
    ).strip()

    endpoint = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = json.dumps({
        "chat_id": TELEGRAM_CHANNEL_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }).encode("utf-8")

    req = urllib.request.Request(endpoint, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            if res_data.get("ok"):
                print(" [✓] Paper publicado y despachado en Telegram.")
    except Exception as e:
        print(f" [!] Error en Telegram: {e}")

def procesar_noticia_con_reintentos(entry, categoria: str, max_intentos: int = 3):
    prompt = f"""
    Elabora un Paper de Inteligencia y Análisis Científico de alta densidad a partir de estos datos:
    - Campo de Estudio: {categoria}
    - Suceso Noticioso: {entry.get('title', '')}
    - Fuente Primaria: {entry.get('link', '')}
    - Extracto Bruto: {entry.get('summary', '')}
    """

    for intento in range(1, max_intentos + 1):
        try:
            response = client.models.generate_content(
                model=MODELO,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    response_mime_type="application/json",
                    temperature=0.25,
                ),
            )
            return json.loads(response.text)
        except Exception as e:
            print(f" [!] Intento {intento}/{max_intentos} fallido en Gemini ({e}).")
            if intento < max_intentos:
                tiempo_espera = intento * 5
                print(f" [*] Reintentando en {tiempo_espera}s...")
                time.sleep(tiempo_espera)
            else:
                return None

def guardar_paper(data: dict, fuente_original: str) -> str:
    slug = slugify(data["title"][:50])
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    post_slug = f"{fecha_actual}-{slug}"
    nombre_archivo = f"{post_slug}.md"
    ruta_completa = os.path.join(OUTPUT_DIR, nombre_archivo)

    tags_formateados = json.dumps(data.get("tags", []))
    categoria = data.get("category", "Geopolítica")
    lista_imgs = IMAGENES_EDITORIALES.get(categoria, IMAGENES_EDITORIALES["Geopolítica"])
    imagen_hero = random.choice(lista_imgs)

    metrics_list = data.get("metrics", [])
    metrics_block = ""
    if metrics_list:
        metrics_block = "> ### Parámetros Operativos & Variables Clave\n" + "\n".join([f"> * **{m}**" for m in metrics_list]) + "\n\n"

    prospectiva_bloque = data.get("prospectiva", "El desarrollo de los acontecimientos exigirá seguimiento continuo de las cadenas de impacto.")

    contenido_md = f"""---
title: "{data['title']}"
description: "{data['description']}"
pubDate: "{fecha_actual}"
category: "{categoria}"
tags: {tags_formateados}
heroImage: "{imagen_hero}"
canonicalSource: "{fuente_original}"
---

{metrics_block}{data['content']}

## Sinergia Sistémica y Prospectiva Global (12-24 Meses)

{prospectiva_bloque}

---

### Metodología de Verificación y Referencias Primarias
* **Documentación Base de Rastreo:** [{fuente_original}]({fuente_original})
* **Marco de Arbitraje Analítico:** {data.get('methodology', 'Investigación elaborada mediante agregación multifuente y modelado de impacto estructural independiente.')}
"""

    with open(ruta_completa, "w", encoding="utf-8") as f:
        f.write(contenido_md)

    print(f"[+] Paper científico consolidado: {nombre_archivo}")
    return post_slug

def ejecutar_pipeline():
    print("=== MOTOR CIENTÍFICO TEP: Malla Global (165 Fuentes) & Papers de Fondo ===")
    historial = cargar_historial()
    nuevos_procesados = 0

    # Procesa 1 reporte riguroso por categoría en cada ciclo (3 cada 4h = 18 al día)
    for categoria, urls in FEEDS.items():
        # Mezcla las fuentes para que la investigación rote dinámicamente
        urls_mezcladas = urls.copy()
        random.shuffle(urls_mezcladas)

        for url in urls_mezcladas:
            try:
                feed = feedparser.parse(url)
                noticia_objetivo = None
                for entry in feed.entries:
                    link = entry.get("link", "")
                    if link and link not in historial:
                        noticia_objetivo = entry
                        break

                if noticia_objetivo:
                    link = noticia_objetivo.get("link", "")
                    print(f"[*] Analizando suceso en {categoria}: {noticia_objetivo.get('title', '')[:50]}...")
                    resultado = procesar_noticia_con_reintentos(noticia_objetivo, categoria)

                    if resultado:
                        post_slug = guardar_paper(resultado, link)
                        historial.append(link)
                        guardar_historial(historial)
                        broadcast_telegram(resultado, post_slug)
                        nuevos_procesados += 1
                        break
            except Exception as ex:
                print(f" [!] Error al procesar {url}: {ex}")

    print(f"=== Ciclo Concluido: {nuevos_procesados} Papers Científicos Publicados ===")

if __name__ == "__main__":
    ejecutar_pipeline()