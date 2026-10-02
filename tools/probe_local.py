import json, sys, http.server, threading, functools, os
from playwright.sync_api import sync_playwright
DIST = os.path.join(os.path.dirname(__file__), "..", "docs")
W = int(sys.argv[1]) if len(sys.argv) > 1 else 743
class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a): pass
    def send_head(self):
        p = self.translate_path(self.path)
        if os.path.exists(p.rstrip("/") + ".html") and not os.path.isfile(p):
            self.path = self.path.rstrip("/")
            self.path += ".html"
        return super().send_head()
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 8765), functools.partial(H, directory=DIST))
threading.Thread(target=srv.serve_forever, daemon=True).start()
probe = open(os.path.join(os.path.dirname(__file__), "styleprobe.js")).read()
routes=['/','/proyectos','/proyectos/investigacion-tfg-lorca','/proyectos/danzas-y-nanas','/proyectos/ecos-del-sur','/proyectos/clarobscur','/proyectos/fauna','/proyectos/trio-3y3','/proyectos/sinestesia-sonora','/proyectos/la-guitarra-a-traves-del-temps','/proyectos/nit-dels-museus','/ceremonias','/sobre-mi','/media','/contacto','/aviso-legal','/privacidad','/cookies']
out={"w":W}
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={"width":W,"height":900})
    for r in routes:
        pg.goto("http://127.0.0.1:8765"+r); pg.wait_for_timeout(300)
        out[r]=pg.evaluate(probe)["styles"]
    b.close()
json.dump(out, open(os.path.join(os.path.dirname(__file__),"probe_local.json"),"w"), ensure_ascii=False)
print("ok")
