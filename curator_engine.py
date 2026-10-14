import os
import json
import html
import time
import random
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime
from slugify import slugify
import feedparser
from google import genai
from google.genai import types

# 1. Parámetros Operativos y Cascada de Modelos
client = genai.Client()

# Lista de modelos en orden de prioridad para evitar errores 404
MODELOS_CANDIDATOS = [
    "gemini-3.8-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
]

OUTPUT_DIR = os.path.join("src", "content", "blog")
HISTORY_FILE = "history.json"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8637388923:AAHl2omIwOIV5dd6uOd_Ho3stAsSMXTNMTY")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "-1004371603591")
SITE_BASE_URL = "https://newsinternacionaltep.com"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# 2. Malla de Fuentes Estratégicas Verificadas
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

# 3. Directriz Editorial basada en el Manual de Estándares y la Rúbrica de Evaluación
SYSTEM_INSTRUCTION = """Actúa como el Editor en Jefe y Analista Senior de un Instituto de Prospectiva e Inteligencia Estratégica (estándar MIT, Harvard y Foreign Affairs).
Tu objetivo es transformar el cable informativo crudo en un Reporte de Investigación Científica y Análisis Estructural que supere los 65/70 puntos de la Rúbrica Editorial.

ESTRICTO PROTOCOLO EDITORIAL (MANUAL DE ESTÁNDARES Y RÚBRICA):
1. TONO Y RIGOR: Autoritativo, neutral, analítico y basado en evidencia empírica. Cero sensacionalismo, cero clickbait.
2. ARQUITECTURA DE CONTENIDO (EMBUDO INVERTIDO):
   El cuerpo ('content') debe usar Markdown y estructurarse obligatoriamente con estos encabezados H2:
   - ## 1. Contexto Estratégico y Planteamiento del Problema (Lede & Nut Graph): Párrafo 1 con un dato contundente o paradoja central. Párrafos 2-3 con la justificación de por qué importa AHORA y la tesis central.
   - ## 2. Estado del Arte y Dinámica Estructural (Background): Recorrido contextual que expone los enfoques tradicionales y por qué están bajo tensión.
   - ## 3. Mecanismos Operativos y Núcleo Técnico (The Science): Desglose técnico y causal profundo. OBLIGATORIO: Incluir una tabla comparativa en formato Markdown (| Variable | Parámetro Base | Proyección de Impacto |) que sintetice las variables numéricas.
   - ## 4. Análisis de Impacto Sistémico, Riesgos y Limitaciones: Consecuencias tangibles en costos, mercados o regulación. Mencionar explícitamente las limitaciones del modelo, sesgos o márgenes de error.
   - ## 5. Visión Prospectiva y Escenarios Globales (12-24 Meses): Proyección de escenarios de equilibrio o ruptura futura, junto a preguntas críticas abiertas.
3. CITAS A VOCES EXPERTAS: Incluye al menos dos blockquotes ('> ') atribuidos a expertos con su cargo e institución académica/corporativa formal.
4. METADATOS Y ESPECIFICACIONES SEO:
   - "title": Titular conciso y riguroso. Máximo 60 caracteres.
   - "description": Abstract ejecutivo técnico. Máximo 155 caracteres.
   - "category": 'Tecnología', 'Economía' o 'Geopolítica'.
   - "tags": Lista de 3 a 5 palabras clave de la disciplina.
   - "author": 'Comité Analítico TEP & Prospectiva'.
   - "metrics": Lista con 3 parámetros cuantitativos clave."""

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
    category = html.escape(data.get("category", "Investigación"))
    title = html.escape(data.get("title", ""))
    description = html.escape(data.get("description", ""))

    raw_tags = data.get("tags", [])
    hashtags = " ".join([f"#{slugify(t, separator='')}" for t in raw_tags]) if raw_tags else ""

    message = (
        f"🔬 <b>DOSSIER ARBITRADO | {category.upper()}</b>\n\n"
        f"<b>{title}</b>\n\n"
        f"<i>{description}</i>\n\n"
        f"📑 <a href='{article_url}'>Acceder a la Investigación Completa & Tablas</a>\n\n"
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
        with urllib.request.urlopen(req, timeout=12) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            if res_data.get("ok"):
                print(" [✓] Despacho transmitido exitosamente a Telegram.")
    except Exception as e:
        print(f" [!] Advertencia Telegram: {e}")

def procesar_noticia_con_reintentos(entry, categoria: str):
    prompt = f"""
    Aplica el Manual de Estándares Editoriales y la Rúbrica Científica para generar un Paper de Investigación de Alto Impacto:
    - Dominio Disciplinar: {categoria}
    - Cable Base: {entry.get('title', '')}
    - Localizador de Fuente: {entry.get('link', '')}
    - Contexto Primario: {entry.get('summary', '')}
    """

    # Probar cascada de modelos en orden
    for modelo in MODELOS_CANDIDATOS:
        for intento in range(1, 3):
            try:
                response = client.models.generate_content(
                    model=modelo,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        response_mime_type="application/json",
                        temperature=0.2,
                    ),
                )
                return json.loads(response.text)
            except Exception as e:
                err_str = str(e)
                # Si es 404 NOT_FOUND, no reintentar en este modelo: pasar al siguiente inmediatamente
                if "404" in err_str or "NOT_FOUND" in err_str or "no longer available" in err_str:
                    print(f" [!] Modelo {modelo} no disponible (404). Cascando al siguiente modelo...")
                    break
                print(f" [!] Intento {intento} fallido en {modelo} ({e}).")
                if intento < 2:
                    time.sleep(3)

    return None

