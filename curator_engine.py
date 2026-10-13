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

# 2. Malla internacional multi-dominio de agencias y medios
FEEDS = {
    "Geopolítica": [
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://rss.politico.com/politics-news.xml",
        "https://thehill.com/feed/",
        "https://www.aljazeera.com/xml/rss/all.xml",
        "https://www.theguardian.com/world/rss",
    ],
    "Economía": [
        "https://feeds.content.dowjones.io/public/rss/mw_topstories",
        "https://search.cnbc.com/rs/search/view.html?partnerId=2000&keywords=economy&sort=date&type=rss",
        "https://search.cnbc.com/rs/search/view.html?partnerId=2000&keywords=markets&sort=date&type=rss",
        "https://finance.yahoo.com/news/rssindex",
    ],
    "Tecnología": [
        "https://techcrunch.com/feed/",
        "https://feeds.arstechnica.com/arstechnica/index",
        "https://www.theverge.com/rss/index.xml",
        "https://www.wired.com/feed/category/business/latest/rss",
    ],
}

# Imágenes contextuales de archivo de prensa en alta resolución
IMAGENES_EDITORIALES = {
    "Geopolítica": [
        "https://images.unsplash.com/photo-1541872703-74c5e44368f9?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1577495508048-b635879837f1?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1509062522246-3755977927d7?auto=format&fit=crop&w=1200&q=80",
    ],
    "Economía": [
        "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1559526324-4b87b5e36e44?auto=format&fit=crop&w=1200&q=80",
    ],
    "Tecnología": [
        "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1531297484001-80022131f5a1?auto=format&fit=crop&w=1200&q=80",
    ],
}

SYSTEM_INSTRUCTION = """Eres el analista jefe y corresponsal internacional senior de 'News Internacional TEP'.
Tu tarea es producir reportes de investigación periodística de altísima densidad analítica, comparables con The New York Times, Foreign Affairs o Financial Times.

Criterios editoriales estrictos:
1. No hagas resúmenes superficiales: Profundiza en las causas estructurales, intereses geopolíticos y dinámicas de poder subyacentes.
2. Contraste de posturas: Analiza las diferentes partes involucradas (gobiernos occidentales vs emergentes, reguladores vs industria, halcones vs palomas, mercados vs política).
3. Datos duros y cuantitativos: Extrae o contextualiza con precisión cifras monetarias, porcentajes de variación, plazos temporales o proyecciones de volumen.
4. Tono riguroso e imparcial: Lenguaje analítico, sobrio, sin sensacionalismo ni valoraciones subjetivas.
5. Prospectiva Global: Reflexiona sobre qué consecuencias tendrá este acontecimiento para la estabilidad mundial, la cadena de valor o los mercados en los próximos 12 a 24 meses.

Devuelve ÚNICAMENTE un objeto JSON válido con estas claves:
- "title": Titular periodístico de gran impacto (estilo NYT, sobrio y contundente).
- "description": Subtítulo analítico exhaustivo (140 a 160 caracteres).
- "category": La categoría exacta ('Geopolítica', 'Economía' o 'Tecnología').
- "tags": Lista de 4 o 5 palabras clave de indexación profesional.
- "key_metrics": Lista de 3 viñetas concisas con datos cuantitativos clave (ejemplo: "USD 12,500M: Capital movilizado...", "+4.3%: Incremento proyectado...", "T4 2026: Plazo de implementación...").
- "content": Cuerpo completo del análisis redactado en Markdown con secciones densas mediante subtítulos ##, citas formales en bloque > y párrafos explicativos desarrollados.
- "global_impact": Dos párrafos redactados que desglosan la prospectiva estratégica y el efecto dominó internacional.
- "sources_summary": Párrafo que resume las fuentes primarias contrastadas y el contexto institucional consultado."""

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
        f"🚨 <b>{category.upper()} | News Internacional TEP</b>\n\n"
        f"<b>{title}</b>\n\n"
        f"{description}\n\n"
        f"🔗 <a href='{article_url}'>Leer informe analítico y prospectiva global</a>\n\n"
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
                print(" [✓] Noticia de fondo difundida en Telegram.")
    except Exception as e:
        print(f" [!] Error en Telegram: {e}")

def procesar_noticia(entry, categoria: str):
    prompt = f"""
    Elabora un informe periodístico de fondo y análisis de prospectiva a partir de esta cobertura:
    - Categoría: {categoria}
    - Titular original: {entry.get('title', '')}
    - Enlace: {entry.get('link', '')}
    - Datos brutos: {entry.get('summary', '')}
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
        print(f"[!] Error al procesar en Gemini: {e}")
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
        metrics_block = "> ### Métricas y Cifras Clave\n" + "\n".join([f"> * **{m}**" for m in metrics_list]) + "\n\n"

    impacto_bloque = data.get("global_impact", "Este acontecimiento condicionará el equilibrio de intereses a nivel internacional.")

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

### Metodología y Contraste de Información
* **Fuente Primaria Monitoreada:** [{fuente_original}]({fuente_original})
* **Marco de Verificación:** {data.get('sources_summary', 'Datos contrastados mediante agregación de agencias internacionales bajo normas de neutralidad analítica.')}
"""

    with open(ruta_completa, "w", encoding="utf-8") as f:
        f.write(contenido_md)

    print(f"[+] Reporte de fondo generado: {nombre_archivo}")
    return post_slug

def ejecutar_pipeline():
    print("=== News Internacional TEP | Generación de Edición de Fondo ===")
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
                    print(f"[*] Analizando cobertura en {categoria}: {noticia_objetivo.get('title', '')[:50]}...")
                    resultado = procesar_noticia(noticia_objetivo, categoria)

                    if resultado:
                        post_slug = guardar_articulo(resultado, link)
                        historial.append(link)
                        guardar_historial(historial)
                        broadcast_telegram(resultado, post_slug)
                        nuevos_procesados += 1
                        # Procesar un reporte representativo por cada categoría
                        break
            except Exception as ex:
                print(f" [!] Error al consultar {url}: {ex}")

    print(f"=== Ciclo finalizado: {nuevos_procesados} nuevos reportes de fondo publicados ===")

if __name__ == "__main__":
    ejecutar_pipeline()