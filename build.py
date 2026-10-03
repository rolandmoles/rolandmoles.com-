#!/usr/bin/env python3
"""
Generador de rolandmoles.com
----------------------------
Convierte las páginas de src/pages en HTML final dentro de dist/.

  python3 build.py            -> construye el sitio
  python3 build.py --serve    -> construye y sirve en http://localhost:8000

Cada página empieza con un bloque <!--meta {...} --> (título, descripción...)
seguido de su contenido. La cabecera, el menú, el pie, el SEO y los datos
estructurados se añaden aquí automáticamente.
"""
import base64, datetime, hashlib, html, json, os, re, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
DIST = os.path.join(ROOT, "docs")

# ---------------------------------------------------------------- AJUSTES
SITE = {
    "domain": "https://www.rolandmoles.com",
    "name": "Roland Moles",
    "email": "hola@rolandmoles.com",            # correo público de la web
    "formspree": "https://formspree.io/f/mlgzvdlb",
    "instagram": "https://www.instagram.com/roland.moles/",
    "linkedin": "https://www.linkedin.com/in/roland-moles-cateura-a41483145/",
    "og_image": "/assets/img/og-image.jpg",
    "locale": "es_ES",
    "goatcounter": "rolandmoles",                # estadísticas sin cookies (vacío = desactivadas)
}

NAV = [("inicio_", "/"), ("sobre mí_", "/sobre-mi"), ("proyectos_", "/proyectos"),
       ("media_", "/media"), ("contacto_", "/contacto")]

# Script mínimo en línea: activa las animaciones solo si hay JavaScript.
# Si site.js no llegara a cargar, a los 3 s se muestra todo igualmente.
INLINE_JS = ("document.documentElement.classList.add('js');"
             "setTimeout(function(){if(!window.__rm)document.documentElement.classList.remove('js')},3000);")


def esc(s):
    return html.escape(s, quote=True)


def sha256_b64(s):
    return base64.b64encode(hashlib.sha256(s.encode()).digest()).decode()


# ---------------------------------------------------------------- MACROS
# Pequeños atajos para no repetir HTML. Formato: {{nombre: campo | campo | ...}}
# En los textos, " ¶ " equivale a un salto de línea.

BACK = ('<a class="inline-flex items-baseline gap-2 text-white/40 hover:text-primary mb-24 transition-colors group text-sm tracking-tight" href="/proyectos">'
        '<span class="group-hover:-translate-x-1 transition-transform inline-block" aria-hidden="true">←</span><span>volver_</span></a>')


def nl(t):
    return re.sub(r"\s*¶\s*", "\n", t)


def m_project_row(href, year, status, title, cat, text):
    return (f'<div data-r="up" style="--dur:.4s"><a class="group block border-b border-white/5 py-8 sm:py-10 md:py-12 hover:bg-white/[0.02] transition-all" href="{href}">'
            '<div class="grid grid-cols-12 gap-4 sm:gap-6 md:gap-8 items-start"><div class="col-span-12 sm:col-span-3 md:col-span-2 text-xs tracking-tight">'
            f'<p class="text-white/30">{year}</p><p class="text-primary mt-2">{status}</p></div>'
            '<div class="col-span-12 sm:col-span-9 md:col-span-10 space-y-2 sm:space-y-3"><div class="flex items-baseline justify-between gap-4">'
            f'<h2 class="text-lg sm:text-xl md:text-2xl tracking-tight group-hover:text-primary transition-colors">{title}</h2>'
            '<span class="text-primary opacity-0 group-hover:opacity-100 transition-opacity text-xs sm:text-sm flex-shrink-0" aria-hidden="true">→</span></div>'
            f'<p class="text-xs text-white/40 tracking-tight">{cat}</p>'
            f'<p class="text-xs sm:text-sm text-white/50 leading-relaxed max-w-2xl tracking-tight">{text}</p></div></div></a></div>')


