// Recoge estilos calculados de los elementos con texto para comparar original vs. nuevo.
(() => {
  const props = ["fontSize", "fontWeight", "lineHeight", "letterSpacing", "color", "fontFamily",
    "paddingTop", "paddingLeft", "marginTop", "marginBottom", "backgroundColor", "textTransform", "maxWidth", "borderTopWidth", "borderLeftWidth"];
  const out = {};
  const root = document.querySelector("main") || document.querySelector("#container .tailwind > div > div:nth-of-type(1)") || document.body;
  const all = document.querySelectorAll("h1,h2,h3,p,a,span,button,label,li,input,textarea,div");
  all.forEach((el) => {
    if (el.closest("nav,#menu,footer,[aria-hidden=true],#lightbox,[hidden],.sr-only")) return;
    const direct = [...el.childNodes].filter((n) => n.nodeType === 3).map((n) => n.textContent).join("").trim();
    if (!direct && !["INPUT", "TEXTAREA"].includes(el.tagName)) return;
    const key = el.tagName + ":" + (direct || el.getAttribute("placeholder") || el.id).slice(0, 50);
    if (out[key]) return;
    const cs = getComputedStyle(el);
    const o = {};
    props.forEach((p) => (o[p] = cs[p]));
    out[key] = o;
  });
  return { w: innerWidth, n: Object.keys(out).length, styles: out };
})()
