import os
import json
from datetime import datetime
from slugify import slugify
import feedparser
from google import genai
from google.genai import types

# 1. Configuración de API y almacenamiento
client = genai.Client()
MODELO = "gemini-3.5-flash-lite"
OUTPUT_DIR = os.path.join("src", "content", "blog")
HISTORY_FILE = "history.json"

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

def guardar_articulo(data: dict, fuente_original: str):
    """Genera el archivo .md compatible con las colecciones de contenido de Astro."""
    slug = slugify(data["title"][:50])
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    nombre_archivo = f"{fecha_actual}-{slug}.md"
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

def ejecutar_pipeline():
    """Ejecuta la curaduría evitando duplicados históricos."""
    print("=== Iniciando Pipeline de Noticias TEP con Antiduplicados ===")
    historial = cargar_historial()
    nuevos_procesados = 0

    for categoria, urls in FEEDS.items():
        for url in urls:
            print(f"[*] Revisando feed de {categoria}...")
            feed = feedparser.parse(url)

            # Buscar la primera noticia no procesada en el feed
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
                    guardar_articulo(resultado, link)
                    historial.append(link)
                    guardar_historial(historial)
                    nuevos_procesados += 1
            else:
                print(f" [=] No hay noticias nuevas en {categoria} (todas procesadas).")

    print(f"=== Pipeline finalizado: {nuevos_procesados} artículos nuevos añadidos ===")

if __name__ == "__main__":
    ejecutar_pipeline()