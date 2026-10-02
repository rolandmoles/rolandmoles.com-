/* rolandmoles.com — interacciones del sitio (sin dependencias) */
(function () {
  "use strict";
  window.__rm = true;
  var html = document.documentElement;

  /* ---------- Animaciones de entrada ---------- */
  function reveal(el) { el.classList.add("in"); }
  var els = document.querySelectorAll("[data-r], [data-line]");
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var observers = {};
  function observerFor(margin) {
    if (!observers[margin]) {
      observers[margin] = new IntersectionObserver(function (entries, obs) {
        entries.forEach(function (e) {
          if (e.isIntersecting) { reveal(e.target); obs.unobserve(e.target); }
        });
      }, { rootMargin: "0px 0px " + margin + " 0px", threshold: 0 });
    }
    return observers[margin];
  }
  requestAnimationFrame(function () {
    els.forEach(function (el) {
      if (reduce || !("IntersectionObserver" in window) || el.hasAttribute("data-load")) {
        requestAnimationFrame(function () { reveal(el); });
      } else {
        observerFor(el.getAttribute("data-m") || "0px").observe(el);
      }
    });
  });

  /* ---------- Menú ---------- */
  var btn = document.getElementById("menu-btn");
  var menu = document.getElementById("menu");
  function setMenu(open) {
    html.classList.toggle("menu-open", open);
    btn.textContent = open ? "cerrar_" : "menú_";
    btn.setAttribute("aria-expanded", open ? "true" : "false");
    if (open) { var a = menu.querySelector("a"); if (a) setTimeout(function () { a.focus({ preventScroll: true }); }, 50); }
  }
  if (btn && menu) {
    btn.addEventListener("click", function () { setMenu(!html.classList.contains("menu-open")); });
    menu.addEventListener("click", function () { setMenu(false); });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && html.classList.contains("menu-open")) { setMenu(false); btn.focus(); }
    });
  }

  /* ---------- Bloques enteros clicables (data-href) ---------- */
  document.querySelectorAll("[data-href]").forEach(function (el) {
    el.addEventListener("click", function (e) {
      if (e.target.closest("a, button, input, textarea")) return;
      window.location.href = el.getAttribute("data-href");
    });
  });

  /* ---------- Botón volver (vuelve a la página anterior si es de este sitio) ---------- */
  document.querySelectorAll("[data-back]").forEach(function (a) {
    a.addEventListener("click", function (e) {
      try {
        if (document.referrer && new URL(document.referrer).origin === location.origin && history.length > 1) {
          e.preventDefault(); history.back();
        }
      } catch (_) {}
    });
  });

  /* ---------- Pestañas de media ---------- */
  var tabs = document.querySelectorAll("[data-tab]");
  var ON = ["text-primary", "border-b", "border-primary"], OFF = ["text-white/40", "hover:text-white/70"];
  function showTab(name, push) {
    tabs.forEach(function (t) {
      var active = t.getAttribute("data-tab") === name;
      t.setAttribute("aria-selected", active ? "true" : "false");
      ON.forEach(function (c) { t.classList.toggle(c, active); });
      OFF.forEach(function (c) { t.classList.toggle(c, !active); });
      var panel = document.getElementById("tab-" + t.getAttribute("data-tab"));
      if (!panel) return;
      if (active) {
        panel.hidden = false;
        panel.style.opacity = "0";
        requestAnimationFrame(function () {
          panel.style.transition = "opacity .5s ease";
          panel.style.opacity = "1";
          panel.querySelectorAll("[data-r]").forEach(function (el, i) {
            el.style.setProperty("--delay", (i * 0.05) + "s"); el.classList.add("in");
          });
        });
      } else { panel.hidden = true; }
    });
    if (push) history.replaceState(null, "", name === "videos" ? location.pathname : "#" + name);
  }
  if (tabs.length) {
    tabs.forEach(function (t) { t.addEventListener("click", function () { showTab(t.getAttribute("data-tab"), true); }); });
    var h = location.hash.replace("#", "");
    if (h === "fotos" || h === "prensa") showTab(h, false);
  }

  /* ---------- Galería ampliada ---------- */
  var lb = document.getElementById("lightbox");
  if (lb) {
    var items = Array.prototype.slice.call(document.querySelectorAll("[data-lb]"));
    var img = lb.querySelector("[data-lb-img]"), count = lb.querySelector("[data-lb-count]");
    var prev = lb.querySelector("[data-lb-prev]"), next = lb.querySelector("[data-lb-next]");
    var idx = 0, opener = null;
    function show(i) {
      idx = i;
      img.style.opacity = "0";
      img.onload = function () { img.style.opacity = "1"; };
      img.src = items[i].getAttribute("data-lb");
      count.textContent = (i + 1) + " / " + items.length;
      prev.hidden = i === 0; next.hidden = i === items.length - 1;
    }
    function open(i) { opener = items[i]; lb.hidden = false; html.style.overflow = "hidden"; show(i); lb.querySelector("[data-lb-close]").focus(); }
    function close() { lb.hidden = true; html.style.overflow = ""; img.src = ""; if (opener) opener.focus(); }
    items.forEach(function (el, i) { el.addEventListener("click", function () { open(i); }); });
    lb.addEventListener("click", close);
    img.addEventListener("click", function (e) { e.stopPropagation(); });
    prev.addEventListener("click", function (e) { e.stopPropagation(); if (idx > 0) show(idx - 1); });
    next.addEventListener("click", function (e) { e.stopPropagation(); if (idx < items.length - 1) show(idx + 1); });
    document.addEventListener("keydown", function (e) {
      if (lb.hidden) return;
      if (e.key === "Escape") close();
      if (e.key === "ArrowLeft" && idx > 0) show(idx - 1);
      if (e.key === "ArrowRight" && idx < items.length - 1) show(idx + 1);
    });
  }

  /* ---------- Formularios (Formspree) ---------- */
  var EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  function clean(v) { return (v || "").trim().replace(/[<>]/g, ""); }

  document.querySelectorAll("form[data-form]").forEach(function (form) {
    var kind = form.getAttribute("data-form");
    var box = form.parentNode;
    var tOk = box.querySelector("template[data-ok]"), tErr = box.querySelector("template[data-err]");
    var submit = form.querySelector("[type=submit]");
    var label = submit.textContent;
    var msg = null;

    function say(tpl, text) {
      if (msg) { msg.remove(); msg = null; }
      if (!tpl) return;
      msg = tpl.content.firstElementChild.cloneNode(true);
      if (text) msg.textContent = text;
      msg.setAttribute("role", "status");
      form.appendChild(msg);
    }
    function fail(text) {
      say(tErr, kind === "contacto" ? text : null);
      submit.disabled = false; submit.textContent = label;
    }

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      say(null);
      var data = {};
      new FormData(form).forEach(function (v, k) { data[k] = typeof v === "string" ? v : ""; });
      if (data._gotcha) return; // antispam: campo trampa que solo rellenan los bots
      delete data._gotcha;

      if (kind === "contacto") {
        data.name = clean(data.name); data.email = clean(data.email); data.message = clean(data.message);
        if (!data.name || !data.email || !data.message) return fail("todos los campos son obligatorios");
        if (!EMAIL_RE.test(data.email)) return fail("email no válido");
        if (data.message.length < 10) return fail("el mensaje debe tener al menos 10 caracteres");
        data._subject = "Nuevo mensaje desde rolandmoles.com";
      } else {
        data.email = clean(data.email);
        if (!EMAIL_RE.test(data.email)) { form.querySelector("input[type=email]").reportValidity(); return; }
        submit.textContent = "enviando...";
      }

      submit.disabled = true;
      fetch(form.action, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Accept": "application/json" },
        body: JSON.stringify(data)
      }).then(function (r) {
        if (!r.ok) throw new Error(r.status);
        if (kind === "contacto") {
          form.reset(); submit.disabled = false; submit.textContent = label;
          say(tOk);
        } else {
          var sent = box.querySelector("[data-sent]");
          form.hidden = true; if (sent) sent.hidden = false;
        }
      }).catch(function () { fail("error al enviar. intenta de nuevo"); });
    });
  });
})();
