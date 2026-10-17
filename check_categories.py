import glob

counts = {}
for f in glob.glob("src/content/blog/*.md"):
    try:
        with open(f, "r", encoding="utf-8", errors="ignore") as fp:
            for line in fp:
                if line.startswith("category:"):
                    cat = line.split(":", 1)[1].strip().strip('"\'')
                    counts[cat] = counts.get(cat, 0) + 1
                    break
    except Exception:
        pass

print("Distribución actual por categoría:")
for k, v in sorted(counts.items()):
    print(f"  - {k}: {v}")