def guardar_paper(data: dict, fuente_original: str) -> str:
    slug = slugify(data["title"][:55])
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    post_slug = f"{fecha_actual}-{slug}"
    nombre_archivo = f"{post_slug}.md"
    ruta_completa = os.path.join(OUTPUT_DIR, nombre_archivo)

    tags_formateados = json.dumps(data.get("tags", ["Análisis", "Estrategia"]))
    categoria = data.get("category", "Geopolítica")

    # Generación de Imagen Fotorrealista Única sin Texto
    safe_concept = data["title"][:75].replace('"', '').replace("'", "")
    seed = random.randint(100000, 999999)
    prompt_img = urllib.parse.quote(f"Professional editorial photojournalism, cinematic documentary shot, 8k, sharp focus, neutral tone, no text, no words, no letters. Subject: {safe_concept}")
    imagen_hero = f"https://image.pollinations.ai/prompt/{prompt_img}?seed={seed}&width=1200&height=630&nologo=true"

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
* **Documento Base de Rastreo:** [{fuente_original}]({fuente_original})
* **Marco de Arbitraje:** Evaluación documental estructurada bajo los estándares de investigación editorial de News Internacional TEP.
"""

    with open(ruta_completa, "w", encoding="utf-8") as f:
        f.write(contenido_md)

    print(f"[+] Paper arbitrado registrado: {nombre_archivo}")
    return post_slug

def ejecutar_pipeline():
    print("=== MOTOR EDITORIAL CIENTÍFICO TEP: Protocolo MIT/Harvard ===")
    historial = cargar_historial()
    nuevos_procesados = 0

    for categoria, urls in FEEDS.items():
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
                    print(f"[*] Analizando suceso [{categoria}]: {noticia_objetivo.get('title', '')[:55]}...")
                    resultado = procesar_noticia_con_reintentos(noticia_objetivo, categoria)

                    if resultado:
                        post_slug = guardar_paper(resultado, link)
                        historial.append(link)
                        guardar_historial(historial)
                        broadcast_telegram(resultado, post_slug)
                        nuevos_procesados += 1
                        break
            except Exception as ex:
                print(f" [!] Excepción de red en {url}: {ex}")

    print(f"=== Ciclo Concluido: {nuevos_procesados} Nuevas Investigaciones Publicadas ===")

if __name__ == "__main__":
    ejecutar_pipeline()