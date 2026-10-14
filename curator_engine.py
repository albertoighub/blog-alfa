import os
import sys
import json
import html
import time
import random
import socket
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime
from slugify import slugify
import feedparser
from google import genai
from google.genai import types

# 1. Parámetros de Red y Entorno
socket.setdefaulttimeout(8.0)
client = genai.Client()
MODELO_ACTIVO = "gemini-3.8-flash"
OUTPUT_DIR = os.path.join("src", "content", "blog")
HISTORY_FILE = "history.json"
STATE_FILE = "curator_state.json"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8637388923:AAHl2omIwOIV5dd6uOd_Ho3stAsSMXTNMTY")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "-1004371603591")
SITE_BASE_URL = "https://newsinternacionaltep.com"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# 2. Fuentes Estratégicas Verificadas
FEEDS = {
    "Geopolítica": [
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://rss.politico.com/politics-news.xml",
        "https://thehill.com/feed/",
        "https://www.aljazeera.com/xml/rss/all.xml",
        "https://www.theguardian.com/world/rss",
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

# 3. Directiva Editorial basada en Manual MIT/Harvard y Rúbrica
SYSTEM_INSTRUCTION = """Actúa como Editor en Jefe y Director de un Instituto de Inteligencia y Prospectiva Científica Internacional (estándar MIT, Harvard y Foreign Affairs).
Transforma el suceso noticioso en un Paper de Investigación y Dossier Analítico de máxima profundidad, densidad técnica y rigor metodológico, superando los 65/70 puntos de la Rúbrica de Evaluación Editorial.

ARQUITECTURA EXIGIDA (EMBUDO INVERTIDO COMPLEJO):
El cuerpo del documento ('content') debe escribirse en Markdown con las siguientes 5 secciones H2 obligatorias:

## 1. Contexto Estratégico y Planteamiento del Problema (Lede & Nut Graph)
Párrafo inicial con dato cuantitativo duro o paradoja sistémica. Párrafos 2 y 3 justificando por qué esta investigación es crítica en este momento y formulando la tesis central.

## 2. Estado del Arte y Dinámica Estructural (Background)
Evolución histórica y contextual del problema. Análisis crítico de los marcos operativos tradicionales y por qué están bajo estrés o agotamiento.

## 3. Mecanismos Operativos y Núcleo Técnico (The Science)
Desglose causal minucioso (arquitectura técnica, modelos económicos o balance táctico). 
OBLIGATORIO: Incluir una tabla comparativa Markdown exhaustiva con el siguiente formato:
| Variable de Análisis | Parámetro Histórico / Base | Magnitud / Proyección de Impacto | Mecanismo Causal |
| :--- | :--- | :--- | :--- |
(Mínimo 3 filas de datos contextualizados con cifras y márgenes analíticos).

## 4. Implicaciones Sistémicas, Riesgos y Limitaciones
Evaluación de impacto en costos, liquidez de mercado o regulación multilateral. Exponer limitaciones metodológicas, sesgos analíticos y áreas grises de los datos actuales.

## 5. Visión Prospectiva y Escenarios Globales (12-24 Meses)
Modelado prospectivo de escenarios alternativos (equilibrio vs. ruptura estructural) y preguntas estratégicas no resueltas.

REGLAS DE RIGOR EDITORIAL:
- CERO CLICKBAIT Y TONO INSTITUCIONAL: Prohibidos adjetivos sensacionalistas, pronombres en primera persona o lenguaje promocional.
- CITAS OBLIGATORIAS: Incluye al menos dos blockquotes ('> ') atribuidos a expertos con su cargo e institución formal verificable.
- PROMPT VISUAL DE ALTA FIDELIDAD: En 'image_prompt_en', redacta un prompt descriptivo en INGLÉS detallando una escena documental real, iluminación cinemática, ángulos y sujetos concretos relacionados con la noticia. Prohibido texto, marcas de agua o conceptos abstractos."""

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

def obtener_siguiente_categoria() -> str:
    categorias = ["Geopolítica", "Economía", "Tecnología"]
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                last_idx = data.get("last_index", -1)
                next_idx = (last_idx + 1) % len(categorias)
        except Exception:
            next_idx = 0
    else:
        next_idx = 0

    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"last_index": next_idx, "categoria": categorias[next_idx]}, f)

    return categorias[next_idx]

