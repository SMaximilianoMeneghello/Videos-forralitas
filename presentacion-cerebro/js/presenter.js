// ============================================================
//  PRESENTADOR — motor de diapositivas + conexión con el control
// ============================================================
(function () {
  const CFG = window.CONFIG;
  const SL = window.SLIDES;
  const N = SL.length;
  const $ = (s, r = document) => r.querySelector(s);
  const root = document.documentElement;

  const store = {
    get(k, d) { try { const v = localStorage.getItem("tcm." + k); return v === null ? d : JSON.parse(v); } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem("tcm." + k, JSON.stringify(v)); } catch (e) {} },
  };

  const stage = $("#stage");
  const shakeEl = $("#shake");
  const slidesEl = $("#slides");
  const flash = $("#fx-flash");
  const sweep = $("#fx-sweep");

  let idx = -1;
  let step = 0;
  let cur = null; // {el, ctx, s}
  let trans = null;
  let started = false;
  let startTime = 0;
  let lite = store.get("lite", false);

  root.style.setProperty("--h", 265);

  // ---------------------------------------------------------- escala del escenario
  function fit() {
    const s = Math.min(window.innerWidth / 1600, window.innerHeight / 900);
    stage.style.transform = `translate(-50%, -50%) scale(${s})`;
  }
  window.addEventListener("resize", fit);
  fit();

  function setLite(v) {
    lite = v;
    store.set("lite", v);
    document.body.classList.toggle("lite", v);
    window.BG && BG.setLite(v);
  }
  setLite(lite);

  // ---------------------------------------------------------- utilidades
  const blur = (px) => (lite ? {} : { filter: `blur(${px}px)` });

  function splitLetters(el) {
    const walk = (node) => {
      Array.from(node.childNodes).forEach((n) => {
        if (n.nodeType === 3) {
          const frag = document.createDocumentFragment();
          n.textContent.split(/(\s+)/).forEach((word) => {
            if (!word) return;
            if (/^\s+$/.test(word)) { frag.appendChild(document.createTextNode(" ")); return; }
            const w = document.createElement("span");
            w.className = "word";
            for (const ch of word) {
              const c = document.createElement("span");
              c.className = "ch";
              c.textContent = ch;
              w.appendChild(c);
            }
            frag.appendChild(w);
          });
          n.replaceWith(frag);
        } else if (n.nodeType === 1 && n.tagName !== "BR") walk(n);
      });
    };
    walk(el);
  }

  function fmt(n) { return Math.round(n).toLocaleString("en-US"); }

  function runCounters(scope, delay, tweens) {
    const list = scope.matches && scope.matches("[data-count]") ? [scope] : [];
    scope.querySelectorAll("[data-count]").forEach((c) => list.push(c));
    list.forEach((c) => {
      const o = { v: 0 };
      const target = parseFloat(c.dataset.count);
      tweens.push(gsap.to(o, {
        v: target, duration: target > 1000 ? 2.6 : 1.8, delay: delay + 0.2, ease: "expo.out",
        onUpdate: () => { c.textContent = fmt(o.v); },
      }));
    });
  }

  // Animación de entrada de un elemento según data-in
  function reveal(el, anim, delay, tweens) {
    anim = anim || el.dataset.in || "up";
    delay = delay || 0;
    gsap.set(el, { visibility: "visible" });
    let tw;
    const E = "expo.out";
    switch (anim) {
      case "letters": {
        const chars = el.querySelectorAll(".ch");
        gsap.set(el, { opacity: 1 });
        tw = gsap.fromTo(chars,
          { opacity: 0, y: 70, rotationX: -90, ...blur(12) },
          { opacity: 1, y: 0, rotationX: 0, ...(lite ? {} : { filter: "blur(0px)" }), duration: 1.5, stagger: 0.035, delay, ease: E, transformPerspective: 600 });
        break;
      }
      case "slowmo":
        tw = gsap.fromTo(el, { opacity: 0, scale: 1.18, ...blur(18) }, { opacity: 1, scale: 1, ...(lite ? {} : { filter: "blur(0px)" }), duration: 2.8, delay, ease: "power2.out" });
        break;
      case "blur":
        tw = gsap.fromTo(el, { opacity: 0, ...blur(30) }, { opacity: 1, ...(lite ? {} : { filter: "blur(0px)" }), duration: 1.6, delay, ease: "power2.out" });
        break;
      case "zoom":
        tw = gsap.fromTo(el, { opacity: 0, scale: 0.3 }, { opacity: 1, scale: 1, duration: 1.3, delay, ease: E });
        break;
      case "pop":
        tw = gsap.fromTo(el, { opacity: 0, scale: 0.5 }, { opacity: 1, scale: 1, duration: 0.8, delay, ease: "back.out(2.2)", onStart: () => SFX.pop() });
        break;
      case "stamp":
        tw = gsap.fromTo(el, { opacity: 0, scale: 3.2, rotation: -16 }, {
          opacity: 1, scale: 1, rotation: -6, duration: 0.55, delay, ease: "power4.in",
          onComplete: () => { SFX.reveal(); shake(14); flashOnce(0.25); },
        });
        break;
      case "flip":
        tw = gsap.fromTo(el, { opacity: 0, rotationY: 95, transformPerspective: 1000 }, { opacity: 1, rotationY: 0, duration: 1.4, delay, ease: E, onStart: () => SFX.whoosh(0.5) });
        break;
      case "left":
        tw = gsap.fromTo(el, { opacity: 0, x: -160 }, { opacity: 1, x: 0, duration: 1.3, delay, ease: E });
        break;
      case "right":
        tw = gsap.fromTo(el, { opacity: 0, x: 160 }, { opacity: 1, x: 0, duration: 1.3, delay, ease: E });
        break;
      case "down":
        tw = gsap.fromTo(el, { opacity: 0, y: -70 }, { opacity: 1, y: 0, duration: 1.2, delay, ease: E });
        break;
      case "fade":
        tw = gsap.fromTo(el, { opacity: 0 }, { opacity: 1, duration: 1.2, delay, ease: "power1.out" });
        break;
      case "draw": {
        const len = el.getTotalLength ? el.getTotalLength() : 1000;
        gsap.set(el, { opacity: 1, strokeDasharray: len, strokeDashoffset: len });
        tw = gsap.to(el, { strokeDashoffset: 0, duration: 1.6, delay, ease: "power2.inOut" });
        break;
      }
      default: // up
        tw = gsap.fromTo(el, { opacity: 0, y: 60 }, { opacity: 1, y: 0, duration: 1.2, delay, ease: E });
    }
    tweens.push(tw);
    runCounters(el, delay, tweens);
    return tw;
  }

  function shake(px = 10) {
    if (lite) return;
    gsap.fromTo(shakeEl, { x: 0, y: 0 }, {
      duration: 0.5, ease: "none",
      keyframes: [{ x: -px, y: px * 0.5 }, { x: px * 0.8, y: -px * 0.6 }, { x: -px * 0.5, y: px * 0.3 }, { x: px * 0.3, y: 0 }, { x: 0, y: 0 }],
    });
  }

  function flashOnce(op = 0.7, d = 0.6) {
    gsap.fromTo(flash, { opacity: op }, { opacity: 0, duration: d, ease: "power2.out" });
  }

  // ---------------------------------------------------------- contexto por diapositiva
  function makeCtx(el) {
    const timers = [], rafs = [], tweens = [];
    const ctx = {
      el, data: {}, lite, sfx: SFX,
      $: (s) => el.querySelector(s),
      $$: (s) => Array.from(el.querySelectorAll(s)),
      after(ms, fn) { const id = setTimeout(fn, ms); timers.push(() => clearTimeout(id)); return id; },
      every(ms, fn) { const id = setInterval(fn, ms); timers.push(() => clearInterval(id)); return id; },
      raf(fn) {
        let on = true, id;
        const loop = (t) => { if (!on) return; fn(t); id = requestAnimationFrame(loop); };
        id = requestAnimationFrame(loop);
        const stop = () => { on = false; cancelAnimationFrame(id); };
        rafs.push(stop);
        return stop;
      },
      tween(t, a, b) { const tw = b ? gsap.fromTo(t, a, b) : gsap.to(t, a); tweens.push(tw); return tw; },
      reveal(target, anim, delay) { return reveal(target, anim, delay, tweens); },
      shake, flash: flashOnce,
      // agrega una clase al <body> mientras dure la diapositiva (ej: sacar el viñeteado en pantallas blancas)
      bodyClass(c) { document.body.classList.add(c); timers.push(() => document.body.classList.remove(c)); },
      cleanup() {
        timers.forEach((f) => f());
        rafs.forEach((f) => f());
        tweens.forEach((t) => t.kill());
        timers.length = rafs.length = tweens.length = 0;
      },
      tweens,
    };
    return ctx;
  }

  function buildSlide(s) {
    const el = document.createElement("section");
    el.className = "slide";
    el.id = "s-" + s.id;
    el.innerHTML = s.html({ presentador: escapeHtml(CFG.presentador), materia: escapeHtml(CFG.materia || "") });
    el.querySelectorAll('[data-in="letters"]').forEach(splitLetters);
    el.querySelectorAll("[data-in]").forEach((e) => { if (e.dataset.in !== "draw") gsap.set(e, { visibility: "hidden" }); });
    el.querySelectorAll('[data-in="draw"]').forEach((e) => {
      const len = e.getTotalLength ? e.getTotalLength() : 1000;
      gsap.set(e, { strokeDasharray: len, strokeDashoffset: len });
    });
    return el;
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }

  // ---------------------------------------------------------- transiciones
  const TRANS = {
    dive(o, n, tl) {
      if (o) tl.to(o, { scale: 1.7, opacity: 0, ...blur(16), duration: 0.8, ease: "power3.in" }, 0);
      tl.fromTo(n, { scale: 0.55, opacity: 0, ...blur(16) }, { scale: 1, opacity: 1, ...(lite ? {} : { filter: "blur(0px)" }), duration: 1.4, ease: "expo.out" }, 0.45);
      tl.call(() => SFX.whoosh(1), null, 0);
      tl.call(() => flashOnce(0.35, 0.8), null, 0.5);
    },
    warp(o, n, tl, dir) {
      const d = dir || 1;
      if (o) tl.to(o, { rotationY: -75 * d, x: -700 * d, z: -500, opacity: 0, duration: 1, ease: "power3.inOut" }, 0);
      tl.fromTo(n, { rotationY: 75 * d, x: 700 * d, z: -500, opacity: 0 }, { rotationY: 0, x: 0, z: 0, opacity: 1, duration: 1.3, ease: "expo.out" }, 0.35);
      tl.call(() => SFX.whoosh(0.9), null, 0);
    },
    sweep(o, n, tl) {
      tl.fromTo(sweep, { xPercent: -120, opacity: 1 }, { xPercent: 260, duration: 1.2, ease: "power2.inOut" }, 0);
      if (o) tl.to(o, { opacity: 0, x: -80, duration: 0.7, ease: "power2.in" }, 0.1);
      tl.fromTo(n, { clipPath: "inset(0% 100% 0% 0%)", opacity: 1 }, { clipPath: "inset(0% 0% 0% 0%)", duration: 1.05, ease: "power2.inOut" }, 0.12);
      tl.set(sweep, { opacity: 0 });
      tl.call(() => SFX.whoosh(0.8), null, 0);
    },
    glitch(o, n, tl) {
      tl.call(() => { SFX.glitch(); document.body.classList.add("glitching"); }, null, 0);
      if (o) {
        tl.to(o, { x: 30, skewX: 18, duration: 0.05 }, 0)
          .to(o, { x: -40, skewX: -12, opacity: 0.6, duration: 0.05 })
          .to(o, { x: 15, scaleY: 1.06, duration: 0.05 })
          .to(o, { opacity: 0, duration: 0.05 });
      }
      tl.call(() => flashOnce(0.5, 0.25), null, 0.2);
      tl.fromTo(n, { opacity: 0, x: -30, skewX: -20 }, { opacity: 1, x: 20, skewX: 10, duration: 0.06 }, 0.22)
        .to(n, { x: -12, skewX: -6, duration: 0.06 })
        .to(n, { x: 6, skewX: 0, opacity: 0.7, duration: 0.06 })
        .to(n, { x: 0, opacity: 1, duration: 0.3, ease: "power2.out" });
      tl.call(() => { document.body.classList.remove("glitching"); SFX.glitch(); }, null, 0.6);
    },
    burst(o, n, tl) {
      tl.call(() => { BG.burst(1); SFX.boom(0.5); SFX.whoosh(1.2); }, null, 0);
      if (o) tl.to(o, { scale: 0.85, opacity: 0, duration: 0.5, ease: "power2.in" }, 0);
      tl.call(() => flashOnce(0.85, 1), null, 0.4);
      tl.fromTo(n, { scale: 1.5, opacity: 0 }, { scale: 1, opacity: 1, duration: 1.6, ease: "expo.out" }, 0.42);
    },
    iris(o, n, tl) {
      if (o) tl.to(o, { scale: 0.92, opacity: 0.25, duration: 1, ease: "power2.inOut" }, 0);
      tl.fromTo(n, { clipPath: "circle(0% at 50% 50%)" }, { clipPath: "circle(80% at 50% 50%)", duration: 1.3, ease: "expo.inOut" }, 0.05);
      tl.call(() => SFX.whoosh(0.9), null, 0);
    },
    rise(o, n, tl) {
      if (o) tl.to(o, { yPercent: -30, opacity: 0, duration: 0.8, ease: "power3.in" }, 0);
      tl.fromTo(n, { yPercent: 40, opacity: 0 }, { yPercent: 0, opacity: 1, duration: 1.2, ease: "expo.out" }, 0.3);
      tl.call(() => SFX.whoosh(0.8), null, 0);
    },
    back(o, n, tl) {
      if (o) tl.to(o, { opacity: 0, x: 120, duration: 0.45, ease: "power2.in" }, 0);
      tl.fromTo(n, { opacity: 0, x: -120 }, { opacity: 1, x: 0, duration: 0.8, ease: "expo.out" }, 0.25);
      tl.call(() => SFX.whoosh(0.5), null, 0);
    },
  };

  // ---------------------------------------------------------- navegación
  function go(i, opts = {}) {
    if (i < 0 || i >= N) return;
    if (trans) trans.progress(1);
    const s = SL[i];
    const old = cur;
    const el = buildSlide(s);
    slidesEl.appendChild(el);
    const ctx = makeCtx(el);
    cur = { el, ctx, s };
    idx = i;
    step = 0;
    store.set("slide", i);

    gsap.to(root, { "--h": s.hue, duration: 1.2, ease: "power2.inOut" });
    BG.setHue(s.hue);

    if (old) old.ctx.cleanup();
    if (s.enter) { try { s.enter(ctx); } catch (e) { console.error(e); } }

    const type = opts.instant ? null : opts.dir < 0 ? "back" : (s.transition || "dive");
    const tl = gsap.timeline({
      onComplete() {
        if (old) old.el.remove();
        gsap.set(el, { clearProps: "transform,filter,clipPath,opacity" });
        trans = null;
      },
    });
    if (type) TRANS[type](old && old.el, el, tl, opts.dir || 1);
    trans = tl;

    // animaciones de entrada (los elementos sin data-step)
    const base = type ? (type === "back" ? 0.3 : 0.55) : 0;
    el.querySelectorAll("[data-in]").forEach((e) => {
      if (e.closest("[data-step]")) return;
      reveal(e, null, base + parseFloat(e.dataset.d || 0), ctx.tweens);
    });

    updateHud();
    sendState();
  }

  function doStep(n) {
    const { el, ctx, s } = cur;
    el.querySelectorAll(`[data-step="${n}"]`).forEach((e, k) => {
      reveal(e, null, parseFloat(e.dataset.d || 0) + k * 0.06, ctx.tweens);
    });
    if (s.step) { try { s.step(ctx, n); } catch (e) { console.error(e); } }
  }

  function next() {
    if (!started) { begin(false); return; }
    if (GAME.active) { GAME.next(); return; }
    const s = SL[idx];
    if (step < (s.steps || 0)) {
      step++;
      doStep(step);
      updateHud();
      sendState();
    } else if (idx < N - 1) {
      go(idx + 1, { dir: 1 });
    } else {
      GAME.open();
    }
  }

  function prev() {
    if (!started) return;
    if (GAME.active) { GAME.prev(); return; }
    if (step > 0) go(idx, { dir: -1 });
    else if (idx > 0) go(idx - 1, { dir: -1 });
  }

  // ---------------------------------------------------------- HUD
  function updateHud() {
    const p = GAME.active ? 1 : (idx + (step / ((SL[idx].steps || 0) + 1))) / N;
    $("#progress i").style.width = `${Math.max(0, p) * 100}%`;
    $("#counter").textContent = GAME.active ? "🎮" : `${idx + 1} / ${N}`;
  }

  function toast(msg) {
    const t = document.createElement("div");
    t.className = "toast";
    t.innerHTML = msg;
    $("#toasts").appendChild(t);
    gsap.fromTo(t, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.5, ease: "back.out(2)" });
    gsap.to(t, { opacity: 0, y: -10, delay: 3, duration: 0.5, onComplete: () => t.remove() });
  }

  // ---------------------------------------------------------- red
  let room = store.get("room", null) || NET.randomCode(4);
  let token = store.get("remoteToken", null) || NET.uid();
  store.set("remoteToken", token);
  const PIN = String(Math.floor(1000 + Math.random() * 9000));
  let pairingOpen = true;
  const remotes = new Set();

  function remoteUrl() { return NET.pageUrl("remote.html", room); }
  function playUrl() { return NET.pageUrl("play.html", room); }

  function qrSvg(text, dark = "#0b0b12") {
    const qr = qrcode(0, "M");
    qr.addData(text);
    qr.make();
    const n = qr.getModuleCount();
    let d = "";
    for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) if (qr.isDark(r, c)) d += `M${c},${r}h1v1h-1z`;
    return `<svg viewBox="-2 -2 ${n + 4} ${n + 4}" shape-rendering="crispEdges"><rect x="-2" y="-2" width="${n + 4}" height="${n + 4}" fill="#fff"/><path d="${d}" fill="${dark}"/></svg>`;
  }

  function renderPairing() {
    document.querySelectorAll(".remote-qr").forEach((e) => (e.innerHTML = qrSvg(remoteUrl())));
    document.querySelectorAll(".pin-code").forEach((e) => (e.textContent = PIN));
    document.querySelectorAll(".room-code").forEach((e) => (e.textContent = room));
    document.querySelectorAll(".remote-url").forEach((e) => (e.textContent = remoteUrl().replace(/^https?:\/\//, "")));
    GAME.refreshJoin && GAME.refreshJoin();
  }

  function setConn(state, extra) {
    const c = $("#conn");
    c.dataset.state = state;
    const labels = { connecting: "Connecting…", ready: "Online", reconnecting: "Reconnecting…", retrying: "Preparing room…", error: "Offline" };
    $("#conn .lbl").textContent = (labels[state] || state) + (remotes.size ? " · 📱" : "");
    const st = $("#start-net");
    if (st) {
      if (state === "ready") st.innerHTML = remotes.size ? "✅ <b>Remote connected</b>" : "Scan the QR code with your phone";
      else if (state === "error") st.innerHTML = "⚠️ " + ((extra && extra.message) || "Could not connect. Check the wifi.") + "<br><small>You can still use the arrow keys.</small>";
      else st.textContent = labels[state] || state;
    }
    if (extra && extra.room && extra.room !== room) { room = extra.room; store.set("room", room); renderPairing(); }
  }

  const net = NET.host({
    room,
    onStatus: setConn,
    onReady(r) { room = r; store.set("room", r); renderPairing(); },
    onConnect() {},
    onClose(cid, role) {
      if (remotes.has(cid)) {
        remotes.delete(cid);
        if (!remotes.size) toast("📱 Remote disconnected");
        setConn($("#conn").dataset.state || "ready");
      }
      if (role === "player") GAME.playerClosed(cid);
    },
    onMessage(cid, msg) {
      if (!msg || !msg.t) return;
      if (msg.t === "hello" && msg.role === "remote") {
        if (msg.token && msg.token === token) authorize(cid, false);
        else net.send(cid, { t: "auth", ok: false, pairing: pairingOpen });
        return;
      }
      if (msg.t === "pin") {
        if (pairingOpen && String(msg.pin) === PIN) authorize(cid, true);
        else net.send(cid, { t: "auth", ok: false, bad: true, pairing: pairingOpen });
        return;
      }
      if (msg.t === "cmd") { if (remotes.has(cid)) command(msg); return; }
      GAME.playerMessage(cid, msg);
    },
  });

  function authorize(cid, fresh) {
    const wasEmpty = remotes.size === 0;
    remotes.add(cid);
    net.send(cid, { t: "auth", ok: true, token });
    if (fresh) {
      pairingOpen = false;
      closePair();
      SFX.shimmer();
    }
    if (wasEmpty) toast("📱 <b>Remote connected</b>");
    setConn("ready");
    sendState();
  }

  function command(m) {
    switch (m.c) {
      case "next": next(); break;
      case "prev": prev(); break;
      case "goto": if (started && !GAME.active) go(Math.max(0, Math.min(N - 1, m.i | 0)), { dir: (m.i | 0) < idx ? -1 : 1 }); break;
      case "start": if (!started) begin(false); break;
      case "mute": SFX.setMuted(!SFX.muted); sendState(); break;
      case "lite": setLite(!lite); sendState(); break;
      default: GAME.command(m); return;
    }
  }

  let stateTimer = null;
  function sendState() {
    // agrupa varios cambios seguidos en un solo envío
    if (stateTimer) return;
    stateTimer = setTimeout(() => {
      stateTimer = null;
      const s = SL[Math.max(0, idx)];
      const notes = s.notes || [];
      const msg = {
        t: "state",
        started,
        mode: GAME.active ? "game" : "slides",
        slide: {
          i: idx, n: N, title: s.title, step, steps: s.steps || 0,
          notes: notes[step] || notes[notes.length - 1] || "",
          next: idx < N - 1 ? SL[idx + 1].title : "🎮 Juego final",
        },
        list: SL.map((x) => x.title),
        elapsed: started ? Math.floor((Date.now() - startTime) / 1000) : 0,
        muted: SFX.muted, lite,
        game: GAME.remoteState(),
        playUrl: playUrl(),
      };
      remotes.forEach((cid) => net.send(cid, msg));
    }, 30);
  }

  // ---------------------------------------------------------- inicio / overlays
  function closePair() { $("#pair").classList.remove("show"); }
  function openPair() {
    pairingOpen = true;
    renderPairing();
    $("#pair").classList.add("show");
  }

  async function fullscreen() {
    try {
      if (!document.fullscreenElement) await document.documentElement.requestFullscreen({ navigationUI: "hide" });
      else await document.exitFullscreen();
    } catch (e) {}
  }

  let wakeLock = null;
  async function keepAwake() {
    try { if ("wakeLock" in navigator) wakeLock = await navigator.wakeLock.request("screen"); } catch (e) {}
  }
  document.addEventListener("visibilitychange", () => { if (document.visibilityState === "visible" && started) keepAwake(); });

  function begin(fromClick) {
    if (started) return;
    const name = ($("#name-input").value || "").trim();
    if (name) { CFG.presentador = name; store.set("name", name); }
    SFX.init();
    if (fromClick) { fullscreen(); }
    keepAwake();
    started = true;
    startTime = Date.now();
    document.body.classList.add("started");
    const st = $("#start");
    gsap.to(st, { opacity: 0, scale: 1.08, ...blur(10), duration: 0.9, ease: "power3.in", onComplete: () => (st.style.display = "none") });
    const saved = store.get("slide", 0);
    let resumeAt = $("#resume") && $("#resume").checked ? saved : 0;
    // ?slide=7 en la URL arranca directo en esa diapositiva (útil para ensayar)
    const qs = parseInt(NET.params.get("slide"), 10);
    if (qs >= 1 && qs <= N) resumeAt = qs - 1;
    setTimeout(() => go(resumeAt, { dir: 1 }), 500);
  }

  // Pantalla de inicio
  $("#name-input").value = store.get("name", CFG.presentador === "Your name" ? "" : CFG.presentador);
  const savedSlide = store.get("slide", 0);
  if (savedSlide > 0 && savedSlide < N) {
    $("#resume-box").style.display = "flex";
    $("#resume-lbl").textContent = `Continue from slide ${savedSlide + 1}`;
  }
  $("#start-btn").addEventListener("click", () => begin(true));
  $("#name-input").addEventListener("keydown", (e) => { if (e.key === "Enter") begin(true); e.stopPropagation(); });
  gsap.from("#start .st-anim", { opacity: 0, y: 40, stagger: 0.12, duration: 1.2, ease: "expo.out", delay: 0.2 });

  // Teclado (también funciona con un presentador/clicker USB)
  document.addEventListener("keydown", (e) => {
    if (e.target && e.target.tagName === "INPUT") return;
    const k = e.key;
    if (["ArrowRight", "ArrowDown", "PageDown", " ", "Enter"].includes(k)) { e.preventDefault(); if (!started) begin(true); else next(); }
    else if (["ArrowLeft", "ArrowUp", "PageUp", "Backspace"].includes(k)) { e.preventDefault(); prev(); }
    else if (k === "f" || k === "F") fullscreen();
    else if (k === "m" || k === "M") { SFX.init(); SFX.toggleMute(); toast(SFX.muted ? "🔇 Sound off" : "🔊 Sound on"); sendState(); }
    else if (k === "l" || k === "L") { setLite(!lite); toast(lite ? "🪶 Light mode on" : "✨ Full effects"); sendState(); }
    else if (k === "p" || k === "P") { $("#pair").classList.contains("show") ? closePair() : openPair(); }
    else if (k === "g" || k === "G") { if (started) GAME.active ? GAME.close() : GAME.open(); }
    else if (k === "Escape") closePair();
    else if (k === "Home" && started && !GAME.active) go(0, { dir: -1 });
  });
  $("#pair").addEventListener("click", closePair);

  // Cronómetro hacia el control cada 15 s (por si se desincroniza)
  setInterval(() => { if (remotes.size) sendState(); }, 15000);

  // API para el juego
  window.PRES = {
    net, sendState, toast, shake, flash: flashOnce, reveal, splitLetters, qrSvg, playUrl, store,
    get room() { return room; },
    get lite() { return lite; },
    get idx() { return idx; },
    get started() { return started; },
    updateHud,
    hideSlides() {
      // el juego tapa todo: frenamos las animaciones de la diapositiva para no gastar CPU
      if (cur) cur.ctx.cleanup();
      gsap.to(slidesEl, { opacity: 0, duration: 0.6 });
      updateHud();
    },
    backToSlides() {
      gsap.set(slidesEl, { opacity: 1 });
      go(Math.max(0, idx), { dir: -1 });
    },
  };
  GAME.init(window.PRES);
  renderPairing();
})();
