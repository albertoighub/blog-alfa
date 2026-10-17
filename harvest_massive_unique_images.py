import urllib.request
import urllib.parse
import json
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

OPTIMIZED_QUERIES = {
    "Tecnología": [
        "supercomputer", "datacenter", "microprocessor", "semiconductor cleanroom",
        "silicon wafer", "robotics laboratory", "cybersecurity operations", "server room",
        "quantum computer", "quantum computing", "artificial intelligence", "neural network",
        "autonomous vehicle", "lidar sensor", "spacecraft assembly", "satellite cleanroom",
        "drones laboratory", "telecommunications tower", "motherboard electronics",
        "cloud computing servers", "humanoid robot", "integrated circuit", "fiber optic cable",
        "virtual reality headset", "microchip inspection", "server rack cooling",
        "hpc cluster", "electronic test equipment oscilloscope", "spacex falcon rocket",
        "spacex starship launch pad", "cleanroom technicians", "robotic arm assembly",
        "optical transceiver network", "biometric scanner", "5g base station",
        "printed circuit board", "electronic engineering laboratory", "nanotechnology chip",
        "data visualization command center", "high performance computing"
    ],
    "Tendencias": [
        "television studio", "podcast studio", "broadcast journalism", "esports tournament",
        "live streaming", "social media mobile", "digital cameras filming", "recording studio console",
        "press conference media", "video editing suite", "influencer", "concert crowd smartphone",
        "soundstage lighting", "newsroom broadcast", "multimedia journalism", "filmmaking camera",
        "digital creators", "mobile journalism", "radio broadcast microphone", "television cameras control room",
        "virtual reality gaming", "gaming headset esports", "acoustic foam microphone studio",
        "teleprompter broadcast", "mobile app demonstration", "content creator ring light",
        "audio mixer broadcast console", "camera crane television", "media interview microphone",
        "press room journalists", "television news desk", "music studio recording console",
        "broadcasting van outside broadcast", "stage lighting entertainment", "podcast interview microphones"
    ],
    "Economía": [
        "stock exchange floor", "wall street exchange", "trading floor traders", "central bank",
        "federal reserve", "european central bank", "container ship port", "cargo port cranes",
        "container terminal", "freight train cargo", "oil refinery", "wind turbine farm",
        "solar power plant", "automotive assembly factory", "manufacturing robotics",
        "commercial bank building", "commodity trading", "aircraft manufacturing",
        "modern combine harvester", "mining excavator", "world economic forum",
        "international monetary fund", "liquified natural gas tanker", "steel mill factory",
        "rotterdam harbor containers", "singapore port shipping", "logistics warehouse forklift",
        "frankfurt skyline banking", "tokyo stock exchange", "london stock exchange"
    ],
    "Ciencia": [
        "laboratory microscope", "biochemistry laboratory", "molecular biology lab",
        "dna sequencing", "pharmaceutical manufacturing cleanroom", "hospital operating room",
        "mri scanner medical", "virology laboratory biosafety", "astronomical observatory dome",
        "telescope optical mirror", "particle detector cern", "hubble telescope deep field",
        "james webb telescope", "ice core antarctica science", "oceanographic research vessel",
        "scanning electron microscope", "cell culture incubator", "radiotelescope array",
        "mars rover surface", "iss cupola earth", "linear accelerator radiation",
        "optics laser laboratory", "spectrometer analytical chemistry", "cleanroom pharmaceutical"
    ],
    "Geopolítica": [
        "diplomacy summit meeting", "united nations general assembly hall", "bilateral meeting presidents",
        "g20 summit leaders", "g7 summit", "peace conference", "european parliament debate",
        "treaty signing", "foreign ministers meeting", "united nations security council chamber",
        "prime minister press conference", "president oval office", "state dinner banquet",
        "nato summit conference", "international court hague", "presidential palace guard",
        "geneva peace talks", "munich security conference leaders", "diplomatic delegation"
    ]
}

NASA_QUERIES = [
    "hubble space telescope", "james webb space telescope", "mars curiosity rover",
    "perseverance rover mars", "international space station cupola", "artemis moon launch",
    "jupiter juno spacecraft", "saturn cassini rings", "solar dynamics observatory",
    "nebula interstellar space", "andromeda galaxy hubble", "deep space exploration"
]

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
                if width < 1000:
                    continue
                thumb = ii.get("thumburl", ii.get("url"))
                clean_url = thumb.split("?")[0]
                results.append(clean_url)
    except Exception:
        pass
    return cat, results

def fetch_nasa(query):
    url = f"https://images-api.nasa.gov/search?q={urllib.parse.quote(query)}&media_type=image"
    req = urllib.request.Request(url, headers={"User-Agent": "NewsInternacionalTEP/1.0"})
    results = []
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            items = data.get("collection", {}).get("items", [])
            for item in items:
                links = item.get("links", [])
                if links and links[0].get("href"):
                    results.append(links[0].get("href"))
    except Exception:
        pass
    return results

def main():
    pool_file = "unique_images_pool.json"
    category_images = {
        "Geopolítica": [],
        "Economía": [],
        "Tecnología": [],
        "Ciencia": [],
        "Tendencias": []
    }
    seen_all = set()

    # Load existing pool if present
    if os.path.exists(pool_file):
        try:
            with open(pool_file, "r", encoding="utf-8") as fp:
                existing = json.load(fp)
            for cat, imgs in existing.items():
                if cat in category_images:
                    for u in imgs:
                        if u not in seen_all:
                            seen_all.add(u)
                            category_images[cat].append(u)
            print(f"Cargadas {len(seen_all)} imágenes previas existentes.")
        except Exception as e:
            print("No se pudo cargar pool previo:", e)

    tasks = []
    for cat, queries in OPTIMIZED_QUERIES.items():
        for q in queries:
            for offset in [0, 50, 100, 150, 200]:
                tasks.append((cat, q, offset))

    print(f"Total requests planificados: {len(tasks)}")
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = [executor.submit(fetch_wikimedia, cat, q, offset) for (cat, q, offset) in tasks]
        done = 0
        for f in as_completed(futures):
            done += 1
            cat, urls = f.result()
            for u in urls:
                if u not in seen_all:
                    seen_all.add(u)
                    category_images[cat].append(u)
            if done % 100 == 0 or done == len(tasks):
                print(f"  Progreso: {done}/{len(tasks)} requests completados | Total únicas: {len(seen_all)}")

    print("\nAñadiendo imágenes desde NASA Image API...")
    for nq in NASA_QUERIES:
        n_urls = fetch_nasa(nq)
        for u in n_urls:
            if u not in seen_all:
                seen_all.add(u)
                category_images["Ciencia"].append(u)

    print("\n" + "=" * 60)
    print(f"COLECCIÓN COMPLETADA EN {time.time() - start_time:.2f} SEGUNDOS")
    print(f"TOTAL IMÁGENES ÚNICAS GLOBALES: {len(seen_all)}")
    print("DESGLOSE POR CATEGORÍA:")
    for cat, imgs in category_images.items():
        print(f"  - {cat}: {len(imgs)} imágenes únicas")
    print("=" * 60)

    with open(pool_file, "w", encoding="utf-8") as fp:
        json.dump(category_images, fp, indent=2)
    print(f"Base de datos de imágenes actualizada en: {pool_file}")

if __name__ == "__main__":
    main()