def broadcast_telegram(data: dict, post_slug: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL_ID:
        return

    article_url = f"{SITE_BASE_URL}/blog/{post_slug}/"
    category = html.escape(data.get("category", "Investigación"))
    title = html.escape(data.get("title", ""))
    description = html.escape(data.get("description", ""))

    raw_tags = data.get("tags", [])
    hashtags = " ".join([f"#{slugify(t, separator='')}" for t in raw_tags]) if raw_tags else ""

    message = (
        f"🔬 <b>DOSSIER ARBITRADO | {category.upper()}</b>\n\n"
        f"<b>{title}</b>\n\n"
        f"<i>{description}</i>\n\n"
        f"📑 <a href='{article_url}'>Acceder al Paper Completo & Métricas</a>\n\n"
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
        with urllib.request.urlopen(req, timeout=8) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            if res_data.get("ok"):
                print(" [✓] Transmisión exitosa a Telegram.")
    except Exception as e:
        print(f" [!] Aviso Telegram: {e}")

def redactar_paper_monografico(entry, categoria: str):
    prompt = f"""
    Aplica el Manual de Estándares Editoriales y la Rúbrica MIT/Harvard para elaborar un Paper de Investigación exhaustivo:
    - Dominio Disciplinar: {categoria}
    - Cable Base: {entry.get('title', '')}
    - Localizador de Fuente: {entry.get('link', '')}
    - Contexto Primario: {entry.get('summary', '')}

    FORMATO JSON DE SALIDA OBLIGATORIO:
    {{
      "title": "Titular analítico directo (máximo 60 caracteres)",
      "description": "Abstract académico ejecutivo (máximo 155 caracteres)",
      "category": "{categoria}",
      "tags": ["3 a 5 palabras clave de la disciplina"],
      "author": "Comité Analítico TEP & Prospectiva",
      "metrics": ["3 parámetros cuantitativos verificables"],
      "image_prompt_en": "Prompt fotorrealista en inglés (cámara, lentes, sujeto concreto, sin texto)",
      "content": "Cuerpo del paper en Markdown estructurado rigurosamente en las 5 secciones H2"
    }}
    """

    try:
        response = client.models.generate_content(
            model=MODELO_ACTIVO,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )
        return json.loads(response.text), None
    except Exception as e:
        err_msg = str(e)
        # Identificar cuota agotada
        if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
            return None, "QUOTA_EXCEEDED"
        return None, err_msg

def guardar_paper(data: dict, fuente_original: str) -> str:
    slug = slugify(data["title"][:55])
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    post_slug = f"{fecha_actual}-{slug}"
    nombre_archivo = f"{post_slug}.md"
    ruta_completa = os.path.join(OUTPUT_DIR, nombre_archivo)

    tags_formateados = json.dumps(data.get("tags", ["Análisis", "Estrategia"]))
    categoria = data.get("category", "Geopolítica")

    # Imagen Fotorrealista Contextual con Semilla Única
    image_prompt_raw = data.get("image_prompt_en", "")
    if not image_prompt_raw or len(image_prompt_raw) < 20:
        safe_subject = data["title"][:70].replace('"', '').replace("'", "")
        image_prompt_raw = f"Editorial documentary photojournalism, realistic lighting, authentic scene, no text, no letters. Subject: {safe_subject}"

    seed = random.randint(100000, 999999)
    prompt_encoded = urllib.parse.quote(f"{image_prompt_raw}, professional photojournalism, 8k resolution, neutral grading, no watermark, no text")
    imagen_hero = f"https://image.pollinations.ai/prompt/{prompt_encoded}?seed={seed}&width=1200&height=630&nologo=true"

    metrics_list = data.get("metrics", [])
    metrics_block = ""
    if metrics_list:
        metrics_block = "> ### Variables Clave y Parámetros Operativos\n" + "\n".join([f"> * **{m}**" for m in metrics_list]) + "\n\n"

    autor = data.get("author", "Comité Analítico TEP & Prospectiva")

    contenido_md = f"""---
title: "{data['title']}"
description: "{data['description']}"
pubDate: "{fecha_actual}"
category: "{categoria}"
tags: {tags_formateados}
author: "{autor}"
heroImage: "{imagen_hero}"
canonicalSource: "{fuente_original}"
---

{metrics_block}{data['content']}

---

### Trazabilidad Metodológica y Fuentes Primarias
* **Documentación Base de Rastreo:** [{fuente_original}]({fuente_original})
* **Marco de Arbitraje:** Evaluación documental estructurada bajo los estándares editoriales y de rigor científico de News Internacional TEP.
"""

    with open(ruta_completa, "w", encoding="utf-8") as f:
        f.write(contenido_md)

    print(f"[+] Paper monográfico archivado: {nombre_archivo}")
    return post_slug

def ejecutar_pipeline():
    print("=== MOTOR DE INTELIGENCIA TEP: Monografía Arbitrada (8 Ciclos Diarios) ===")
    historial = cargar_historial()
    categoria_turno = obtener_siguiente_categoria()
    print(f"[*] Turno de investigación programado: {categoria_turno.upper()}")

    urls = FEEDS.get(categoria_turno, FEEDS["Geopolítica"]).copy()
    random.shuffle(urls)

    for url in urls:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, timeout=6.0) as resp:
                raw_xml = resp.read()

            feed = feedparser.parse(raw_xml)
            noticia_candidata = None

            for entry in feed.entries:
                link = entry.get("link", "")
                summary = entry.get("summary", "")
                title = entry.get("title", "")
                if link and link not in historial and len(title) > 15 and len(summary) > 40:
                    noticia_candidata = entry
                    break

            if noticia_candidata:
                link = noticia_candidata.get("link", "")
                print(f"[*] Cable prioritario detectado: {noticia_candidata.get('title', '')[:60]}...")
                resultado, error_tipo = redactar_paper_monografico(noticia_candidata, categoria_turno)

                # CIRCUITO DE SEGURIDAD ANTE CUOTA 429: Abortar inmediatamente
                if error_tipo == "QUOTA_EXCEEDED":
                    print("\n[!] AVISO DE CONTROL: Cuota de peticiones temporalmente alcanzada en Google Gemini.")
                    print("[!] Deteniendo la ejecución para permitir que la cuota se restablezca de forma natural.")
                    return

                if resultado:
                    post_slug = guardar_paper(resultado, link)
                    historial.append(link)
                    guardar_historial(historial)
                    broadcast_telegram(resultado, post_slug)
                    print("=== Ciclo Exitoso: Publicación completada ===")
                    return
        except Exception:
            continue

    print(" [!] No se hallaron cables no procesados en este ciclo.")

if __name__ == "__main__":
    ejecutar_pipeline()