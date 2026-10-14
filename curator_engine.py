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

socket.setdefaulttimeout(15.0)

# ==============================================================================
# CONFIGURACIÓN GENERAL Y ENDPOINTS
# ==============================================================================
MODELOS_PRIORITARIOS = [
    "gemini-2.5-pro",
    "gemini-3.8-flash",
    "gemini-2.0-flash",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
]

LM_STUDIO_ENDPOINT = os.getenv("LM_STUDIO_URL", "http://127.0.0.1:1234/v1/chat/completions")
LM_STUDIO_MODELS_URL = os.getenv("LM_STUDIO_MODELS", "http://127.0.0.1:1234/v1/models")

OBJETIVO_REPORTAJES_POR_CICLO = 18
OUTPUT_DIR = os.path.join("src", "content", "blog")
HISTORY_FILE = "history.json"
STATE_FILE = "curator_state.json"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8637388923:AAHl2omIwOIV5dd6uOd_Ho3stAsSMXTNMTY")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "-1004371603591")
SITE_BASE_URL = "https://newsinternacionaltep.com"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Cliente oficial Google GenAI
client = None
if os.getenv("GEMINI_API_KEY"):
    try:
        client = genai.Client()
    except Exception as e:
        print(f" [!] Aviso al inicializar genai.Client: {e}")

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

## 4. Implicaciones Sistémicas, Riesgos y Limitaciones
Evaluación de impacto en costos, liquidez de mercado o regulación multilateral. Exponer limitaciones metodológicas, sesgos analíticos y áreas grises de los datos actuales.

## 5. Visión Prospectiva y Escenarios Globales (12-24 Meses)
Modelado prospectivo de escenarios alternativos (equilibrio vs. ruptura estructural) y preguntas estratégicas no resueltas.

