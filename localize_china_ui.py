import os

# 1. Update Header.astro
header_path = "src/components/Header.astro"
with open(header_path, "r", encoding="utf-8") as f:
    header = f.read()

header_replacements = [
    ("'es-MX'", "'zh-CN'"),
    ("HORA GLOBAL", "全球标准时间"),
    ("MERCADOS & DIVISAS", "全球金融市场与外汇"),
    ("Nueva York:", "纽约:"),
    ("Londres:", "伦敦:"),
    ("Fráncfort:", "法兰克福:"),
    ("Tokio:", "东京:"),
    ("Singapur:", "新加坡:"),
    ("Dubái:", "迪拜:"),
    ("Cd. de México:", "墨西哥城:"),
    ("ORO (XAU/USD)", "现货黄金 (XAU/USD)"),
    ("BRENT CRUDO", "布伦特原油"),
    ("BONO EE.UU. 10A", "美债10年期"),
    ("Búsqueda Avanzada", "深度检索"),
    ("NEWS INTERNACIONAL <span class=\"brand-badge-tep\">TEP</span>", "NEWS INTERNATIONAL <span class=\"brand-badge-tep\">CHINA TEP</span>"),
    ('>Inicio<', '>首页<'),
    ('>Política<', '>政治与防务<'),
    ('>Economía & Mercados<', '>经济与市场<'),
    ('>Tecnología & IA<', '>科技与AI<'),
    ('>Ciencia & Medicina<', '>科学与医学<'),
    ('>Redes & Revuelo<', '>社交媒体与动态<'),
    ('>Nosotros<', '>关于我们<'),
    ('>♥ Apoyar<', '>♥ 赞助支持<'),
    ("FILTROS DE INTELIGENCIA", "智能情报分析检索"),
    ("Buscador de Publicaciones TEP", "TEP 权威档案与全球情报检索中心"),
    ("Ingrese palabras clave (ej: Litio, Sanciones, Chips, IA)...", "输入关键词（如：半导体、地缘政治、超算、人工智能）..."),
    ("Buscar Publicaciones", "立即检索"),
    ("Resultados encontrados:", "检索结果："),
    ("No se encontraron publicaciones.", "未检索到匹配文献。"),
    ("Ver publicación completa →", "查看完整研报 →"),
    ("ESC para cerrar", "按 ESC 关闭")
]

for old, new in header_replacements:
    header = header.replace(old, new)

with open(header_path, "w", encoding="utf-8") as f:
    f.write(header)

print("Header.astro localized to Chinese.")

# 2. Update Footer.astro
footer_path = "src/components/Footer.astro"
with open(footer_path, "r", encoding="utf-8") as f:
    footer = f.read()

footer_replacements = [
    ("NEWS INTERNACIONAL <span class=\"footer-badge\">TEP</span>", "NEWS INTERNATIONAL <span class=\"footer-badge\">CHINA TEP</span>"),
    ("Diario científico y plataforma de inteligencia global enfocado en la investigación estructural, analítica cuantitativa de mercados y soberanía tecnológica sin sesgos mediáticos.", "全球科学与宏观战略情报平台，聚焦结构性实证研究、定量金融市场分析及独立前沿研报。"),
    ("All rights reserved.", "保留所有权利。"),
    ("ÁREAS DE COBERTURA", "核心研究领域"),
    ("Política & Orden Global", "政治与防务战略"),
    ("Economía & Mercados Financieros", "经济与全球金融市场"),
    ("Tecnología & IA", "科技与人工智能"),
    ("Ciencia & Medicina de Precisión", "前沿科学与精准医学"),
    ("Redes Sociales & Tendencias Virales", "社交媒体与数字化动态"),
    ("INSTITUCIONAL & APOYO", "机构与赞助"),
    ("Nosotros y Misión Editorial", "关于我们与学术标准"),
    ("Términos y Condiciones", "服务条款"),
    ("Política de Privacidad", "隐私政策"),
    ("Apoyar con PayPal al Creador", "通过官方 PayPal 赞助支持"),
    ("Edición en Español (newsinternacionaltep.com)", "西班牙语主网 (newsinternacionaltep.com)"),
    ("Edición en Inglés (international.newsinternacionaltep.com)", "英文国际版 (international.newsinternacionaltep.com)")
]

