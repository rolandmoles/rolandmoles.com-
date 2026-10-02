#!/bin/sh
# Prepara la copia local de la web (carpeta "rolandmoles.com (web)" en iCloud > RMC > SOCIAL MEDIA > WEB).
# Después de cada publicación, Claude copia /mnt/user-data/outputs/webcopy a esa carpeta.
set -e
cd "$(dirname "$0")/.."
OUT=/mnt/user-data/outputs/webcopy
rm -rf "$OUT/web publicada" "$OUT/codigo fuente"
mkdir -p "$OUT/web publicada" "$OUT/codigo fuente/assets"
cp -r docs/. "$OUT/web publicada/" && rm -f "$OUT/web publicada/.nojekyll"
cp -r src build.py README.md package.json static "$OUT/codigo fuente/"
cp -r assets/img "$OUT/codigo fuente/assets/"
rm -f "$OUT/codigo fuente/static/.nojekyll"
echo "Copia preparada en $OUT"
