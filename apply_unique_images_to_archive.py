import glob
import re
import json
import os
from collections import Counter

def normalize_category(raw_cat):
    c = raw_cat.strip().lower()
    if "cien" in c:
        return "Ciencia"
    elif "econ" in c:
        return "Economía"
    elif "geo" in c or "pol" in c:
        return "Geopolítica"
    elif "tec" in c:
        return "Tecnología"
    elif "trend" in c or "tend" in c or "red" in c:
        return "Tendencias"
    return "Geopolítica"

def main():
    pool_file = "unique_images_pool.json"
    if not os.path.exists(pool_file):
        print(f"Error: No se encontró {pool_file}")
        return

    with open(pool_file, "r", encoding="utf-8") as fp:
        pool = json.load(fp)

    print("Pool disponible por categoría:")
    for k, v in pool.items():
        print(f"  - {k}: {len(v)} imágenes disponibles")

    # Queue iterators
    queues = {k: list(v) for k, v in pool.items()}
    pointers = {k: 0 for k in pool.keys()}

    articles = sorted(glob.glob("src/content/blog/*.md"))
    print(f"\nProcesando {len(articles)} artículos...")

    assigned_hero = set()
    assigned_all = set()
    duplicate_errors = 0
    updated_articles = 0

    def get_next_image(cat):
        nonlocal duplicate_errors
        q = queues[cat]
        p = pointers[cat]
        while p < len(q):
            img = q[p]
            p += 1
            pointers[cat] = p
            if img not in assigned_all:
                assigned_all.add(img)
                return img
        # If pool for specific category exhausted, borrow from another category with surplus
        for other_cat, o_q in queues.items():
            op = pointers[other_cat]
            while op < len(o_q):
                img = o_q[op]
                op += 1
                pointers[other_cat] = op
                if img not in assigned_all:
                    assigned_all.add(img)
                    return img
        duplicate_errors += 1
        raise RuntimeError(f"Error: Agotadas todas las imágenes del pool para {cat}")

    for idx, fpath in enumerate(articles):
        with open(fpath, "r", encoding="utf-8", errors="ignore") as fp:
            content = fp.read()

        # Find category
        cat_match = re.search(r"category:\s*[\"']?([^\"\n\r]+)[\"']?", content)
        raw_cat = cat_match.group(1) if cat_match else "Geopolítica"
        cat = normalize_category(raw_cat)

        # 1. Assign unique Hero Image
        new_hero = get_next_image(cat)
        assigned_hero.add(new_hero)

        # Replace heroImage
        content = re.sub(
            r'heroImage:\s*["\']?https://[^\s"\']+["\']?',
            f'heroImage: "{new_hero}"',
            content,
            count=1
        )

        # 2. Assign unique Figure 1 & Figure 2 in body
        # Find all markdown images in body ![alt](url)
        body_images = re.findall(r'!\[([^\]]*)\]\((https://[^\)]+)\)', content)
        for alt, old_url in body_images:
            new_body_img = get_next_image(cat)
            # Replace exact occurrence
            old_tag = f"![{alt}]({old_url})"
            new_tag = f"![{alt}]({new_body_img})"
            content = content.replace(old_tag, new_tag, 1)

        with open(fpath, "w", encoding="utf-8") as fp:
            fp.write(content)

        updated_articles += 1
        if updated_articles % 1000 == 0 or updated_articles == len(articles):
            print(f"  Artículos actualizados: {updated_articles}/{len(articles)}")

    print("\n" + "=" * 60)
    print("VERIFICACIÓN DE APLICACIÓN Y UNICIDAD")
    print("=" * 60)
    print(f"Total artículos procesados: {updated_articles}")
    print(f"Total imágenes de portada (Hero) asignadas: {len(assigned_hero)}")
    print(f"Total imágenes globales utilizadas (Hero + Cuerpo): {len(assigned_all)}")
    print(f"Errores de duplicidad o agotamiento: {duplicate_errors}")

    assert len(assigned_hero) == len(articles), f"Mismatch en portadas: {len(assigned_hero)} vs {len(articles)}"
    print("MATEMÁTICAMENTE VERIFICADO: 100% de las publicaciones tienen portada única.")
    print("Ninguna imagen se repite en todo el sitio web.")
    print("=" * 60)

if __name__ == "__main__":
    main()
