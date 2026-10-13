import os
import json
import html
import random
import urllib.request
import urllib.error
from datetime import datetime
from slugify import slugify
import feedparser
from google import genai
from google.genai import types

# 1. Configuración del Cliente y Canales
client = genai.Client()
MODELO = "gemini-3.5-flash-lite"
OUTPUT_DIR = os.path.join("src", "content", "blog")
HISTORY_FILE = "history.json"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8637388923:AAHl2omIwOIV5dd6uOd_Ho3stAsSMXTNMTY")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "-1004371603591")
SITE_BASE_URL = "https://newsinternacionaltep.com"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# 2. Malla internacional masiva de agencias y medios (Top Selection del Directorio de 165 sitios)
FEEDS = {
    "Geopolítica": [
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://rss.politico.com/politics-news.xml",
        "https://www.aljazeera.com/xml/rss/all.xml",
        "https://www.theguardian.com/world/rss",
        "https://www.scmp.com/rss/91/feed",
    ],
    "Economía": [
        "https://feeds.content.dowjones.io/public/rss/mw_topstories",
        "https://search.cnbc.com/rs/search/view.html?partnerId=2000&keywords=markets&sort=date&type=rss",
        "https://finance.yahoo.com/news/rssindex",
        "https://www.ft.com/?format=rss",
        "https://asia.nikkei.com/rss/feed/category/business",
    ],
    "Tecnología": [
        "https://techcrunch.com/feed/",
        "https://feeds.arstechnica.com/arstechnica/index",
        "https://www.wired.com/feed/category/business/latest/rss",
        "https://spectrum.ieee.org/rss/rocs/robotics",
        "https://www.theverge.com/rss/index.xml",
    ],
}

# Imágenes contextuales de archivo de prensa en alta resolución
IMAGENES_EDITORIALES = {
    "Geopolítica": [
        "https://images.unsplash.com/photo-1541872703-74c5e44368f9?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1577495508048-b635879837f1?auto=format&fit=crop&w=1200&q=80",
    ],
    "Economía": [
        "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=1200&q=80",
    ],
    "Tecnología": [
        "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?auto=format&fit=crop&w=1200&q=80",
    ],
}

# 3. Directiva de Cero Plagio y Sobreescritura Máxima
SYSTEM_INSTRUCTION = """Eres el motor de inteligencia analítica central de 'News Internacional TEP'.
Tu tarea es consumir los datos crudos proporcionados de agencias globales y convertirlos en reportes investigativos 100% nuevos, densos y originales.

REGLA DE ORO INQUEBRANTABLE: BAJO NINGUNA CIRCUNSTANCIA copiarás de manera literal el texto original de la fuente. Debes leer el suceso, procesarlo como un experto en geopolítica/finanzas, y reescribir un análisis estructural con tus propias palabras, utilizando un lenguaje sobrio, neutral y académico.

Estructura requerida:
1. Reescritura Analítica Total: No eres un traductor, eres un analista de The New York Times/Bloomberg. Desmenuza el qué, el porqué y las causas de fondo.
2. Extracción de Métricas Duras: Identifica cifras monetarias, porcentajes o fechas clave y preséntalas de forma concisa.
3. Prospectiva a 24 Meses: Deduce y redacta el impacto que este suceso tendrá a nivel global en el corto y mediano plazo.

Devuelve ÚNICAMENTE un objeto JSON válido con estas claves:
- "title": Titular periodístico sobrio y formal (100% reescrito).
- "description": Subtítulo analítico (140 a 160 caracteres).
- "category": La categoría exacta ('Geopolítica', 'Economía' o 'Tecnología').
- "tags": Lista de 4 o 5 palabras clave de indexación.
- "key_metrics": Lista de 3 viñetas concisas con datos cuantitativos clave del evento.
- "content": Cuerpo completo del análisis redactado en Markdown con secciones densas mediante subtítulos ## y párrafos desarrollados (Totalmente original, cero plagio).
- "global_impact": Dos párrafos de prospectiva estratégica y efecto dominó en los mercados o la diplomacia.
- "sources_summary": Párrafo que indique "Informe redactado tras el monitoreo y contraste de datos emitidos originalmente por agencias internacionales..."."""

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
        f"🚨 <b>{category.upper()} | Análisis Estructural</b>\n\n"
        f"<b>{title}</b>\n\n"
        f"{description}\n\n"
        f"🔗 <a href='{article_url}'>Leer informe completo</a>\n\n"
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
                print(" [✓] Alerta de inteligencia despachada a Telegram.")
    except Exception as e:
        print(f" [!] Error en Telegram: {e}")

def procesar_noticia(entry, categoria: str):
    prompt = f"""
    Lee los siguientes datos crudos e instaura un informe 100% original, reescrito desde cero con profundidad analítica:
    - Categoría Operativa: {categoria}
    - Titular fuente: {entry.get('title', '')}
    - Enlace primario: {entry.get('link', '')}
    - Extracto crudo: {entry.get('summary', '')}
    """

    try:
        response = client.models.generate_content(
            model=MODELO,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                temperature=0.3, # Ligero aumento para mayor originalidad y evitar réplicas
            ),
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"[!] Error procesando el prompt: {e}")
        return None

def guardar_articulo(data: dict, fuente_original: str) -> str:
    slug = slugify(data["title"][:50])
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    post_slug = f"{fecha_actual}-{slug}"
    nombre_archivo = f"{post_slug}.md"
    ruta_completa = os.path.join(OUTPUT_DIR, nombre_archivo)

    tags_formateados = json.dumps(data.get("tags", []))
    categoria = data.get("category", "Geopolítica")
    lista_imgs = IMAGENES_EDITORIALES.get(categoria, IMAGENES_EDITORIALES["Geopolítica"])
    imagen_hero = random.choice(lista_imgs)

    metrics_list = data.get("key_metrics", [])
    metrics_block = ""
    if metrics_list:
        metrics_block = "> ### Indicadores y Cifras Clave\n" + "\n".join([f"> * **{m}**" for m in metrics_list]) + "\n\n"

    impacto_bloque = data.get("global_impact", "El suceso altera significativamente las dinámicas de poder.")

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

## Impacto Estructural y Prospectiva Global

{impacto_bloque}

---

### Metodología y Trazabilidad del Monitoreo
* **Cita Origen de Agregación:** [{fuente_original}]({fuente_original})
* **Marco de Verificación Legal:** {data.get('sources_summary', 'Informe redactado a partir del procesamiento y reestructuración analítica de datos en tiempo real.')}
"""

    with open(ruta_completa, "w", encoding="utf-8") as f:
        f.write(contenido_md)

    print(f"[+] Informe analítico consolidado: {nombre_archivo}")
    return post_slug

def ejecutar_pipeline():
    print("=== IA TEP | Extracción de Red Global y Reescritura Analítica ===")
    historial = cargar_historial()
    nuevos_procesados = 0

    for categoria, urls in FEEDS.items():
        for url in urls:
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
                    print(f"[*] Transformando fuente en {categoria}: {noticia_objetivo.get('title', '')[:45]}...")
                    resultado = procesar_noticia(noticia_objetivo, categoria)

                    if resultado:
                        post_slug = guardar_articulo(resultado, link)
                        historial.append(link)
                        guardar_historial(historial)
                        broadcast_telegram(resultado, post_slug)
                        nuevos_procesados += 1
                        break
            except Exception as ex:
                print(f" [!] Error en la consulta del feed {url}: {ex}")

    print(f"=== Ciclo Inteligente Finalizado: {nuevos_procesados} Reportes Originales Publicados ===")

if __name__ == "__main__":
    ejecutar_pipeline()