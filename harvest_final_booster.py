import urllib.request
import urllib.parse
import json
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

FINAL_QUERIES = {
    "Economía": [
        "central bank meeting", "federal reserve chair", "stock exchange bell ringing",
        "wall street bull", "banknotes currency", "gold bullion vault",
        "cargo ship crane", "freight train locomotive", "oil tanker sea",
        "wind power turbine", "solar farm panels", "wheat harvest combine",
        "modern tractor agriculture", "automotive robotic welding", "steel foundry furnace",
        "air cargo logistics", "rotterdam port aerial", "singapore port night",
        "frankfurt financial district", "london bank skyscrapers", "tokyo financial district",
        "hong kong financial center", "chicago board of trade", "commodity futures trading",
        "container shipping logistics", "freight rail transport", "energy power grid transformer",
        "offshore oil rig drilling", "modern dairy farming automation", "commercial aviation manufacturing"
    ],
    "Ciencia": [
        "medical researcher pipetting", "biochemistry laboratory glassware", "dna helix model",
        "laboratory incubator cell culture", "fluorescence microscopy cell", "optical telescope mount observatory",
        "cern compact muon solenoid", "deep space nebula hubble", "james webb telescope golden mirrors",
        "antarctica glacier science", "marine biology coral reef research", "surgical robot hospital",
        "quantum optics table laser", "paleontology dinosaur fossil", "seismograph station",
        "astronaut spacewalk earth", "mars rover sample tube", "nanotechnology scanning probe",
        "bioreactor cell culture", "radiotherapy cancer treatment linac", "climate science weather station",
        "superconducting magnet laboratory", "cleanroom silicon wafer inspection", "neuroscience eeg cap recording",
        "astronomical spectrograph observatory", "ocean research submarine submersible", "volcanology field research"
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
    for cat, queries in FINAL_QUERIES.items():
        for q in queries:
            for offset in [0, 50, 100, 150, 200]:
                tasks.append((cat, q, offset))

    print(f"Total requests planificados: {len(tasks)}")
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
            if done % 50 == 0 or done == len(tasks):
                print(f"  Progreso: {done}/{len(tasks)} requests | Añadidas: {added_count} nuevas | Total pool: {len(seen_all)}")

    print("\n" + "=" * 60)
    print(f"COLECCIÓN FINAL COMPLETADA EN {time.time() - start_time:.2f} SEGUNDOS")
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