def m_press_row(href, year, media, title, text):
    return (f'<div data-r="up" style="--dur:.4s"><a href="{href}" target="_blank" rel="noopener noreferrer" class="group block border-b border-white/5 py-8 sm:py-10 md:py-12 hover:bg-white/[0.02] transition-all">'
            '<div class="grid grid-cols-12 gap-4 sm:gap-6 md:gap-8 items-start"><div class="col-span-12 sm:col-span-3 md:col-span-2 text-xs tracking-tight">'
            f'<p class="text-white/30">{year}</p><p class="text-white/40 mt-2">{media}</p></div>'
            '<div class="col-span-12 sm:col-span-9 md:col-span-10 space-y-2 sm:space-y-3"><div class="flex items-baseline justify-between gap-4">'
            f'<h2 class="text-lg sm:text-xl md:text-2xl tracking-tight group-hover:text-primary transition-colors">{title}</h2>'
            '<span class="text-primary opacity-0 group-hover:opacity-100 transition-opacity text-xs sm:text-sm flex-shrink-0" aria-hidden="true">→</span></div>'
            f'<p class="text-xs sm:text-sm text-white/50 leading-relaxed max-w-2xl tracking-tight">{text}</p></div></div></a></div>')


def m_photo(name, alt):
    return (f'<button type="button" class="block aspect-square bg-white/5 overflow-hidden cursor-pointer group" data-lb="/assets/img/{name}-full.webp" aria-label="Ampliar: {esc(alt)}">'
            f'<img src="/assets/img/{name}.webp" alt="{esc(alt)}" width="800" height="800" loading="lazy" decoding="async" '
            'class="w-full h-full object-cover opacity-40 group-hover:opacity-60 transition-all duration-700 grayscale group-hover:grayscale-0"></button>')


def m_project_head(year, cat, status, title, lede):
    return ('<div class="mb-24"><div class="flex flex-wrap gap-6 mb-12 text-xs tracking-tight">'
            f'<div class="text-white/30">{year}</div><div class="text-white/30">{cat}</div><div class="text-primary">{status}</div></div>'
            f'<h1 class="text-4xl md:text-5xl mb-8 tracking-tight leading-tight">{title}</h1>'
            f'<p class="text-base text-white/50 tracking-tight leading-relaxed max-w-2xl">{lede}</p></div>')


def m_row(label, text):
    return (f'<div class="grid grid-cols-12 gap-8"><div class="col-span-3 text-white/30">{label}</div>'
            f'<div class="col-span-9"><p class="text-white/50 leading-relaxed whitespace-pre-line">{nl(text)}</p></div></div>')


def m_collab(name, role):
    return (f'<div class="border-l border-primary/30 pl-4 space-y-1"><h3 class="text-white/80">{name}</h3>'
            f'<p class="text-white/40 text-xs">{role}</p></div>')


SIMPLE = {
    "rows_start": '<div class="space-y-12 mb-24 text-sm tracking-tight">',
    "rows_end": "</div>",
    "collabs_start": ('<div class="border-t border-white/5 pt-24 mb-24"><h2 class="text-xl mb-12 tracking-tight">colaboradores_</h2>'
                      '<div class="grid grid-cols-1 md:grid-cols-2 gap-8 text-sm tracking-tight">'),
    "collabs_end": "</div></div>",
    "project_end": ('<div class="mt-20 pt-12 border-t border-white/5 flex flex-wrap gap-4 items-center">'
                    '<a class="inline-block px-8 py-4 bg-primary text-black hover:bg-primary/80 transition-all text-sm tracking-tight" href="/contacto">contacto_</a>'
                    '</div></div></div></div>'),
}

MACROS = {"project_row": m_project_row, "press_row": m_press_row, "photo": m_photo,
          "project_head": m_project_head, "row": m_row, "collab": m_collab}


