import urllib.request
import urllib.parse
import json
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

BOOSTER_QUERIES = {
    "Tendencias": [
        "broadcasting studio", "media conference", "music festival stage", "film festival red carpet",
        "cinema theater audience", "television interview", "radio station studio", "press conference journalist",
        "fashion show runway", "stadium crowd event", "convention hall exhibition", "comic con crowd",
        "esports gaming tournament", "streaming studio gaming", "podcast recording microphone",
        "digital audio workstation", "social gathering festival", "parade carnival celebration",
        "urban street photography", "modern city nightlife crowd", "art gallery modern exhibition",
        "contemporary museum installation", "photojournalist camera", "television cameras production",
        "video producer monitors", "sound engineering live event", "cultural festival performance",
        "creative agency office", "ted conference speaker", "keynote presentation audience",
        "film set camera crew", "broadcast studio lights", "multimedia production set",
        "documentary filmmaker camera", "music concert lighting stage", "digital art installation",
        "virtual reality exhibition", "tech conference audience", "dj mixing console crowd",
        "film premiere red carpet", "press photographers event", "rock festival stage crowd",
        "electronic music festival", "broadcast control room television", "news anchor desk studio"
    ],
    "Economía": [
        "stock trader floor", "securities exchange trading", "financial district skyscrapers",
        "central bank building", "container terminal shipping", "freight train transport",
        "oil platform offshore", "wind turbine generator", "solar energy plant",
        "automobile factory assembly", "manufacturing industrial robot", "commercial banking tower",
        "commodity trading floor", "cargo airplane freight", "modern farm combine",
        "mining haul truck", "liquified gas tanker", "steel production factory",
        "container ship harbor", "automated logistics warehouse", "financial analytics screens",
        "frankfurt financial center", "shanghai financial district", "london docklands canary wharf",
        "new york stock exchange", "tokyo exchange trading", "hong kong central skyline",
        "heavy industry manufacturing", "chemical processing refinery", "hydroelectric dam generator"
    ],
    "Ciencia": [
        "medical laboratory researcher", "biochemistry research assay", "dna sequencing machine",
        "pharmaceutical manufacturing", "surgical suite operating", "mri medical imaging",
        "virology laboratory hood", "astronomical observatory telescope", "particle physics detector",
        "cern large hadron collider", "hubble deep sky image", "james webb telescope deep field",
        "polar research station antarctica", "marine biology research ship", "scanning electron microscope image",
        "cell culture microbiology", "atacama large millimeter array", "mars surface curiosity rover",
        "international space station earth", "radiation therapy medical linear accelerator", "optics research laser",
        "analytical chemistry spectroscopy", "biotechnology cleanroom", "fossil excavation paleontology"
    ]
}

BLACK_LIST_WORDS = [
    "flag of", "coat of arms", "icon", "logo", "map of", "diagram", "chart of",
    "insignia", "emblem", "seal of", "currency sign", "symbol", "infographic",
    "drawing", "caricature", "sketch", "passport", "postage stamp", "coin of", ".pdf", ".djvu"
]

def fetch_wikimedia(cat, query, offset):
    url = f"https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch={urllib.parse.quote(query)}+filetype:bitmap&gsrnamespace=6&gsrlimit=50&gsroffset={offset}&prop=imageinfo&iiprop=url|size|mime&iiurlwidth=1280&format=json"
    req = urllib.request.Request(url, headers={"User-Agent": "NewsInternacionalTEP/1.0 (contact@newsinternacionaltep.com)"})
    results = []
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            pages = data.get("query", {}).get("pages", {})
            for p in pages.values():
                title = p.get("title", "").lower()
                if any(bad in title for bad in BLACK_LIST_WORDS):
                    continue
                ii = p.get("imageinfo", [{}])[0]
                mime = ii.get("mime", "")
                if mime not in ["image/jpeg", "image/jpg", "image/png", "image/webp"]:
                    continue
                width = ii.get("width", 0)
                if width < 800:
                    continue
                thumb = ii.get("thumburl", ii.get("url"))
                clean_url = thumb.split("?")[0]
                results.append(clean_url)
    except Exception:
        pass
    return cat, results

def main():
    pool_file = "unique_images_pool.json"
    with open(pool_file, "r", encoding="utf-8") as fp:
        category_images = json.load(fp)

    seen_all = set()
    for cat, urls in category_images.items():
        for u in urls:
            seen_all.add(u)

    print(f"Pool previo cargado: {len(seen_all)} imágenes únicas.")

    tasks = []
    for cat, queries in BOOSTER_QUERIES.items():
        for q in queries:
            for offset in [0, 50, 100, 150, 200, 250]:
                tasks.append((cat, q, offset))

    print(f"Total requests planificados para el booster: {len(tasks)}")
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=14) as executor:
        futures = [executor.submit(fetch_wikimedia, cat, q, offset) for (cat, q, offset) in tasks]
        done = 0
        added_count = 0
        for f in as_completed(futures):
            done += 1
            cat, urls = f.result()
            for u in urls:
                if u not in seen_all:
                    seen_all.add(u)
                    category_images[cat].append(u)
                    added_count += 1
            if done % 100 == 0 or done == len(tasks):
                print(f"  Progreso booster: {done}/{len(tasks)} requests | Añadidas: {added_count} nuevas | Total pool: {len(seen_all)}")

    print("\n" + "=" * 60)
    print(f"BOOSTER COMPLETADO EN {time.time() - start_time:.2f} SEGUNDOS")
    print(f"NUEVAS IMÁGENES AÑADIDAS: {added_count}")
    print(f"TOTAL IMÁGENES ÚNICAS GLOBALES: {len(seen_all)}")
    print("DESGLOSE POR CATEGORÍA:")
    for cat, imgs in category_images.items():
        print(f"  - {cat}: {len(imgs)} imágenes únicas")
    print("=" * 60)

    with open(pool_file, "w", encoding="utf-8") as fp:
        json.dump(category_images, fp, indent=2)
    print(f"Base de datos actualizada con éxito en: {pool_file}")

if __name__ == "__main__":
    main()
