"""Optimiza las fotos de originals/ -> assets/img/ (WebP, sin metadatos ni GPS)."""
import os
from PIL import Image, ImageOps
import pillow_heif
pillow_heif.register_heif_opener()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC, OUT = os.path.join(ROOT, "originals"), os.path.join(ROOT, "assets", "img")
os.makedirs(OUT, exist_ok=True)

def load(name):
    im = ImageOps.exif_transpose(Image.open(os.path.join(SRC, name)))
    return im.convert("RGB")

def fit(im, long_side=None, short_side=None, width=None):
    w, h = im.size
    if width: s = width / w
    elif long_side: s = long_side / max(w, h)
    else: s = short_side / min(w, h)
    s = min(s, 1)
    return im.resize((round(w * s), round(h * s)), Image.LANCZOS)

def save(im, name, q):
    p = os.path.join(OUT, name)
    im.save(p, "WEBP", quality=q, method=6)  # sin exif = sin GPS
    print(f"{name:22s} {im.size[0]}x{im.size[1]}  {os.path.getsize(p)//1024} KB")

hero = load("hero.jpg")
# portada: siempre en gris y al 15 % de opacidad -> se puede comprimir mucho sin que se note
g = ImageOps.grayscale(hero).convert("RGB")
save(fit(g, width=1920), "hero.webp", 62)
save(fit(g, width=960), "hero-960.webp", 62)
save(fit(g, width=900), "retrato.webp", 72)

fotos = {"foto-1": "foto-1.jpg", "foto-2": "foto-2.jpg", "foto-3": "foto-3.jpg", "foto-4": "foto-4.jpg",
         "foto-5": "foto-5.jpg", "foto-6": "foto-6.jpg", "foto-7": "hero.jpg", "foto-8": "foto-8.jpg"}
for out, src in fotos.items():
    im = hero if src == "hero.jpg" else load(src)
    save(fit(im, short_side=800), out + ".webp", 74)
    save(fit(im, long_side=2000), out + "-full.webp", 80)

# iconos a partir del logo
logo = load("logo.jpg")
w, h = logo.size; s = min(w, h)
sq = logo.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s))
sq.resize((180, 180), Image.LANCZOS).save(os.path.join(OUT, "apple-touch-icon.png"))
sq.resize((192, 192), Image.LANCZOS).save(os.path.join(OUT, "icon-192.png"))
sq.resize((512, 512), Image.LANCZOS).save(os.path.join(OUT, "icon-512.png"))
sq.save(os.path.join(ROOT, "static", "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)])
print("iconos ok")