def expand(body, meta):
    decor = ""
    if meta.get("decor"):
        decor = open(os.path.join(SRC, "partials", meta["decor"] + ".html"), encoding="utf-8").read().strip()
    nxt = meta.get("_next")
    next_html = ""
    if nxt:
        next_html = ('<a class="group block mt-20 pt-12 border-t border-white/5" href="' + nxt[0] + '">'
                     '<p class="text-xs text-white/30 tracking-tight mb-4">siguiente proyecto_</p>'
                     '<div class="flex items-baseline justify-between gap-4"><span class="text-2xl md:text-3xl tracking-tight group-hover:text-primary transition-colors">'
                     + nxt[1] + '</span><span class="text-primary opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all text-sm flex-shrink-0" aria-hidden="true">→</span></div></a>')
    SIMPLE["project_end"] = ('<div class="mt-20 pt-12 border-t border-white/5 flex flex-wrap gap-4 items-center">'
                             '<a class="inline-block px-8 py-4 bg-primary text-black hover:bg-primary/80 transition-all text-sm tracking-tight" href="/contacto">contacto_</a>'
                             '</div>' + next_html + '</div></div></div>')
    SIMPLE["project_start"] = ('<div class="relative min-h-screen pt-24 sm:pt-32 pb-16 sm:pb-24 overflow-hidden">' + decor +
                               '<div class="max-w-[1200px] mx-auto px-8 md:px-16"><div data-r="fade" data-load style="--dur:.5s">' + BACK)

    def rep(m):
        name, args = m.group(1), m.group(2)
        if args is None:
            if name in SIMPLE:
                return SIMPLE[name]
            if name in SITE:
                return esc(SITE[name])
            raise SystemExit(f"Macro desconocida: {name}")
        parts = [p.strip() for p in args.split(" | ")]
        return MACROS[name](*parts)

    return re.sub(r"\{\{\s*(\w+)\s*(?::\s*(.*?))?\s*\}\}", rep, body, flags=re.S)


# ---------------------------------------------------------------- LAYOUT

def nav_html(path):
    items = "".join(
        f'<div class="mi"><a class="block text-4xl sm:text-5xl md:text-6xl tracking-tight transition-colors '
        f'{"text-primary" if href == path else "text-white/80 hover:text-primary"}" href="{href}"'
        f'{" aria-current=\"page\"" if href == path else ""}>{name}</a></div>'
        for name, href in NAV)
    return ('<nav class="fixed top-0 left-0 right-0 z-50 bg-black/80 backdrop-blur-md" aria-label="Principal"><div class="max-w-[1600px] mx-auto px-4 sm:px-8 md:px-16 py-4 sm:py-6 md:py-8">'
            '<div class="flex items-center justify-between"><a class="text-xs sm:text-sm tracking-tight hover:text-primary transition-colors" href="/">roland moles</a>'
            '<button type="button" id="menu-btn" class="text-xs sm:text-sm tracking-tight hover:text-primary transition-colors" aria-label="Menú" aria-expanded="false" aria-controls="menu">menú_</button>'
            '</div></div></nav>'
            '<div id="menu" class="fixed inset-0 z-40 bg-black/95 backdrop-blur-lg"><div class="flex items-center justify-center min-h-screen">'
            f'<div class="space-y-8 text-center">{items}</div></div></div>')


def footer_html():
    e = esc(SITE["email"])
    return ('<footer class="border-t border-white/5 mt-20 sm:mt-32 md:mt-40"><div class="max-w-[1600px] mx-auto px-4 sm:px-8 md:px-16 py-12 sm:py-16 md:py-24">'
            '<div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-12 gap-8 sm:gap-12 md:gap-16 mb-12 sm:mb-16 text-xs sm:text-sm tracking-tight">'
            '<div class="sm:col-span-2 md:col-span-5"><h3 class="mb-3 sm:mb-4 tracking-tight text-sm sm:text-base">roland moles</h3></div>'
            '<div class="md:col-span-3"><h3 class="mb-3 sm:mb-4 text-white font-bold text-xs">navegación_</h3><div class="space-y-2 text-white/50 text-xs">'
            + "".join(f'<a href="{h}" class="block hover:text-primary transition-colors">{n}</a>' for n, h in NAV) +
            '</div></div><div class="md:col-span-4"><h3 class="mb-4 text-white font-bold text-xs">redes_</h3><div class="space-y-2 text-white/50 text-xs">'
            f'<a href="{SITE["instagram"]}" target="_blank" rel="noopener noreferrer" class="block hover:text-primary transition-colors">instagram_</a>'
            f'<a href="{SITE["linkedin"]}" target="_blank" rel="noopener noreferrer" class="block hover:text-primary transition-colors">linkedin_</a>'
            f'<a href="mailto:{e}" class="block hover:text-primary transition-colors">email_</a></div></div></div>'
            '<div class="pt-8 border-t border-white/5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 text-white/20 text-xs tracking-tight">'
            f'<p>© {datetime.date.today().year} roland moles</p><p class="flex items-center gap-2" style="font-size: 10px;">'
            '<a class="hover:text-white/40 transition-colors no-underline" href="/aviso-legal">Aviso legal</a><span aria-hidden="true">·</span>'
            '<a class="hover:text-white/40 transition-colors no-underline" href="/privacidad">Política de privacidad</a><span aria-hidden="true">·</span>'
            '<a class="hover:text-white/40 transition-colors no-underline" href="/cookies">Política de cookies</a></p></div></div></footer>')


