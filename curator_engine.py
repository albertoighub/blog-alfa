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

# 1. Configuración de API y Telegram
client = genai.Client()
MODELO = "gemini-3.5-flash-lite"
OUTPUT_DIR = os.path.join("src", "content", "blog")
HISTORY_FILE = "history.json"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8637388923:AAHl2omIwOIV5dd6uOd_Ho3stAsSMXTNMTY")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "-1004371603591")
SITE_BASE_URL = "https://newsinternacionaltep.com"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# 2. Fuentes periodísticas multi-agencia clasificadas
FEEDS = {
    "Tecnología": [
        "https://techcrunch.com/feed/",
        "https://www.theverge.com/rss/index.xml",
        "https://feeds.arstechnica.com/arstechnica/index",
    ],
    "Economía": [
        "https://feeds.content.dowjones.io/public/rss/mw_topstories",
        "https://search.cnbc.com/rs/search/view.html?partnerId=2000&keywords=economy&sort=date&type=rss",
        "https://finance.yahoo.com/news/rssindex",
    ],
    "Geopolítica": [
        "https://rss.politico.com/politics-news.xml",
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://thehill.com/feed/",
    ],
}

# Imágenes editoriales contextuales de alta resolución
IMAGENES_EDITORIALES = {
    "Tecnología": [
        "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?auto=format&fit=crop&w=1200&q=80",
    ],
    "Economía": [
        "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=1200&q=80",
    ],
    "Geopolítica": [
        "https://images.unsplash.com/photo-1541872703-74c5e44368f9?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1577495508048-b635879837f1?auto=format&fit=crop&w=1200&q=80",
    ],
}

# 3. Directriz editorial estilo New York Times / Bloomberg
SYSTEM_INSTRUCTION = """Eres el analista jefe y corresponsal internacional para 'News Internacional TEP'.
Tu cometido es transformar una noticia en un informe periodístico de fondo, riguroso, cuantitativo y con visión prospectiva.

Pautas analíticas indispensables:
1. Rigor estructural: No resumas simplemente. Analiza el trasfondo estructural, las causas de raíz y las posturas contrapuestas de los actores involucrados.
2. Datos y Métricas: Extrae o contextualiza cifras cuantitativas duras (porcentajes, montos, plazos, volúmenes de mercado o impacto demográfico).
3. Prospectiva e Impacto Global: Reflexiona sobre qué implicaciones tendrá este suceso en los equilibrios de poder internacional, la estabilidad económica y la vida cotidiana en el medio plazo.
4. Tono: Periodismo de alta escuela, imparcial, preciso y sin sesgos emocionales.

Devuelve ÚNICAMENTE un objeto JSON válido con las siguientes claves:
- "title": Titular periodístico formal y contundente (estilo NYT).
- "description": Subtítulo analítico (máximo 160 caracteres).
- "category": La categoría correspondiente ('Tecnología', 'Economía' o 'Geopolítica').
- "tags": Lista de 3 a 5 términos clave.
- "key_metrics": Lista con 2 a 3 viñetas breves conteniendo datos cuantitativos clave.
- "content": Cuerpo completo del informe redactado en Markdown (emplea subtítulos ## y párrafos desarrollados).
- "global_impact": Dos párrafos redactados analizando las consecuencias sistémicas globales.
- "sources_summary": Párrafo sintetizando el contraste de posturas y fuentes consultadas."""

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
        f"🔗 <a href='{article_url}'>Leer informe analítico y prospectiva</a>\n\n"
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
                print(" [✓] Noticia difundida en Telegram.")
    except Exception as e:
        print(f" [!] Error en Telegram: {e}")

def procesar_noticia(entry, categoria: str):
    prompt = f"""
    Genera un informe periodístico y prospectivo con base en esta noticia:
    - Categoría base: {categoria}
    - Titular original: {entry.get('title', '')}
    - Enlace: {entry.get('link', '')}
    - Información base: {entry.get('summary', '')}
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
    categoria = data.get("category", "Tecnología")
    lista_imagenes = IMAGENES_EDITORIALES.get(categoria, IMAGENES_EDITORIALES["Tecnología"])
    imagen_hero = random.choice(lista_imagenes)

    metrics_list = data.get("key_metrics", [])
    metrics_block = ""
    if metrics_list:
        metrics_block = "> ### Métricas y Cifras Clave\n" + "\n".join([f"> * **{m}**" for m in metrics_list]) + "\n\n"

    impacto_bloque = data.get("global_impact", "El acontecimiento marca una pauta analítica a seguir en las próximas semanas.")

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
* **Fuente de Referencia:** [{fuente_original}]({fuente_original})
* **Marco de Verificación:** {data.get('sources_summary', 'Datos sintetizados y contrastados con estándares de neutralidad periodística.')}
"""

    with open(ruta_completa, "w", encoding="utf-8") as f:
        f.write(contenido_md)

    print(f"[+] Informe periodístico generado: {nombre_archivo}")
    return post_slug

def ejecutar_pipeline():
    print("=== Motor Periodístico TEP: Análisis Multi-Fuente y Prospectiva ===")
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
                        break
            except Exception as ex:
                print(f" [!] Error en feed {url}: {ex}")

    print(f"=== Ciclo finalizado: {nuevos_procesados} nuevos informes publicados ===")

if __name__ == "__main__":
    ejecutar_pipeline()