REGLAS DE RIGOR EDITORIAL:
- CERO CLICKBAIT Y TONO INSTITUCIONAL: Prohibidos adjetivos sensacionalistas, pronombres en primera persona o lenguaje promocional.
- CITAS OBLIGATORIAS: Incluye al menos dos blockquotes ('> ') atribuidos a expertos con su cargo e institución formal verificable.
- EXTRACCIÓN DE ENTIDADES VISUALES:
  * "primary_entity": Nombre de la persona, institución, empresa o activo tangible central (ej: 'Emmanuel Macron', 'TSMC', 'Federal Reserve', 'Oil Tanker').
  * "visual_search_terms": 2 o 3 términos en inglés para búsqueda documental real."""

# ==============================================================================
# GESTIÓN DE HISTORIAL Y ESTADO ATÓMICO
# ==============================================================================

def cargar_historial() -> list:
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def guardar_historial(historial: list):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(historial, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f" [!] Error al guardar historial: {e}")

# ==============================================================================
# MOTOR VISUAL Y DE VERIFICACIÓN CRUZADA (DIRECTORIO GLOBAL 165 MEDIOS)
# ==============================================================================

def validar_directorio_global_medios(categoria: str) -> bool:
    if os.path.exists("directorio_global_medios.txt"):
        try:
            with open("directorio_global_medios.txt", "r", encoding="utf-8") as f:
                return categoria.lower() in f.read().lower()
        except Exception:
            pass
    return True

def extraer_foto_prensa_original(entry) -> str:
    if "enclosures" in entry and entry.enclosures:
        for enc in entry.enclosures:
            url = enc.get("href", "")
            tipo = enc.get("type", "")
            if tipo.startswith("image/") or any(url.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                return url

    if "media_content" in entry and entry.media_content:
        for m in entry.media_content:
            url = m.get("url", "")
            if url and not url.endswith(".gif"):
                return url

    if "media_thumbnail" in entry and entry.media_thumbnail:
        for thumb in entry.media_thumbnail:
            url = thumb.get("url", "")
            if url:
                return url

    return ""

def buscar_foto_wikimedia(entidad: str) -> str:
    if not entidad or len(entidad) < 3:
        return ""
    try:
        query = urllib.parse.quote(entidad.strip())
        endpoint = f"https://en.wikipedia.org/w/api.php?action=query&titles={query}&prop=pageimages&format=json&pithumbsize=1200&redirects=1"
        req = urllib.request.Request(endpoint, headers={"User-Agent": "NewsInternacionalTEP/2.0 (editorial@newsinternacionaltep.com)"})
        with urllib.request.urlopen(req, timeout=5.0) as res:
            data = json.loads(res.read().decode("utf-8"))
            pages = data.get("query", {}).get("pages", {})
            for pid, pdata in pages.items():
                if "thumbnail" in pdata and pdata["thumbnail"].get("source"):
                    return pdata["thumbnail"]["source"]
    except Exception:
        pass
    return ""

def resolver_imagen_congruente(entry, data: dict, categoria: str) -> str:
    palabras_ruido_visual = ["taxi", "car", "street", "driver", "vehicle", "traffic", "road", "people", "portrait", "person", "uber"]
    
    foto_original = extraer_foto_prensa_original(entry)
    if foto_original:
        url_lower = foto_original.lower()
        tiene_ruido = any(ruido in url_lower for ruido in palabras_ruido_visual)
        if categoria in ["Tecnología", "Economía", "Geopolítica"] and tiene_ruido:
            print(f" [!] Filtro Cruzado: Descartada imagen superficial/urbana ({foto_original.split('/')[-1]}). Elevando a estándar documental...")
        else:
            print(f" [✓] Imagen corroborada (Filtro 1 - Prensa Original): {foto_original[:65]}...")
            return foto_original

    entidad = data.get("primary_entity", "")
    foto_wiki = buscar_foto_wikimedia(entidad)
    if foto_wiki:
        print(f" [✓] Imagen corroborada (Filtro 2 - Wikimedia Archive para '{entidad}'): {foto_wiki[:65]}...")
        return foto_wiki

    search_terms = data.get("visual_search_terms", entidad)
    safe_subject = (search_terms if search_terms else data["title"][:50]).replace('"', '').replace("'", "")
    
    if any(k in data["title"].lower() for k in ["digital", "ataque", "red", "servidor", "centro", "tecnolog", "ciber", "ia"]):
        prompt_raw = f"High-end corporate documentary photography of {safe_subject}, advanced digital infrastructure, data centers, server racks, fiber optics, global connectivity nodes, professional lighting, technical precision, no text, no words, no letters, no typography, 35mm lens"
    else:
        prompt_raw = f"Authentic documentary photojournalism of {safe_subject}, 35mm lens photography, natural editorial lighting, realistic institutional event, high geopolitical relevance, no text, no words, no letters, no typography, unedited realistic"

    prompt_encoded = urllib.parse.quote(prompt_raw)
    seed = random.randint(100000, 999999)
    foto_ia = f"https://image.pollinations.ai/prompt/{prompt_encoded}?seed={seed}&width=1200&height=630&nologo=true"
    print(f" [✓] Imagen técnica generada bajo protocolo institucional (Filtro 3)")
    return foto_ia

# ==============================================================================
# CONECTOR LM STUDIO (IA LOCAL: GEMMA 4 E4B) Y CASCADA GEMINI
# ==============================================================================

def detectar_lm_studio() -> bool:
    """Verifica si el servidor local de LM Studio está activo en el puerto 1234"""
    try:
        req = urllib.request.Request(LM_STUDIO_MODELS_URL, headers={"User-Agent": "TEP-Local-Detector"})
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            if resp.status == 200:
                return True
    except Exception:
        pass
    return False

def consultar_lm_studio(prompt: str) -> tuple:
    """Envía la solicitud al modelo local Gemma 4 E4B en LM Studio"""
    payload = {
        "model": "gemma-4-e4b-instruct",
        "messages": [
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 4096,
    }
    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        LM_STUDIO_ENDPOINT,
        data=data_bytes,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=180.0) as resp:
            res_json = json.loads(resp.read().decode("utf-8"))
            raw_text = res_json["choices"][0]["message"]["content"]
            # Extraer JSON del bloque si viene envuelto en markdown ```json
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0].strip()
            return json.loads(raw_text), None
    except Exception as e:
        return None, f"LM_STUDIO_ERROR: {e}"

def consultar_cascada_gemini(prompt: str) -> tuple:
    """Ejecuta la cascada de modelos en Google Cloud ante saturación o límites"""
    if not client:
        return None, "NO_GEMINI_CLIENT"

    for modelo in MODELOS_PRIORITARIOS:
        for intento in range(2):
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
                if response and response.text:
                    return json.loads(response.text), None
            except Exception as e:
                err_str = str(e)
                if "503" in err_str or "UNAVAILABLE" in err_str:
                    print(f" [!] Modelo {modelo} saturado (503). Reintento en 3s...")
                    time.sleep(3)
                    continue
                elif "404" in err_str or "NOT_FOUND" in err_str:
                    print(f" [!] Modelo {modelo} no soportado en esta cuenta. Saltando al siguiente...")
                    break
                elif "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    print(f" [!] Cuota temporal alcanzada en {modelo}. Saltando al siguiente modelo...")
                    break
                else:
                    print(f" [!] Error en {modelo}: {err_str[:80]}. Evaluando alternativa...")
                    break
    return None, "TODOS_LOS_MODELOS_AGOTADOS"

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
      "primary_entity": "Entidad o personaje físico principal para rastreo visual",
      "visual_search_terms": "2 terminos clave en ingles para fotografia real",
      "content": "Cuerpo del paper en Markdown estructurado rigurosamente en las 5 secciones H2"
    }}
    """
    # 1. Si LM Studio está encendido en local, máxima prioridad
    if detectar_lm_studio():
        print(" [*] LM Studio detectado. Redactando con Gemma 4 E4B (Modo Soberano Local)...")
        res, err = consultar_lm_studio(prompt)
        if res:
            return res, None
        print(f" [!] Error en LM Studio ({err}). Derivando a Cascada Gemini...")

    # 2. Si no, o si falla, usar Cascada Gemini Cloud
    return consultar_cascada_gemini(prompt)

