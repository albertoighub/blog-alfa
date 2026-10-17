"""
DUPLICADOR Y TRADUCTOR OFICIAL PARA NEWS INTERNATIONAL TEP
Sincroniza y transcribe automáticamente el archivo de investigación de blog-alfa
hacia blog-international utilizando la IA local de LM Studio (Gemma-4) y diccionarios
estructurados de alta velocidad.
"""

import os
import sys
import glob
import json
import re
import urllib.request
import urllib.parse
from datetime import datetime

SOURCE_DIR = os.path.abspath(r"C:\BIONIC_CORE\blog-alfa\src\content\blog")
DEST_DIR = os.path.abspath(r"C:\BIONIC_CORE\blog-international\src\content\blog")
LM_STUDIO_URL = "http://127.0.0.1:1235/v1/chat/completions"
MODEL_ID = "google/gemma-4-e4b"
SITE_BASE_URL = "https://international.newsinternacionaltep.com"

CATEGORY_MAP = {
    "Geopolítica": "Politics & Defense",
    "Economía": "Economy & Markets",
    "Tecnología": "Technology & AI",
    "Ciencia": "Science & Medicine",
    "Tendencias": "Social Media & Dynamics"
}

CATEGORY_SLUG_MAP = {
    "Geopolítica": "geopolitics",
    "Economía": "economy",
    "Tecnología": "technology",
    "Ciencia": "science",
    "Tendencias": "trends"
}

TAGS_MAP = {
    "Geopolítica": ["Geopolitics", "International Security", "Defense", "Global Governance"],
    "Seguridad Internacional": ["International Security", "Defense Systems", "Geostrategy"],
    "Diplomacia": ["Diplomacy", "Foreign Affairs", "Treaties"],
    "Defensa": ["Defense", "Military Doctrine", "Strategic Deterrence"],
    "Gobernanza Global": ["Global Governance", "Multilateral Order", "Institutions"],
    "Economía Global": ["Global Economy", "Macroeconomics", "Sovereign Debt"],
    "Bancos Centrales": ["Central Banks", "Monetary Policy", "Liquidity"],
    "Mercados Financieros": ["Financial Markets", "Equities", "Fixed Income"],
    "Política Monetaria": ["Monetary Policy", "Interest Rates", "Inflation"],
    "Comercio Internacional": ["International Trade", "Supply Chains", "Tariffs"],
    "Tecnología": ["Technology", "Applied Science", "Hardware Architecture"],
    "Inteligencia Artificial": ["Artificial Intelligence", "Frontier Models", "Machine Learning"],
    "Semiconductores": ["Semiconductors", "Lithography", "Silicon Fabrication"],
    "Ciberseguridad": ["Cybersecurity", "Network Infrastructure", "Cryptography"],
    "Computación Avanzada": ["Advanced Computing", "HPC", "Data Centers"],
    "Ciencia": ["Science", "Empirical Research", "Biomedicine"],
    "Medicina": ["Medicine", "Clinical Trials", "Therapeutics"],
    "Biotecnología": ["Biotechnology", "Genomics", "CRISPR"],
    "Investigación Clínica": ["Clinical Research", "Translational Medicine", "Oncology"],
    "Salud Pública": ["Public Health", "Epidemiology", "Healthcare Policy"],
    "Redes Sociales": ["Social Media", "Platform Architecture", "Algorithmic Feeds"],
    "Dinámica Digital": ["Digital Dynamics", "Network Analysis", "Audiences"],
    "Cultura Algorítmica": ["Algorithmic Culture", "Recommendation Engines", "Behavioral Data"],
    "Plataformas": ["Platforms", "Digital Ecosystems", "Monetization"],
    "Comportamiento Colectivo": ["Collective Behavior", "Public Sphere", "Sociology"]
}

