import os
import sys
import re
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

socket.setdefaulttimeout(12.0)

# ==============================================================================
# CONFIGURACIÓN SOBERANA TEP & LM STUDIO (PUERTO 1235)
# ==============================================================================
LM_STUDIO_BASE = os.getenv("LM_STUDIO_BASE", "http://127.0.0.1:1235/v1")
LM_STUDIO_MODELS_URL = f"{LM_STUDIO_BASE}/models"
LM_STUDIO_CHAT_URL = f"{LM_STUDIO_BASE}/chat/completions"

# 3 monografías por cada sección (3 Geopolítica, 3 Economía, 3 Tecnología = 9 en total)
OBJETIVO_POR_SECCION = 3 
OUTPUT_DIR = os.path.join("src", "content", "blog")
HISTORY_FILE = "history.json"
STATE_FILE = "curator_state.json"
INFOKEYS_FILE = "infokeys.txt"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8637388923:AAHl2omIwOIV5dd6uOd_Ho3stAsSMXTNMTY")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "-1004371603591")
SITE_BASE_URL = "https://newsinternacionaltep.com"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Feeds de respaldo directo por si algún dominio de infokeys no expone RSS público
FEEDS_RESPALDO = {
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
  * "visual_search_terms": 2 o 3 términos en ingles para fotografia real."""

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

# ==============================================================================
# MOTOR DE INGESTA DINÁMICA: INFOKEYS (CAPA 1 DE BÚSQUEDA)
# ==============================================================================

def cargar_infokeys_por_seccion() -> dict:
    """Extrae y clasifica los 300 dominios del archivo infokeys.txt por categoría"""
    directorios = {"Geopolítica": [], "Economía": [], "Tecnología": []}
    
    if not os.path.exists(INFOKEYS_FILE):
        print(f" [!] Archivo {INFOKEYS_FILE} no detectado. Utilizando catálogo base.")
        return FEEDS_RESPALDO

    seccion_actual = None
    url_regex = re.compile(r"https?://[^\s<>\"']+")

    with open(INFOKEYS_FILE, "r", encoding="utf-8", errors="ignore") as f:
        for linea in f:
            linea_str = linea.strip()
            linea_upper = linea_str.upper()
            
            if "SECCIÓN 1" in linea_upper or "POLÍTICA" in linea_upper or "GEOPOLÍTICA" in linea_upper:
                seccion_actual = "Geopolítica"
            elif "SECCIÓN 2" in linea_upper or "ECONOMÍA" in linea_upper or "MERCADOS" in linea_upper:
                seccion_actual = "Economía"
            elif "SECCIÓN 3" in linea_upper or "TECNOLOGÍA" in linea_upper or "COMPUTACIONAL" in linea_upper:
                seccion_actual = "Tecnología"

            if seccion_actual:
                coincidencias = url_regex.findall(linea_str)
                for u in coincidencias:
                    u_limpia = u.rstrip(".,;)")
                    if u_limpia not in directorios[seccion_actual]:
                        directorios[seccion_actual].append(u_limpia)

    return directorios

def autodescubrir_feed_rss(base_url: str) -> list:
    """Rastrea de forma acelerada canales RSS/Atom desde el dominio infokey"""
    rutas_comunes = ["/feed", "/rss", "/rss.xml", "/feed/", "/atom.xml", "/news/rss.xml"]
    
    # 1. Probar descubrimiento directo en HTML (link rel alternate)
    try:
        req = urllib.request.Request(base_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=3.5) as response:
            tipo_contenido = response.headers.get("Content-Type", "").lower()
            contenido = response.read(35000).decode("utf-8", errors="ignore")
            
            # Si el link ya era un XML directo
            if "xml" in tipo_contenido or "<rss" in contenido or "<feed" in contenido:
                return [base_url]
                
            enlaces_feed = re.findall(r'<link[^>]+type=["\']application/(?:rss|atom)\+xml["\'][^>]+href=["\']([^"\']+)["\']', contenido, re.IGNORECASE)
            if enlaces_feed:
                candidato = enlaces_feed[0]
                if candidato.startswith("/"):
                    return [urllib.parse.urljoin(base_url, candidato)]
                return [candidato]
    except Exception:
        pass

    # 2. Respaldo de rutas frecuentes rápidas
    dominio_base = base_url.rstrip("/")
    return [f"{dominio_base}{ruta}" for ruta in rutas_comunes[:2]]

# ==============================================================================
# DETECCIÓN DE LM STUDIO LOCAL (PUERTO 1235)
# ==============================================================================

def detectar_modelo_cargado_lm_studio() -> tuple:
    try:
        req = urllib.request.Request(LM_STUDIO_MODELS_URL, headers={"User-Agent": "TEP-Local-Curator"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            modelos = data.get("data", [])
            if modelos and len(modelos) > 0:
                return modelos[0].get("id", ""), None
            return None, "NO_MODELS_LOADED"
    except urllib.error.URLError as e:
        return None, f"CONEXION_RECHAZADA: Verifica que LM Studio esté activo en el puerto 1235. ({e.reason})"
    except Exception as e:
        return None, str(e)

# ==============================================================================
# GESTIÓN DE HISTORIAL ATÓMICO
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
# MOTOR VISUAL Y ARBITRAJE DE PRENSA (4 CAPAS)
# ==============================================================================

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
        with urllib.request.urlopen(req, timeout=4.0) as res:
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
            print(f" [!] Filtro Cruzado: Descartada imagen superficial ({foto_original.split('/')[-1]}). Elevando a estándar documental...")
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
    print(" [✓] Imagen técnica generada bajo protocolo institucional (Filtro 3)")
    return foto_ia

# ==============================================================================
# REDACCIÓN MEDIANTE GEMMA LOCAL (LM STUDIO)
# ==============================================================================

def redactar_paper_monografico(entry, categoria: str, modelo_activo_id: str):
    prompt = f"""
    Aplica el Manual de Estándares Editoriales y la Rúbrica MIT/Harvard para elaborar un Paper de Investigación exhaustivo:
    - Dominio Disciplinar: {categoria}
    - Cable Base: {entry.get('title', '')}
    - Localizador de Fuente: {entry.get('link', '')}
    - Contexto Primario: {entry.get('summary', '')}

    FORMATO JSON DE SALIDA OBLIGATORIO (DEVUELVE UNICAMENTE EL JSON VALIDO SIN TEXTO ADICIONAL):
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

    payload = {
        "model": modelo_activo_id,
        "messages": [
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 4096,
        "stream": False
    }

    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        LM_STUDIO_CHAT_URL,
        data=data_bytes,
        headers={"Content-Type": "application/json"}
    )

    print(f" [*] Gemma transformando cable en Dossier Monográfico (Modelo: {modelo_activo_id})...")
    try:
        with urllib.request.urlopen(req, timeout=300.0) as resp:
            res_json = json.loads(resp.read().decode("utf-8"))
            raw_text = res_json["choices"][0]["message"]["content"].strip()
            
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0].strip()

            return json.loads(raw_text), None
    except urllib.error.HTTPError as e:
        error_detalle = e.read().decode("utf-8", errors="ignore")
        return None, f"LM_STUDIO_HTTP_{e.code}: {error_detalle}"
    except Exception as e:
        return None, f"LM_STUDIO_LOCAL_ERROR: {e}"

