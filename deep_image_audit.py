import glob
import re
from collections import Counter

hero_counts = Counter()
body_counts = Counter()
total_files = 0

for f in glob.glob("src/content/blog/*.md"):
    total_files += 1
    with open(f, "r", encoding="utf-8", errors="ignore") as fp:
        content = fp.read()
    h = re.findall(r"heroImage:\s*[\"']?(https://[^\s\"']+)[\"']?", content)
    if h:
        hero_counts[h[0]] += 1
    b = re.findall(r"!\[.*?\]\((https://[^\s\)]+)\)", content)
    for img in b:
        body_counts[img] += 1

print(f"Total articles analyzed: {total_files}")
print(f"Unique hero images: {len(hero_counts)}")
print(f"Top 5 repeated hero images:")
for url, c in hero_counts.most_common(5):
    print(f"  [{c} times] {url}")

print(f"\nUnique body images: {len(body_counts)}")
print(f"Top 5 repeated body images:")
for url, c in body_counts.most_common(5):
    print(f"  [{c} times] {url}")