def translate_with_local_llm(text, max_tokens=256):
    """Llama a la IA local en LM Studio para traducir con precisión periodística."""
    prompt = (
        f"Translate the following journalistic analysis text from Spanish into concise, high-level academic English. "
        f"Return ONLY the English translation, with no commentary.\n\nText:\n{text}"
    )
    payload = {
        "model": MODEL_ID,
        "messages": [
            {"role": "system", "content": "You are a professional editor and translator for a prestigious international intelligence journal."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": max_tokens
    }
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            LM_STUDIO_URL,
            data=data,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=12.0) as resp:
            res_json = json.loads(resp.read().decode("utf-8"))
            out = res_json["choices"][0]["message"]["content"].strip()
            # Quitar comillas si el modelo las agregó
            return out.strip('"').strip("'")
    except Exception as e:
        return None

def translate_markdown_file(source_path, dest_path, use_llm=False):
    """Lee un archivo en español y genera su contraparte en inglés."""
    with open(source_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Parsear frontmatter
    fm_match = re.match(r"^---\n(.*?)\n---\n(.*)$", content, re.DOTALL)
    if not fm_match:
        return False

    fm_raw = fm_match.group(1)
    body_raw = fm_match.group(2)

    # Extraer campos
    title_m = re.search(r'title:\s*"(.*?)"', fm_raw)
    desc_m = re.search(r'description:\s*"(.*?)"', fm_raw)
    pubdate_m = re.search(r'pubDate:\s*"(.*?)"', fm_raw)
    cat_m = re.search(r'category:\s*"(.*?)"', fm_raw)
    img_m = re.search(r'heroImage:\s*"(.*?)"', fm_raw)

    title_es = title_m.group(1) if title_m else ""
    desc_es = desc_m.group(1) if desc_m else ""
    pubdate = pubdate_m.group(1) if pubdate_m else "2026-10-14"
    cat_es = cat_m.group(1) if cat_m else "Geopolítica"
    hero_image = img_m.group(1) if img_m else ""

    cat_en = CATEGORY_MAP.get(cat_es, "Politics & Defense")
    cat_slug = CATEGORY_SLUG_MAP.get(cat_es, "geopolitics")
    tags_en = [TAGS_MAP.get(cat_es, ["Intelligence", "Global Research"])[0], "Research Paper", "TEP Archive"]

    # Traducir título y descripción si LLM está activo, o mediante diccionario estilístico
    title_en = None
    desc_en = None
    if use_llm:
        title_en = translate_with_local_llm(title_es, max_tokens=60)
        desc_en = translate_with_local_llm(desc_es, max_tokens=120)

    if not title_en:
        # Reemplazo estilístico de alta velocidad
        title_en = title_es.replace("Análisis Histórico y Causal:", "Historical and Causal Analysis:")
        title_en = title_en.replace("Balance Retrospectivo y Proyección Sistémica", "Retrospective Balance and Systemic Outlook")
        title_en = title_en.replace("Investigación Documental TEP:", "TEP Intelligence Investigation:")
        title_en = title_en.replace("y su Impacto Estructural en el Escenario Global", "and its Structural Impact on the Global Arena")
        title_en = title_en.replace("Crónica Arbitrada:", "Peer-Reviewed Chronicle:")
        title_en = title_en.replace("Modelado de Trayectorias y Lecciones Operativas:", "Trajectory Modeling and Operational Lessons:")
        title_en = title_en.replace("Frente a las Presiones de Transformación Estructural", "Under Structural Transformation Pressures")
        title_en = title_en.replace("Arbitraje Técnico, Vulnerabilidades y Precedentes", "Technical Arbitrage, Vulnerabilities, and Precedents")

    if not desc_en:
        desc_en = (
            f"Exhaustive monographic investigation from the News International TEP historical archive regarding {title_en.lower()}. "
            f"Retrospective evaluation of critical parameters, trajectory modeling, empirical datasets, and prospective editorial judgment."
        )

    # Traducir estructura del cuerpo
    body_en = body_raw
    body_en = body_en.replace("> ### Variables Críticas y Parámetros Operativos del Registro Histórico", "> ### Critical Parameters and Empirical Metrics from Historical Records")
    body_en = body_en.replace("> ### Variables Clave y Parámetros Operativos", "> ### Key Variables and Operational Metrics")
    body_en = body_en.replace("## 1. Contexto Estratégico y Planteamiento del Acontecimiento", "## 1. Strategic Context and Problem Formulation")
    body_en = body_en.replace("## 1. Contexto Estratégico y Planteamiento del Problema", "## 1. Strategic Context and Problem Formulation")
    body_en = body_en.replace("## 2. Estado de la Situación y Dinámica Estructural", "## 2. Empirical State of Affairs and Structural Dynamics")
    body_en = body_en.replace("## 2. Estado del Arte y Dinámica Estructural", "## 2. State of the Art and Structural Dynamics")
    body_en = body_en.replace("## 3. Mecanismos Operativos y Núcleo Técnico", "## 3. Operational Mechanisms and Quantitative Core")
    body_en = body_en.replace("## 4. Evaluación de Escenarios y Modelado de Riesgo", "## 4. Scenario Evaluation and Risk Modeling")
    body_en = body_en.replace("## 5. Reflexión Editorial y Juicio Histórico TEP", "## 5. TEP Editorial Judgment & Historical Reflection")
    body_en = body_en.replace("## 5. Reflexión Personal Profesional & Conclusiones Prospectivas", "## 5. TEP Editorial Judgment & Historical Reflection")
    body_en = body_en.replace("### Trazabilidad Metodológica y Fuentes Primarias", "### Methodological Traceability and Primary Sources")
    body_en = body_en.replace("Figura 1: Mapeo y registro fotográfico documental archivado en la hemeroteca de News Internacional TEP.", "Figure 1: Archival photographic evidence documented in the News International TEP records.")
    body_en = body_en.replace("Figura 2: Proyección de trayectorias y modelado de dispersión elaborado por la Unidad Cuantitativa TEP.", "Figure 2: Trajectory modeling and scenario dispersion prepared by the TEP Quantitative Unit.")
    body_en = body_en.replace("| Parámetro / Vector de Monitoreo | Registro Base Previo | Valor Máximo Registrado | Mecanismo Causal Determinante |", "| Monitoring Vector / Metric | Baseline Record | Maximum Observed Value | Underlying Causal Mechanism |")
    body_en = body_en.replace("| Escenario Evaluado | Probabilidad Asignada Ex-Ante | Desenlace Observado Ex-Post | Factor Crítico de Desviación |", "| Evaluated Scenario | Ex-Ante Probability | Ex-Post Observed Outcome | Critical Deviation Factor |")

    # Frontmatter en inglés
    new_fm = f"""---
title: "{title_en}"
description: "{desc_en}"
pubDate: "{pubdate}"
category: "{cat_en}"
tags: {json.dumps(tags_en, ensure_ascii=False)}
author: "TEP Intelligence Board & Historical Archive"
heroImage: "{hero_image}"
canonicalSource: "{SITE_BASE_URL}/category/{cat_slug}"
---"""

    dest_content = f"{new_fm}\n{body_en}"
    with open(dest_path, "w", encoding="utf-8") as f:
        f.write(dest_content)

    return True

def sync_all_posts(max_posts=None, use_llm=False, force=False):
    os.makedirs(DEST_DIR, exist_ok=True)
    all_files = glob.glob(os.path.join(SOURCE_DIR, "*.md"))
    print(f"[*] Found {len(all_files)} Spanish articles in blog-alfa.")
    
    synced = 0
    target_list = all_files[:max_posts] if max_posts else all_files
    for f in target_list:
        bname = os.path.basename(f)
        dest_file = os.path.join(DEST_DIR, bname)
        if force or not os.path.exists(dest_file):
            success = translate_markdown_file(f, dest_file, use_llm=use_llm)
            if success:
                synced += 1
                if synced % 50 == 0:
                    print(f"  [✓] Synced {synced} articles into English edition...")

    print(f"[✓] Synchronization completed. Total translated articles written: {synced}")

if __name__ == "__main__":
    use_llm = "--llm" in sys.argv
    force = "--force" in sys.argv or True
    sync_all_posts(use_llm=use_llm, force=force)
