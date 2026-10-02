import http.server, threading, functools, os, json
from playwright.sync_api import sync_playwright
DIST = os.path.join(os.path.dirname(__file__), "..", "docs")
class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a): pass
    def send_head(self):
        p = self.translate_path(self.path.split('?')[0].split('#')[0])
        if os.path.exists(p.rstrip("/") + ".html") and not os.path.isfile(p):
            self.path = self.path.split('?')[0].rstrip("/") + ".html"
        elif not os.path.exists(p):
            self.path = "/404.html"
        return super().send_head()
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 8766), functools.partial(H, directory=DIST))
threading.Thread(target=srv.serve_forever, daemon=True).start()
B="http://127.0.0.1:8766"
routes=['/','/proyectos','/proyectos/fauna','/proyectos/investigacion-tfg-lorca','/ceremonias','/sobre-mi','/media','/contacto','/cookies','/no-existe']
report={}
with sync_playwright() as p:
    b=p.chromium.launch()
    for vw,vh,tag in [(1440,900,'d'),(390,844,'m')]:
        pg=b.new_page(viewport={"width":vw,"height":vh})
        errs=[]
        pg.on("console", lambda m: errs.append(m.type+": "+m.text) if m.type in ("error","warning") else None)
        pg.on("pageerror", lambda e: errs.append("pageerror: "+str(e)))
        for r in routes:
            errs.clear()
            pg.goto(B+r, wait_until="networkidle"); 
            # desplazar hasta abajo para disparar animaciones
            h=pg.evaluate("document.body.scrollHeight")
            for y in range(0,h,400): pg.evaluate(f"scrollTo(0,{y})"); pg.wait_for_timeout(40)
            pg.wait_for_timeout(900); pg.evaluate("scrollTo(0,0)"); pg.wait_for_timeout(300)
            hidden=pg.evaluate("[...document.querySelectorAll('[data-r]')].filter(e=>!e.closest('[hidden]') && getComputedStyle(e).opacity<0.99).length")
            broken=pg.evaluate("[...document.images].filter(i=>i.complete && i.naturalWidth===0 && !i.closest('[hidden]') && i.getAttribute('src')).map(i=>i.src)")
            name=(r.strip('/').replace('/','_') or 'home')+'_'+tag
            pg.screenshot(path=f"tools/shots/{name}.png", full_page=True)
            report[name]={"hiddenAfterScroll":hidden,"brokenImgs":broken,"console":[e for e in errs if 'goatcounter' not in e and 'gc.zgo.at' not in e and 'heyzine' not in e and 'netlify' not in e][:5]}
        pg.close()
    # interacciones
    pg=b.new_page(viewport={"width":1440,"height":900})
    pg.goto(B+"/"); pg.click("#menu-btn"); pg.wait_for_timeout(600)
    report["menu_open"]={"label":pg.inner_text("#menu-btn"),"visible":pg.evaluate("getComputedStyle(document.getElementById('menu')).visibility")}
    pg.screenshot(path="tools/shots/menu_d.png")
    pg.keyboard.press("Escape"); pg.wait_for_timeout(400)
    report["menu_closed"]=pg.evaluate("getComputedStyle(document.getElementById('menu')).visibility")
    pg.goto(B+"/media"); pg.click("[data-tab=fotos]"); pg.wait_for_timeout(700)
    report["tab_fotos_visible"]=pg.is_visible("#tab-fotos")
    pg.screenshot(path="tools/shots/media_fotos_d.png", full_page=True)
    pg.click("[data-lb] >> nth=3"); pg.wait_for_timeout(800)
    report["lightbox"]={"open":pg.is_visible("#lightbox"),"count":pg.inner_text("[data-lb-count]"),"imgw":pg.evaluate("document.querySelector('[data-lb-img]').naturalWidth")}
    pg.screenshot(path="tools/shots/lightbox_d.png")
    pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(300); report["lightbox_next"]=pg.inner_text("[data-lb-count]")
    pg.keyboard.press("Escape")
    pg.click("[data-tab=prensa]"); pg.wait_for_timeout(700); report["tab_prensa_rows"]=pg.evaluate("document.querySelectorAll('#tab-prensa a').length")
    pg.goto(B+"/contacto"); pg.fill("#name","Prueba"); pg.fill("#email","no-es-email"); pg.fill("#message","hola hola hola"); pg.click("button[type=submit]"); pg.wait_for_timeout(300)
    report["contact_validation"]=pg.inner_text("form[data-form] > p:last-child")
    b.close()
print(json.dumps(report,ensure_ascii=False,indent=1))