def person():
    return {
        "@type": "Person", "@id": SITE["domain"] + "/#person",
        "name": "Roland Moles", "url": SITE["domain"] + "/",
        "image": SITE["domain"] + "/assets/img/retrato.webp",
        "jobTitle": "Guitarrista clásico",
        "description": "Guitarrista clásico andorrano establecido en Barcelona. Interpretación, creación escénica e investigación artística.",
        "email": "mailto:" + SITE["email"],
        "nationality": {"@type": "Country", "name": "Andorra"},
        "address": {"@type": "PostalAddress", "addressLocality": "Barcelona", "addressCountry": "ES"},
        "alumniOf": {"@type": "CollegeOrUniversity", "name": "Conservatori Superior del Liceu"},
        "knowsAbout": ["Guitarra clásica", "Música de cámara", "Creación escénica", "Investigación artística"],
        "sameAs": [SITE["instagram"], SITE["linkedin"]],
    }


def jsonld(path, meta, url):
    graph = [person(), {"@type": "WebSite", "@id": SITE["domain"] + "/#website", "url": SITE["domain"] + "/",
                        "name": "Roland Moles", "inLanguage": "es", "publisher": {"@id": SITE["domain"] + "/#person"}}]
    page = {"@type": "ProfilePage" if meta.get("type") == "profile" else "WebPage", "@id": url + "#webpage",
            "url": url, "name": meta["title"], "description": meta["description"], "inLanguage": "es",
            "isPartOf": {"@id": SITE["domain"] + "/#website"}}
    if path == "/" or meta.get("type") == "profile":
        page["mainEntity"] = {"@id": SITE["domain"] + "/#person"}
    graph.append(page)
    if path != "/":
        crumbs = [("Inicio", "/")]
        segs = path.strip("/").split("/")
        labels = {"proyectos": "Proyectos"}
        acc = ""
        for i, s in enumerate(segs):
            acc += "/" + s
            name = meta["title"].split(" | ")[0].rstrip("_") if i == len(segs) - 1 else labels.get(s, s)
            crumbs.append((name, acc))
        graph.append({"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": SITE["domain"] + (h if h != "/" else "/")}
            for i, (n, h) in enumerate(crumbs)]})
    if meta.get("schema") == "project":
        graph.append({"@type": "CreativeWork", "name": meta["title"].split(" | ")[0].rstrip("_"),
                      "description": meta["description"], "url": url, "inLanguage": "es",
                      "creator": {"@id": SITE["domain"] + "/#person"}})
    if meta.get("schema") == "service":
        graph.append({"@type": "Service", "name": "Guitarra clásica en directo para bodas y eventos",
                      "serviceType": "Música en directo para celebraciones", "description": meta["description"],
                      "provider": {"@id": SITE["domain"] + "/#person"},
                      "areaServed": [{"@type": "Place", "name": "Barcelona"}, {"@type": "Place", "name": "Cataluña"},
                                     {"@type": "Country", "name": "Andorra"}],
                      "url": url})
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, separators=(",", ":"))