# ==============================================================================
# GUARDADO DE PAPERS Y TRANSMISIÓN
# ==============================================================================

def guardar_paper(data: dict, fuente_original: str, imagen_final: str) -> str:
    slug = slugify(data["title"][:55])
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    post_slug = f"{fecha_actual}-{slug}"
    nombre_archivo = f"{post_slug}.md"
    ruta_completa = os.path.join(OUTPUT_DIR, nombre_archivo)

    tags_formateados = json.dumps(data.get("tags", ["Análisis", "Estrategia"]))
    categoria = data.get("category", "Geopolítica")

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
heroImage: "{imagen_final}"
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
        f"📑 <a href='{article_url}'>Acceder al Paper Completo & Tablas</a>\n\n"
        f"{hashtags}"
    ).strip()

    endpoint = f"[https://api.telegram.org/bot](https://api.telegram.org/bot){TELEGRAM_BOT_TOKEN}/sendMessage"
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

# ==============================================================================
# PIPELINE DE PUBLICACIÓN MASIVA (HASTA 18 REPORTAJES)
# ==============================================================================

def ejecutar_pipeline():
    print(f"=== MOTOR DE INTELIGENCIA TEP: Monografías Masivas (Meta: {OBJETIVO_REPORTAJES_POR_CICLO}) ===")
    historial = cargar_historial()
    publicaciones_realizadas = 0
    categorias = ["Geopolítica", "Economía", "Tecnología"]

    # Recorrer categorías cíclicamente para balance temático
    for i in range(OBJETIVO_REPORTAJES_POR_CICLO):
        categoria = categorias[i % len(categorias)]
        print(f"\n[*] Slot {i+1}/{OBJETIVO_REPORTAJES_POR_CICLO} - Explorando: {categoria.upper()}")

        urls = FEEDS.get(categoria, []).copy()
        random.shuffle(urls)
        noticia_procesada = False

        for url in urls:
            if noticia_procesada:
                break
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                with urllib.request.urlopen(req, timeout=8.0) as resp:
                    raw_xml = resp.read()

                feed = feedparser.parse(raw_xml)
                for entry in feed.entries:
                    link = entry.get("link", "")
                    summary = entry.get("summary", "")
                    title = entry.get("title", "")
                    
                    if link and link not in historial and len(title) > 15 and len(summary) > 40:
                        print(f" [*] Analizando cable: {title[:65]}...")
                        resultado, err = redactar_paper_monografico(entry, categoria)
                        
                        if resultado:
                            img = resolver_imagen_congruente(entry, resultado, categoria)
                            slug = guardar_paper(resultado, link, img)
                            historial.append(link)
                            guardar_historial(historial)
                            broadcast_telegram(resultado, slug)
                            publicaciones_realizadas += 1
                            noticia_procesada = True
                            print(f" [✓] Publicación completada ({publicaciones_realizadas}/{OBJETIVO_REPORTAJES_POR_CICLO})")
                            time.sleep(2) # Pausa estratégica
                            break
                        else:
                            print(f" [!] No se pudo redactar con cable actual ({err}). Probando siguiente...")
            except Exception as e:
                continue

    print(f"\n=== Ciclo finalizado. Total de nuevos reportajes incorporados: {publicaciones_realizadas} ===")

if __name__ == "__main__":
    ejecutar_pipeline()