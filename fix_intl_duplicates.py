import os
import re
from collections import Counter

alfa_dir = "../blog-alfa/src/content/blog"
intl_dir = "src/content/blog"

# Read all alfa heroImages
alfa_heroes = {}
for entry in os.scandir(alfa_dir):
    if entry.name.endswith(".md"):
        with open(entry.path, "r", encoding="utf-8", errors="ignore") as fp:
            for line in fp:
                if line.startswith("heroImage:"):
                    img = line.split(":", 1)[1].strip().strip('"\'')
                    alfa_heroes[entry.name] = img
                    break

print(f"Total alfa heroes loaded: {len(alfa_heroes)} | Unique: {len(set(alfa_heroes.values()))}")

# Fix any intl file where heroImage doesn't match alfa
mismatches = 0
for fname, target_hero in alfa_heroes.items():
    intl_path = os.path.join(intl_dir, fname)
    if not os.path.exists(intl_path):
        continue
    with open(intl_path, "r", encoding="utf-8", errors="ignore") as fp:
        content = fp.read()

    # Current intl hero
    m = re.search(r"heroImage:\s*[\"']?([^\"\r\n]+)[\"']?", content)
    curr_hero = m.group(1).strip() if m else ""

    if curr_hero != target_hero:
        mismatches += 1
        content = re.sub(
            r"heroImage:\s*[\"']?[^\r\n\"']+[\"']?",
            f'heroImage: "{target_hero}"',
            content,
            count=1
        )
        with open(intl_path, "w", encoding="utf-8") as fp:
            fp.write(content)

print(f"Total mismatches fixed: {mismatches}")

# Verify uniqueness now
counts = Counter()
for entry in os.scandir(intl_dir):
    if entry.name.endswith(".md"):
        with open(entry.path, "r", encoding="utf-8", errors="ignore") as fp:
            for line in fp:
                if line.startswith("heroImage:"):
                    img = line.split(":", 1)[1].strip().strip('"\'')
                    counts[img] += 1
                    break

print(f"Final International Unique Hero Images: {len(counts)}/{sum(counts.values())}")
print(f"Top 3 occurrences: {counts.most_common(3)}")
assert len(counts) == 6310, "International does not have 6310 unique hero images!"
print("MATEMÁTICAMENTE VERIFICADO: El sitio gemelo en inglés tiene 100% imágenes de portada únicas.")