# ==============================================================================
# ALMACENAMIENTO ATÓMICO Y DIFUSIÓN TELEGRAM
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

    print(f" [+] Paper monográfico archivado: {nombre_archivo}")
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

# ==============================================================================
# PIPELINE POR LOTES BALANCEADOS (3 POR SECCIÓN = 9 PAPERS)
# ==============================================================================

def ejecutar_pipeline():
    print("=== MOTOR SOBERANO TEP: Lote Ampliado (3 Papers por Sección con Capa InfoKeys) ===")
    
    modelo_activo_id, error_modelo = detectar_modelo_cargado_lm_studio()
    if error_modelo == "NO_MODELS_LOADED":
        print("\n[!] ALERTA: LM Studio está activo en el puerto 1235, pero NO tiene ningún modelo cargado en memoria.")
        print(" -> Abre LM Studio, entra a 'Instancias cargadas', selecciona Gemma 4 E4B y presiona 'Cargar modelo'.")
        return
    elif error_modelo:
        print(f"\n[!] Error al conectar con LM Studio: {error_modelo}")
        return

    print(f"[✓] Núcleo analítico verificado: {modelo_activo_id}")

    historial = cargar_historial()
    catalogo_infokeys = cargar_infokeys_por_seccion()
    categorias = ["Geopolítica", "Economía", "Tecnología"]
    total_publicaciones = 0

    for categoria in categorias:
        print(f"\n=======================================================")
        print(f"[*] INICIANDO SECCIÓN: {categoria.upper()} (Meta: {OBJETIVO_POR_SECCION} papers)")
        print(f"=======================================================")
        
        publicados_seccion = 0
        dominios_infokeys = catalogo_infokeys.get(categoria, []).copy()
        random.shuffle(dominios_infokeys)
        
        # Combinar dominios de InfoKeys con feeds verificados de respaldo
        fuentes_de_rastreo = dominios_infokeys + FEEDS_RESPALDO.get(categoria, [])

        for fuente in fuentes_de_rastreo:
            if publicados_seccion >= OBJETIVO_POR_SECCION:
                break

            # Determinar feeds candidatos desde el enlace de infokeys
            if fuente.startswith("http") and ("xml" in fuente or "rss" in fuente or "feed" in fuente):
                candidatos_feeds = [fuente]
            else:
                candidatos_feeds = autodescubrir_feed_rss(fuente)

            for url_feed in candidatos_feeds:
                if publicados_seccion >= OBJETIVO_POR_SECCION:
                    break
                try:
                    req = urllib.request.Request(url_feed, headers={"User-Agent": USER_AGENT})
                    with urllib.request.urlopen(req, timeout=5.0) as resp:
                        raw_data = resp.read()

                    feed = feedparser.parse(raw_data)
                    for entry in feed.entries:
                        if publicados_seccion >= OBJETIVO_POR_SECCION:
                            break
                        link = entry.get("link", "")
                        summary = entry.get("summary", "")
                        title = entry.get("title", "")
                        
                        # Filtro de pertinencia y densidad informativa
                        if link and link not in historial and len(title) > 18 and len(summary) > 40:
                            print(f"\n  [*] [{categoria} {publicados_seccion+1}/{OBJETIVO_POR_SECCION}] Cable capturado: {title[:65]}...")
                            resultado, err = redactar_paper_monografico(entry, categoria, modelo_activo_id)
                            
                            if resultado:
                                img = resolver_imagen_congruente(entry, resultado, categoria)
                                slug = guardar_paper(resultado, link, img)
                                historial.append(link)
                                guardar_historial(historial)
                                broadcast_telegram(resultado, slug)
                                publicados_seccion += 1
                                total_publicaciones += 1
                                print(f"  [✓] Paper {publicados_seccion}/{OBJETIVO_POR_SECCION} archivado y emitido.")
                                time.sleep(1.5)
                            else:
                                print(f"  [!] Descarte por fallo en transformación: {err}")
                except Exception:
                    continue

        print(f"[*] Resumen Sección {categoria}: {publicados_seccion}/{OBJETIVO_POR_SECCION} completados.")

    print(f"\n=======================================================")
    print(f"[✓] Ciclo concluido. Total de reportes incorporados: {total_publicaciones}/9")
    print(f"=======================================================")

if __name__ == "__main__":
    ejecutar_pipeline()