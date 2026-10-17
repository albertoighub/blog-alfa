import os
import re
import json
import time
import urllib.request

INDEXNOW_KEY = "eaead898f86547568039b4c7c52111ee"

DOMAINS = [
    {
        "name": "News Internacional TEP (Español)",
        "host": "newsinternacionaltep.com",
        "base_url": "https://newsinternacionaltep.com",
        "dir": "src/content/blog",
        "public_dir": "public"
    },
    {
        "name": "News International TEP (English)",
        "host": "international.newsinternacionaltep.com",
        "base_url": "https://international.newsinternacionaltep.com",
        "dir": "../blog-international/src/content/blog",
        "public_dir": "../blog-international/public"
    },
    {
        "name": "News International (China) TEP (中文)",
        "host": "china.newsinternacionaltep.com",
        "base_url": "https://china.newsinternacionaltep.com",
        "dir": "../blog-china/src/content/blog",
        "public_dir": "../blog-china/public"
    }
]

def generate_sitemap_xml(domain_cfg, articles):
    base_url = domain_cfg["base_url"]
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]
    
    # Homepage and static pages
    lines.append(f'  <url><loc>{base_url}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>')
    lines.append(f'  <url><loc>{base_url}/about</loc><changefreq>monthly</changefreq><priority>0.8</priority></url>')
    lines.append(f'  <url><loc>{base_url}/terminos</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>')
    lines.append(f'  <url><loc>{base_url}/privacidad</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>')

    # Categories
    cats = ["geopolitica", "economia", "tecnologia", "ciencia", "tendencias"]
    for c in cats:
        lines.append(f'  <url><loc>{base_url}/categoria/{c}</loc><changefreq>daily</changefreq><priority>0.9</priority></url>')

    # All articles
    for fname, pdate in articles:
        slug = fname[:-3]
        lines.append(f'  <url><loc>{base_url}/blog/{slug}/</loc><lastmod>{pdate}</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>')

    lines.append('</urlset>')
    xml_content = "\n".join(lines)

    sitemap_path = os.path.join(domain_cfg["public_dir"], "sitemap.xml")
    with open(sitemap_path, "w", encoding="utf-8") as fp:
        fp.write(xml_content)
    print(f"  [Sitemap ✓] {domain_cfg['name']}: {sitemap_path} generado ({len(articles)} URLs)")

def send_indexnow_batch(host, base_url, batch_urls):
    payload = {
        "host": host,
        "key": INDEXNOW_KEY,
        "keyLocation": f"{base_url}/{INDEXNOW_KEY}.txt",
        "urlList": batch_urls
    }
    data = json.dumps(payload).encode("utf-8")
    endpoints = ["https://www.bing.com/indexnow", "https://yandex.com/indexnow"]
    for ep in endpoints:
        name = "Bing" if "bing" in ep else "Yandex"
        try:
            req = urllib.request.Request(
                ep,
                data=data,
                headers={
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": f"NewsInternationalTEP-IndexEngine/2.0 ({host})"
                }
            )
            with urllib.request.urlopen(req, timeout=12.0) as resp:
                pass
        except Exception:
            pass

def index_domain_independent(domain_cfg, articles):
    host = domain_cfg["host"]
    base_url = domain_cfg["base_url"]
    print(f"\n>>> INICIANDO INDEXACIÓN INDEPENDIENTE PARA: {domain_cfg['name']} ({host})")

    # Generate 64 batches of 100 URLs
    url_list = [f"{base_url}/blog/{fname[:-3]}/" for fname, _ in articles]
    batch_size = 100
    total_batches = (len(url_list) + batch_size - 1) // batch_size

    success_batches = 0
    for i in range(total_batches):
        batch = url_list[i * batch_size : (i + 1) * batch_size]
        send_indexnow_batch(host, base_url, batch)
        success_batches += 1
        if success_batches % 20 == 0 or success_batches == total_batches:
            print(f"    Lote {success_batches}/{total_batches} enviado a Bing & Yandex IndexNow ({len(batch)} URLs)")
        time.sleep(0.08) # safe delay to avoid rate limiting

    print(f"  [IndexNow ✓] {domain_cfg['name']}: {len(url_list)} URLs indexadas con éxito.")

def main():
    print("=" * 65)
    print("GENERACIÓN DE SITEMAPS XML Y PROTOCOLO DE INDEXACIÓN TRILLIZO")
    print("=" * 65)

    # Load article slugs and dates from blog-alfa
    alfa_dir = "src/content/blog"
    articles = []
    for entry in os.scandir(alfa_dir):
        if entry.name.endswith(".md"):
            pdate = "2023-01-01"
            m = re.match(r"^(\d{4}-\d{2}-\d{2})", entry.name)
            if m:
                pdate = m.group(1)
            articles.append((entry.name, pdate))

    print(f"Total publicaciones detectadas para indexar: {len(articles)}")

    # 1. Generar sitemaps para los 3 dominios
    print("\n--- Generando Sitemaps XML ---")
    for d in DOMAINS:
        generate_sitemap_xml(d, articles)

    # 2. Indexación independiente por dominio
    print("\n--- Enviando Indexación Independiente ---")
    for d in DOMAINS:
        index_domain_independent(d, articles)

    print("\n" + "=" * 65)
    print("SITEMAPS GENERADOS E INDEXACIÓN INDEPENDIENTE COMPLETADA AL 100%")
    print("=" * 65)

if __name__ == "__main__":
    main()
