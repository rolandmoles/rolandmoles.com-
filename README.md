# rolandmoles.com

Web personal de Roland Moles, guitarrista clásico. Sitio estático publicado con GitHub Pages.

## Cómo está organizado

- `src/pages/` — una página por archivo. Las rutas siguen la carpeta: `src/pages/proyectos/fauna.html` → `/proyectos/fauna`.
  Cada página empieza con un bloque `<!--meta {...} -->` con título y descripción (lo que sale en Google).
- `src/partials/` — JavaScript del sitio y piezas reutilizables.
- `src/input.css` — tema visual (colores, tipografía, animaciones).
- `assets/img/` — imágenes optimizadas (WebP, sin metadatos).
- `build.py` — genera la web final en `docs/` (cabecera, menú, pie, SEO, sitemap).
- `docs/` — **web publicada**. No se edita a mano: se regenera con `python3 build.py`.

## Ajustes generales

En `build.py`, bloque `SITE`: correo público, formulario (Formspree), enlace de compra del libro, Instagram y estadísticas (GoatCounter).

## Atajos dentro de las páginas

```
{{project_row: /ruta | año | [estado] | Título_ | categoría | texto}}
{{row: etiqueta | texto ¶ con saltos de línea}}
{{collab: Nombre | rol}}
{{press_row: url | año | medio | Titular_ | texto}}
{{photo: foto-1 | texto alternativo}}
```

## Publicar un cambio

```
npm install
python3 build.py
git add -A && git commit -m "Describe el cambio" && git push
```