CSP = ("default-src 'self'; "
       "script-src 'self' 'sha256-{h}'{gc_js}; "
       "style-src 'self' 'unsafe-inline'; "
       "img-src 'self' data: https://cdnm.heyzine.com{gc_img}; "
       "font-src 'self'; "
       "connect-src 'self' https://formspree.io{gc_img}; "
       "form-action 'self' https://formspree.io; "
       "frame-src https://fauna-rolandmoles.netlify.app https://www.youtube-nocookie.com https://heyzine.com; "
       "object-src 'none'; base-uri 'self'; upgrade-insecure-requests")


def page_html(path, meta, body, css_v, js_v):
    url = SITE["domain"] + (path if path != "/" else "/")
    title, desc = meta["title"], meta["description"]
    img = meta.get("image") or SITE["domain"] + SITE["og_image"]
    if img.startswith("/"):
        img = SITE["domain"] + img
    robots = "noindex, follow" if meta.get("noindex") else "index, follow, max-image-preview:large"
    preload = (f'<link rel="preload" as="image" href="{meta["preload"]}" imagesrcset="{meta["preload_srcset"]}" imagesizes="100vw" fetchpriority="high">\n'
               if meta.get("preload_srcset") else (f'<link rel="preload" as="image" href="{meta["preload"]}" fetchpriority="high">\n' if meta.get("preload") else ""))
    og_type = "profile" if meta.get("type") == "profile" else ("article" if meta.get("schema") == "project" else "website")
    gc = SITE.get("goatcounter")
    gc_url = f"https://{gc}.goatcounter.com" if gc else ""
    csp = CSP.format(h=sha256_b64(INLINE_JS), gc_img=(" " + gc_url) if gc else "", gc_js=" https://gc.zgo.at" if gc else "")
    stats = (f'<script data-goatcounter="{gc_url}/count" async src="https://gc.zgo.at/count.v5.js" '
             'integrity="sha384-atnOLvQb9t+jTSipvd75X2yginT4PjVbqDdlJAmxMm+wYElFmeR6EmLP5bYeoRVQ" crossorigin="anonymous"></script>\n') if gc and not meta.get("noindex") else ""
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{csp}">
<meta name="referrer" content="strict-origin-when-cross-origin">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{url}">
<meta name="author" content="Roland Moles">
<meta name="theme-color" content="#000000">
<meta name="color-scheme" content="dark">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="Roland Moles">
<meta property="og:locale" content="{SITE['locale']}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{img}">
<meta property="og:image:alt" content="Roland Moles, guitarrista clásico">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{img}">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" href="/assets/img/icon-192.png" type="image/png">
<link rel="apple-touch-icon" href="/assets/img/apple-touch-icon.png">
{preload}<link rel="stylesheet" href="/assets/site.css?v={css_v}">
<script>{INLINE_JS}</script>
<script src="/assets/site.js?v={js_v}" defer></script>
{stats}
<script type="application/ld+json">{jsonld(path, meta, url)}</script>
</head>
<body>
<a href="#main" class="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-[60] focus:bg-primary focus:text-black focus:px-4 focus:py-2 text-sm">saltar al contenido</a>
<div class="min-h-screen bg-black text-white">{nav_html(path)}<main id="main">{body}</main>{footer_html()}</div>
</body>
</html>
"""


# ---------------------------------------------------------------- BUILD

def read_page(fp):
    raw = open(fp, encoding="utf-8").read()
    m = re.match(r"\s*<!--meta\s*(\{.*?\})\s*-->\s*", raw, re.S)
    if not m:
        raise SystemExit(f"Falta el bloque meta en {fp}")
    return json.loads(m.group(1)), raw[m.end():].strip()


def file_hash(fp):
    return hashlib.md5(open(fp, "rb").read()).hexdigest()[:8]


def main():
    if os.path.isdir(DIST):
        shutil.rmtree(DIST)
    os.makedirs(DIST)
    # estáticos
    shutil.copytree(os.path.join(ROOT, "assets"), os.path.join(DIST, "assets"))
    for f in os.listdir(os.path.join(ROOT, "static")):
        shutil.copy(os.path.join(ROOT, "static", f), DIST)
    shutil.copy(os.path.join(SRC, "partials", "site.js"), os.path.join(DIST, "assets", "site.js"))

    pages = []
    pdir = os.path.join(SRC, "pages")
    for dp, _, files in os.walk(pdir):
        for f in sorted(files):
            if f.endswith(".html"):
                fp = os.path.join(dp, f)
                rel = os.path.relpath(fp, pdir)[:-5].replace(os.sep, "/")
                path = "/" if rel == "index" else "/" + rel
                pages.append((path, fp))

    # orden de proyectos = el de la lista de /proyectos (para "siguiente proyecto_")
    order = re.findall(r"\{\{project_row:\s*(\S+)\s*\|", open(os.path.join(pdir, "proyectos.html"), encoding="utf-8").read())
    titles = {}
    for path, fp in pages:
        if path in order:
            titles[path] = read_page(fp)[0]["title"].split(" | ")[0]
    nexts = {p: (order[(i + 1) % len(order)], titles.get(order[(i + 1) % len(order)], "")) for i, p in enumerate(order)}

    # primera pasada: HTML sin estilos para que Tailwind detecte las clases
    js_v = file_hash(os.path.join(DIST, "assets", "site.js"))
    rendered = []
    for path, fp in pages:
        meta, body = read_page(fp)
        if path in nexts:
            meta["_next"] = nexts[path]
        body = expand(body, meta)
        rendered.append((path, meta, body))
        out = os.path.join(DIST, "index.html" if path == "/" else path.strip("/") + ".html")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, "w", encoding="utf-8").write(page_html(path, meta, body, "0", js_v))

    # CSS con Tailwind
    subprocess.run(["npx", "@tailwindcss/cli", "-i", os.path.join(SRC, "input.css"),
                    "-o", os.path.join(DIST, "assets", "site.css"), "--minify"],
                   cwd=ROOT, check=True, capture_output=True)
    css_v = file_hash(os.path.join(DIST, "assets", "site.css"))

    # segunda pasada con versión de CSS (evita cachés antiguas tras cada cambio)
    for path, meta, body in rendered:
        out = os.path.join(DIST, "index.html" if path == "/" else path.strip("/") + ".html")
        open(out, "w", encoding="utf-8").write(page_html(path, meta, body, css_v, js_v))

    # 404
    meta404 = {"title": "Página no encontrada | Roland Moles", "description": "Esta página no existe.", "noindex": True}
    body404 = ('<div class="min-h-screen pt-24 sm:pt-32 pb-16 sm:pb-24"><div class="max-w-[1200px] mx-auto px-4 sm:px-8 md:px-16">'
               '<div data-r="up" data-load style="--y:20px;--dur:.8s"><h1 class="text-4xl sm:text-5xl md:text-6xl mb-12 tracking-tight">404_</h1>'
               '<p class="text-base sm:text-lg text-white/50 tracking-tight max-w-md mb-12">esta página no existe o ha cambiado de sitio.</p>'
               '<a class="inline-block px-8 py-4 bg-white/10 text-white hover:bg-primary hover:text-black transition-all text-sm tracking-tight" href="/">volver al inicio_</a></div></div></div>')
    open(os.path.join(DIST, "404.html"), "w", encoding="utf-8").write(page_html("/404", meta404, body404, css_v, js_v))

    # sitemap y robots
    today = datetime.date.today().isoformat()
    urls = []
    for path, meta, _ in sorted(rendered, key=lambda r: (r[0] != "/", r[0])):
        if meta.get("noindex"):
            continue
        prio = "1.0" if path == "/" else ("0.8" if path.count("/") == 1 else "0.6")
        urls.append(f"  <url><loc>{SITE['domain']}{path if path != '/' else '/'}</loc><lastmod>{today}</lastmod><priority>{prio}</priority></url>")
    open(os.path.join(DIST, "sitemap.xml"), "w").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(urls) + "\n</urlset>\n")
    open(os.path.join(DIST, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\n\nSitemap: {SITE['domain']}/sitemap.xml\n")
    print(f"OK: {len(rendered)} páginas en docs/")


if __name__ == "__main__":
    main()
    if "--serve" in sys.argv:
        os.chdir(DIST)
        subprocess.run([sys.executable, os.path.join(ROOT, "serve.py")])
