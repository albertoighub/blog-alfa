import sqlite3
import feedparser
from datetime import datetime
import time
import os

# --- Configuración Global ---
DB_PATH = r"C:\Users\Andre\bionic_memory.db"
WORKSPACE_DIR = r"C:\Users\Andre\.lmstudio\apps\bionic\projects\d49037d8-47f4-5808-9028-c707de117f8f\workspace"

# Fuentes de alto impacto (RSS/API endpoints simulados para demostración)
# NOTA: En producción, estas URLs serían reemplazadas por scraping avanzado con curl_cffi o playwright.
FEED_SOURCES = [
    {"name": "Reuters Global", "url": "http://rss.reuters.com/reuters/global"}, # Placeholder RSS for testing structure
    {"name": "AP News Tech", "url": "https://apnews.com/section/technology/feed.xml"}, # Real API example
    {"name": "Hacker News Top", "url": "https://news.ycombinator.com/rss"} # Real RSS example
]

def initialize_db():
    """Establece la conexión y asegura que la tabla de cola exista."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Verificación de existencia
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tep_news_queue';")
        if not cursor.fetchone():
            print("[INFO] La tabla 'tep_news_queue' no existe. Creándola...")
            cursor.execute('''
                CREATE TABLE tep_news_queue (
                    article_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    source_url TEXT UNIQUE NOT NULL,
                    category TEXT NOT NULL,
                    status TEXT DEFAULT 'PENDIENTE',
                    raw_content TEXT,
                    processed_content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')
        conn.commit()
        return conn
    except sqlite3.Error as e:
        print(f"[FATAL ERROR] Error al conectar o inicializar la DB: {e}")
        exit(1)

def harvest_and_insert():
    """Escanea feeds RSS y extrae artículos, insertándolos en la cola."""
    conn = initialize_db()
    cursor = conn.cursor()
    print("\n=========================================================")
    print("--- Iniciando Harvester Evasivo (Fase 1: Ingesta de Cables) ---")
    print("=========================================================")
    total_inserted = 0
    duplicates_skipped = 0

    for source in FEED_SOURCES:
        source_name = source['name']
        feed_url = source['url']
        print(f"\n[INFO] Procesando fuente: {source_name}")

        try:
            # Usamos feedparser para manejar RSS/Atom de manera estándar. 
            # Este es el proxy funcional inicial, reemplazable por curl_cffi en producción.
            feed = feedparser.parse(feed_url)
            articles = feed.entries if hasattr(feed, 'entries') else []

            if not articles:
                print(f"[WARNING] No se encontraron artículos o el feed no pudo ser parseado para {source_name}.")
                continue

            for entry in articles:
                title = entry.get('title', 'No Title Provided')
                link = entry.get('link', '')
                summary = entry.get('summary') or entry.get('description') or ''
                category = source_name.split()[0].lower() # Categorización simple

                # Limpieza y preparación del contenido crudo (simulando trafilatura/limpieza inicial)
                raw_content = summary if summary else f"Content not available for {title}"
                
                print(f"  -> Descubierto: '{title[:60]}...'")

                try:
                    # INSERT OR IGNORE asegura que no se inserten duplicados basados en source_url.
                    cursor.execute('''
                        INSERT OR IGNORE INTO tep_news_queue (title, source_url, category, raw_content) 
                        VALUES (?, ?, ?, ?)
                    ''', (title, link, category, raw_content))

                    if cursor.rowcount > 0:
                        total_inserted += 1
                        print(f"    [SUCCESS] Insertado en cola con estado 'PENDIENTE'.")
                    else:
                        duplicates_skipped += 1
                        # Esto ocurre si la source_url ya existe (duplicado)
                        pass

                except sqlite3.Error as e:
                    print(f"    [ERROR SQL CRÍTICO] Fallo al insertar el artículo '{title}': {e}")

        except Exception as e:
            print(f"[CRITICAL ERROR DE RED/PARSE] No se pudo acceder o parsear la fuente {source_name}: {e}")
            # En un entorno real, aquí se implementaría reintento con backoff.

    conn.commit()
    conn.close()
    print("\n=========================================================")
    print("--- Harvester Finalizado ---")
    print(f"Total de artículos insertados en 'tep_news_queue': {total_inserted}")
    print(f"Artículos duplicados ignorados: {duplicates_skipped}")
    print("=========================================================")


if __name__ == "__main__":
    harvest_and_insert()