import os
import re
import time

def main():
    alfa_dir = "src/content/blog"
    intl_dir = "../blog-international/src/content/blog"

    if not os.path.exists(intl_dir):
        print(f"Error: {intl_dir} does not exist.")
        return

    alfa_files = sorted([f for f in os.listdir(alfa_dir) if f.endswith(".md")])
    print(f"Sincronizando {len(alfa_files)} artículos a la edición internacional en inglés...")

    start_time = time.time()
    synced_count = 0

    for fname in alfa_files:
        alfa_path = os.path.join(alfa_dir, fname)
        intl_path = os.path.join(intl_dir, fname)

        if not os.path.exists(intl_path):
            continue

        with open(alfa_path, "r", encoding="utf-8", errors="ignore") as fp:
            alfa_text = fp.read()

        # Extract heroImage
        hero_match = re.search(r'heroImage:\s*["\']?(https://[^\s"\']+)["\']?', alfa_text)
        if not hero_match:
            continue
        new_hero = hero_match.group(1)

        # Extract body images
        alfa_body_images = re.findall(r'!\[([^\]]*)\]\((https://[^\)]+)\)', alfa_text)

        with open(intl_path, "r", encoding="utf-8", errors="ignore") as fp:
            intl_text = fp.read()

        # Update heroImage in intl
        intl_text = re.sub(
            r'heroImage:\s*["\']?https://[^\s"\']+["\']?',
            f'heroImage: "{new_hero}"',
            intl_text,
            count=1
        )

        # Update body figures in intl
        intl_body_images = re.findall(r'!\[([^\]]*)\]\((https://[^\)]+)\)', intl_text)
        for idx, (alt, old_url) in enumerate(intl_body_images):
            if idx < len(alfa_body_images):
                target_url = alfa_body_images[idx][1]
                old_tag = f"![{alt}]({old_url})"
                new_tag = f"![{alt}]({target_url})"
                intl_text = intl_text.replace(old_tag, new_tag, 1)

        with open(intl_path, "w", encoding="utf-8") as fp:
            fp.write(intl_text)

        synced_count += 1
        if synced_count % 1000 == 0 or synced_count == len(alfa_files):
            print(f"  Sincronizados: {synced_count}/{len(alfa_files)} artículos...")

    print("=" * 60)
    print(f"SINCRONIZACIÓN COMPLETADA EN {time.time() - start_time:.2f} SEGUNDOS")
    print(f"Total artículos sincronizados con imágenes únicas en el gemelo inglés: {synced_count}")
    print("=" * 60)

if __name__ == "__main__":
    main()
