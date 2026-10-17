import os
from collections import Counter

counts = Counter()
blog_dir = "src/content/blog"
total_files = 0

for entry in os.scandir(blog_dir):
    if entry.name.endswith(".md"):
        total_files += 1
        try:
            with open(entry.path, "r", encoding="utf-8", errors="ignore") as fp:
                for line in fp:
                    if line.startswith("heroImage:"):
                        img = line.split(":", 1)[1].strip().strip('"\'')
                        counts[img] += 1
                        break
        except Exception:
            pass

print(f"Total articles analyzed: {total_files}")
print(f"Total heroImage occurrences: {sum(counts.values())}")
print(f"Unique images currently used: {len(counts)}")
print("Top 5 most repeated images:")
for img, cnt in counts.most_common(5):
    print(f"  - Repetitions: {cnt} | URL: {img[:80]}...")
