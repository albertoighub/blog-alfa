import glob
import os
import re

files = glob.glob("src/content/blog/*.md")
truly_blurry = []

for f in files:
    content = open(f, encoding="utf-8", errors="ignore").read()
    for line in content.splitlines()[:15]:
        if line.startswith("heroImage:"):
            u = line.split("heroImage:")[1].strip(" \"'")
            # Match 100x100 or thumbnail URLs
            if "jornaldenegocios.pt" in u or "100x100" in u or "150x150" in u or "200x200" in u:
                truly_blurry.append((f, u, "Tiny thumbnail"))
            elif "bonniernews" in u or "kyivindependent" in u:
                truly_blurry.append((f, u, "External scrape"))

print(f"Total definitely blurry/thumbnail images: {len(truly_blurry)}")
for f, u, reason in truly_blurry:
    print(f"  {os.path.basename(f)}: {u} ({reason})")
