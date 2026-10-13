import os
import json
import html
import urllib.request
import urllib.error
from datetime import datetime
from slugify import slugify
import feedparser
from google import genai
from google.genai import types

# 1. Configuración de API, almacenamiento y Telegram
client = genai.Client()
MODELO = "gemini-3.5-flash-lite"
OUTPUT_DIR = os.path.join("src", "content", "blog")
HISTORY_FILE = "history.json"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8637388923:AAHl2omIwOIV5dd6uOd_Ho3stAsSMXTNMTY")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "@newsinternacionaltep")
SITE_BASE_URL = "https://newsinternacionaltep.com"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# 2. Fuentes RSS clasificadas por categoría
FEEDS = {
    "Tecnología": [
        "https://techcrunch.com/feed/",
    ],
    "Economía": [
        "https://feeds.content.dowjones.io/public/rss/mw_topstories",
    ],
    "Política": [
        "https://rss.politico.com/politics-news.xml",
    ],
}

# 3. Directriz editorial neutral para AdSense E-E-A-T
SYSTEM_INSTRUCTION = """Eres un analista periodístico especializado en Tecnología, Economía y Política global para el portal 'News Internacional TEP'.
Tu tarea es tomar una noticia cruda y transformarla en un análisis profundo, objetivo e imparcial.

Directrices editoriales estrictas:
1. No te limites a resumir; analiza la causa, el contexto y el impacto estructural del acontecimiento.
2. Tono riguroso, formal y neutral (sin opiniones personales ni sesgo partidista).
3. Redacta en español neutro de alta calidad periodística.
4. Devuelve ÚNICAMENTE un objeto JSON válido con las siguientes claves:
   - "title": Título informativo y profesional.
   - "description": Resumen conciso para SEO (máximo 150 caracteres).
   - "category": La categoría asignada ('Tecnología', 'Economía' o 'Política').
   - "tags": Lista de 3 a 5 palabras clave en formato de lista JSON.
   - "content": Cuerpo completo del análisis redactado en formato Markdown (usa subtítulos ##, listas con viñetas y párrafos bien estructurados).
   - "sources_summary": Párrafo breve resumiendo las posturas o datos oficiales mencionados."""

def cargar_historial() -> list:
    """Recupera los enlaces de noticias ya procesadas con anterioridad."""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def guardar_historial(historial: list):
    """Guarda de forma persistente los enlaces procesados."""
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(historial, f, indent=2, ensure_ascii=False)

def broadcast_telegram(data: dict, post_slug: str):
    """Difunde la noticia directamente al canal de Telegram utilizando la librería estándar de Python."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL_ID:
        print(" [!] Configuración de Telegram incompleta. Omitiendo emisión.")
        return

    article_url = f"{SITE_BASE_URL}/blog/{post_slug}/"
    category = html.escape(data.get("category", "Noticias"))
    title = html.escape(data.get("title", ""))
    description = html.escape(data.get("description", ""))

    raw_tags = data.get("tags", [])
    hashtags = " ".join([f"#{slugify(t, separator='')}" for t in raw_tags]) if raw_tags else ""

    message = (
        f"🚨 <b>{category.upper()} | News Internacional TEP</b>\n\n"
        f"<b>{title}</b>\n\n"
        f"{description}\n\n"
        f"🔗 <a href='{article_url}'>Leer análisis completo</a>\n\n"
        f"{hashtags}"
    ).strip()

    endpoint = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = json.dumps({
        "chat_id": TELEGRAM_CHANNEL_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }).encode("utf-8")

    req = urllib.request.Request(
        endpoint,
        data=payload,
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            if res_data.get("ok"):
                print(" [✓] Noticia difundida exitosamente en el canal de Telegram.")
            else:
                print(f" [!] Respuesta inesperada de Telegram: {res_data}")
    except urllib.error.HTTPError as e:
        print(f" [!] Error HTTP en Telegram API ({e.code}): {e.read().decode('utf-8')}")
    except Exception as e:
        print(f" [!] Excepción al conectar con Telegram: {e}")

def procesar_noticia(entry, categoria: str):
    """Envía la noticia a Gemini para estructuración analítica."""
    prompt = f"""
    Procesa la siguiente noticia informativa:
    - Categoría base: {categoria}
    - Título original: {entry.get('title', '')}
    - Enlace oficial: {entry.get('link', '')}
    - Resumen original: {entry.get('summary', '')}
    """

    try:
        response = client.models.generate_content(
            model=MODELO,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"[!] Error al procesar noticia con Gemini: {e}")
        return None

def guardar_articulo(data: dict, fuente_original: str) -> str:
    """Genera el archivo .md compatible con las colecciones de Astro y retorna el slug."""
    slug = slugify(data["title"][:50])
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    post_slug = f"{fecha_actual}-{slug}"
    nombre_archivo = f"{post_slug}.md"
    ruta_completa = os.path.join(OUTPUT_DIR, nombre_archivo)

    tags_formateados = json.dumps(data.get("tags", []))

    contenido_md = f"""---
title: "{data['title']}"
description: "{data['description']}"
pubDate: "{fecha_actual}"
category: "{data['category']}"
tags: {tags_formateados}
canonicalSource: "{fuente_original}"
---

{data['content']}

---

### Fuentes y Transparencia Informativa
* **Fuente de Referencia:** [{fuente_original}]({fuente_original})
* **Metodología:** {data.get('sources_summary', 'Contenido sintetizado y contrastado a partir de fuentes informativas abiertas.')}
"""

    with open(ruta_completa, "w", encoding="utf-8") as f:
        f.write(contenido_md)

    print(f"[+] Artículo generado: {nombre_archivo}")
    return post_slug

def ejecutar_pipeline():
    """Ejecuta la curaduría evitando duplicados y difundiendo en Telegram."""
    print("=== Iniciando Pipeline de Noticias TEP con Antiduplicados y Telegram ===")
    historial = cargar_historial()
    nuevos_procesados = 0

    for categoria, urls in FEEDS.items():
        for url in urls:
            print(f"[*] Revisando feed de {categoria}...")
            feed = feedparser.parse(url)

            noticia_objetivo = None
            for entry in feed.entries:
                link = entry.get("link", "")
                if link and link not in historial:
                    noticia_objetivo = entry
                    break

            if noticia_objetivo:
                link = noticia_objetivo.get("link", "")
                print(f" -> Procesando nueva noticia: {noticia_objetivo.get('title', 'Sin título')}")
                resultado = procesar_noticia(noticia_objetivo, categoria)

                if resultado:
                    post_slug = guardar_articulo(resultado, link)
                    historial.append(link)
                    guardar_historial(historial)
                    broadcast_telegram(resultado, post_slug)
                    nuevos_procesados += 1
            else:
                print(f" [=] No hay noticias nuevas en {categoria} (todas procesadas).")

    print(f"=== Pipeline finalizado: {nuevos_procesados} artículos nuevos añadidos ===")

if __name__ == "__main__":
    ejecutar_pipeline()