for old, new in footer_replacements:
    footer = footer.replace(old, new)

with open(footer_path, "w", encoding="utf-8") as f:
    f.write(footer)

print("Footer.astro localized to Chinese.")

# 3. Update index.astro
index_path = "src/pages/index.astro"
with open(index_path, "r", encoding="utf-8") as f:
    index_html = f.read()

index_replacements = [
    ('<html lang="es">', '<html lang="zh-CN">'),
    ('Publicaciones en Rotación Continua', '持续轮播深度精选研报'),
    ('FLUJO EN VIVO', '实时情报流'),
    ('aria-label="Pausar o Reanudar rotación">⏸ Pausar</button>', 'aria-label="暂停或继续轮播">⏸ 暂停</button>'),
    ('toggleBtn.textContent = "▶ Reanudar";', 'toggleBtn.textContent = "▶ 继续";'),
    ('toggleBtn.textContent = "⏸ Pausar";', 'toggleBtn.textContent = "⏸ 暂停";'),
    ('<span>RADAR DE COBERTURA</span>', '<span>全球监控情报雷达</span>'),
    ('<span style="font-size: 0.65rem; color: #dc2626;">MONITOREO EN VIVO</span>', '<span style="font-size: 0.65rem; color: #dc2626;">实时电讯监控</span>'),
    ('<span>Acceder al Dossier Completo</span>', '<span>查阅完整研报卷宗</span>'),
    ('Investigación crítica sobre perfilamiento algorítmico no consentido, filtros de sesgo automatizados y la vulnerabilidad sociológica de los postulantes en la era digital.', '关于非自愿算法画像、自动化偏见过滤机制及数字劳动力市场中应聘者社会学脆弱性的深度专题调查。'),
    ('ESPACIO PUBLICITARIO INSTITUCIONAL • GOOGLE ADSENSE (ca-pub-3739732712037306)', '官方赞助展示席位 • GOOGLE ADSENSE (ca-pub-3739732712037306)'),
    ('Política & Orden Global', '政治与全球防务格局'),
    ('Economía & Mercados Financieros', '经济与全球金融市场'),
    ('Tecnología & Inteligencia Artificial', '前沿科技与人工智能'),
    ('Ciencia & Medicina de Frontera', '前沿科学与尖端医学'),
    ('Redes Sociales & Noticias de Alto Revuelo', '社交媒体与数字化动态'),
    ('Ver sección completa →', '查看完整专题专栏 →'),
    ('• TEP Política', '• TEP 政治防务'),
    ('• TEP Mercados', '• TEP 全球市场'),
    ('• TEP Tecnología', '• TEP 前沿科技'),
    ('• TEP Ciencia', '• TEP 科学医学'),
    ('• TEP Dinámica Digital', '• TEP 动态网络'),
    ('INDEPENDENCIA ANALÍTICA & RIGOR EDITORIAL', '独立学术分析 • 客观事实准则'),
    ('Impulsa el Archivo Libre de News Internacional TEP', '助力 News International (China) TEP 开放知识档案库'),
    ('Nuestra redacción e infraestructura técnica operan sin subsidios corporativos ni censura partidista. Tu contribución directa a través de PayPal fortalece nuestros servidores de análisis, la ingesta continua de cables de datos y el acceso abierto a la inteligencia global.', '我们的数据架构与分析团队保持高度客观独立。您通过官方 PayPal 的直接资助将用于强化高性能分布式计算服务器、持续接入一手全球电讯数据流，并保障高质量情报对全球研究共同体完全开放。'),
    ('<span>Donar con PayPal Oficial</span>', '<span>使用官方 PayPal 赞助支持</span>'),
    ('Titular: andredateig@gmail.com', '收款方账户：andredateig@gmail.com'),
    ("'es-MX'", "'zh-CN'")
]

for old, new in index_replacements:
    index_html = index_html.replace(old, new)

with open(index_path, "w", encoding="utf-8") as f:
    f.write(index_html)

print("index.astro in blog-china localized to Chinese.")
