import os
import re

POSTS_DIR = os.path.join("src", "content", "blog")

PHOTOS_CIENCIA = [
    "https://images.unsplash.com/photo-1579684385127-1ef15d508118", # Microscopio
    "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69", # Pipetas bioquímica
    "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b", # Laboratorio médico
    "https://images.unsplash.com/photo-1530497610245-94d3c16cda28", # ADN / genética
    "https://images.unsplash.com/photo-1516549655169-df83a0774514", # Quirúrgico / clínico
    "https://images.unsplash.com/photo-1559757175-5700dde675bc", # Diagnóstico y monitoreo
    "https://images.unsplash.com/photo-1511174511562-5f7f18b874f8", # Precisión quirúrgica
    "https://images.unsplash.com/photo-1576086213369-97a306d36557", # Microbiología / placas
    "https://images.unsplash.com/photo-1581093458791-9f3c3900df4b", # Criomicroscopía
    "https://images.unsplash.com/photo-1507668077129-56e32842fceb", # Neurociencia
    "https://images.unsplash.com/photo-1584515979956-d9f6e5d09982", # Virología / vacunas
    "https://images.unsplash.com/photo-1583912267670-6575ad472688", # Criogenia / biobancos
    "https://images.unsplash.com/photo-1583912267749-011867160320", # Farmacología molecular
    "https://images.unsplash.com/photo-1532094349884-543bc11b234d", # Química analítica
    "https://images.unsplash.com/photo-1563245372-f21724e3856d", # Telemetría médica
    "https://images.unsplash.com/photo-1579154204601-01588f351e67", # Centrífuga hematológica
    "https://images.unsplash.com/photo-1584515933487-779824d29309", # Pruebas serológicas
    "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d", # Medicina de precisión
    "https://images.unsplash.com/photo-1576091160550-2173dba999ef", # Histología celular
    "https://images.unsplash.com/photo-1581594693702-fbdc51b2763b", # Sala blanca
]

PHOTOS_TENDENCIAS = [
    "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe", # Red abstracta
    "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5", # Algoritmos
    "https://images.unsplash.com/photo-1519389950473-47ba0277781c", # Creadores de contenido
    "https://images.unsplash.com/photo-1516321318423-f06f85e504b3", # Redes sociales
    "https://images.unsplash.com/photo-1550751827-4bd374c3f58b", # Ciberespacio y metadatos
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa", # Red satelital
    "https://images.unsplash.com/photo-1573164713988-8665fc963095", # Conferencia de medios
    "https://images.unsplash.com/photo-1517245386807-bb43f82c33c4", # Estudio broadcast / streaming
    "https://images.unsplash.com/photo-1534528741775-53994a69daeb", # Retrato documental
    "https://images.unsplash.com/photo-1522071820081-009f0129c71c", # Estrategia digital
    "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9", # Teléfonos y video vertical
    "https://images.unsplash.com/photo-1508739773434-c26b3d09e071", # Pantallas urbanas
    "https://images.unsplash.com/photo-1504384308090-c894fdcc538d", # Data centers
    "https://images.unsplash.com/photo-1558494949-ef010cbdcc31", # Servidores
    "https://images.unsplash.com/photo-1529156069898-49953e39b3ac", # Audiencias y jóvenes
    "https://images.unsplash.com/photo-1542744173-8e7e53415bb0", # Métricas de audiencia
    "https://images.unsplash.com/photo-1551836022-d5d88e9218df", # Interacción táctil
    "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2", # Vocería oficial
    "https://images.unsplash.com/photo-1515378791036-0648a3ef77b2", # Redacción digital
    "https://images.unsplash.com/photo-1531403009284-440f080d1e12", # Plataformas UX
]

def clean_url(base_url, w=1200, h=630):
    return f"{base_url}?auto=format&fit=crop&w={w}&h={h}&q=82"

count = 0
files = sorted([f for f in os.listdir(POSTS_DIR) if f.endswith(".md")])

for i, fname in enumerate(files):
    fpath = os.path.join(POSTS_DIR, fname)
    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    if "pollinations.ai" not in content:
        continue

    is_ciencia = "Ciencia" in content or "-cie-" in fname
    photo_pool = PHOTOS_CIENCIA if is_ciencia else PHOTOS_TENDENCIAS
    
    # 3 imágenes distintas y determinísticas para cada paper
    hero_base = photo_pool[i % len(photo_pool)]
    in1_base = photo_pool[(i + 7) % len(photo_pool)]
    in2_base = photo_pool[(i + 13) % len(photo_pool)]
    
    hero_url = clean_url(hero_base, 1200, 630)
    in1_url = clean_url(in1_base, 1000, 500)
    in2_url = clean_url(in2_base, 1000, 500)
    
    # Reemplazo de heroImage
    content = re.sub(
        r'heroImage:\s*"https://image\.pollinations\.ai/[^"]+"',
        f'heroImage: "{hero_url}"',
        content
    )
    
    # Reemplazar inline images
    pollination_links = re.findall(r'https://image\.pollinations\.ai/[^\)\"\s]+', content)
    if len(pollination_links) >= 1:
        content = content.replace(pollination_links[0], in1_url)
    if len(pollination_links) >= 2:
        content = content.replace(pollination_links[1], in2_url)
    # Por si queda alguno suelto
    content = re.sub(r'https://image\.pollinations\.ai/[^\)\"\s]+', in1_url, content)
    
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
        
    count += 1

print(f"[✓] Se reemplazaron todas las imágenes de Pollinations por fotografías auténticas de alta definición en {count} artículos.")
