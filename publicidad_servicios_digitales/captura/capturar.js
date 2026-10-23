// Captura cuadro a cuadro de una página web REAL con tiempo virtual.
// - Los temporizadores, Date y requestAnimationFrame se controlan con page.clock (Playwright).
// - Las animaciones/transiciones CSS se pausan y se avanzan con la Web Animations API.
// - Clics, escritura y desplazamiento son eventos reales sobre la página.
// Uso: node captura/capturar.js captura/guiones/<guion>.js <carpeta_salida> [desde] [hasta]
const path = require('path'), fs = require('fs');
const { chromium } = require('/opt/node22/lib/node_modules/playwright');

const FPS = 30;
const ease = x => x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;

(async () => {
  const [guionPath, outDir, desdeArg, hastaArg] = process.argv.slice(2);
  const G = require(path.resolve(guionPath));
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required', '--font-render-hinting=none', '--hide-scrollbars'] });
  const ctx = await browser.newContext({ viewport: { width: G.w, height: G.h }, deviceScaleFactor: G.dpr || 1, isMobile: !!G.mobile, hasTouch: !!G.mobile });
  const page = await ctx.newPage();
  page.on('pageerror', e => console.log('PAGEERR', e.message));
  page.on('console', m => { if (m.type() === 'error') console.log('CONSOLE', m.text()); });
  const T0 = new Date(G.ahora || '2026-10-23T20:00:00-03:00').getTime();
  await page.clock.install({ time: T0 - 5000 });
  await page.clock.pauseAt(T0); // el reloj queda detenido: sólo avanza con runFor (1/30 s por cuadro)
  await page.addInitScript(() => {
    window.__vt = 0;
    window.__abiertos = [];
    window.open = (u) => { window.__abiertos.push(u); return null; };
    // los enlaces externos se registran pero no se navega fuera de la página durante la captura
    document.addEventListener('click', e => { const a = e.target.closest && e.target.closest('a[target=_blank]'); if (a) { window.__abiertos.push(a.href); e.preventDefault(); } }, true);
    window.__drive = (vt) => {
      for (const a of document.getAnimations()) {
        if (a.__s === undefined) { a.__s = vt; a.pause(); }
        a.currentTime = Math.max(0, vt - a.__s);
      }
    };
    window.__tap = (x, y, k) => {
      let d = document.getElementById('__tap');
      if (!d) {
        d = document.createElement('div'); d.id = '__tap';
        d.style.cssText = 'position:fixed;z-index:2147483647;width:46px;height:46px;margin:-23px 0 0 -23px;border-radius:50%;pointer-events:none;background:rgba(255,255,255,.45);border:2px solid rgba(255,255,255,.95);box-shadow:0 0 18px rgba(255,255,255,.6)';
        document.documentElement.appendChild(d);
      }
      d.style.left = x + 'px'; d.style.top = y + 'px';
      // k: 0..1 progreso del toque (aparece, presiona, se expande y desaparece)
      const op = k < .15 ? k / .15 : k < .45 ? 1 : Math.max(0, 1 - (k - .45) / .55);
      const sc = k < .3 ? 1.15 - k : k < .45 ? .8 : .8 + (k - .45) * 2.2;
      d.style.opacity = op; d.style.transform = `scale(${sc})`; d.style.display = op <= 0 ? 'none' : 'block';
    };
  });
  await page.goto('file://' + path.resolve(path.dirname(guionPath), G.url));
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(300);
  if (G.preparar) await G.preparar(page);

  const total = Math.round(G.dur * FPS);
  const desde = +(desdeArg || 0), hasta = Math.min(total, +(hastaArg || total));
  const pasos = G.pasos.map(p => ({ ...p, hecho: false }));
  let scrollActual = null; // {t0,t1,a,b}
  const taps = [];

  async function centro(sel) {
    const b = await page.locator(sel).first().boundingBox();
    return { x: b.x + b.width / 2, y: b.y + b.height / 2 };
  }
  async function yDe(target) {
    if (typeof target === 'number') return target;
    return await page.evaluate(([sel, off]) => { const el = document.querySelector(sel); return Math.max(0, el.getBoundingClientRect().top + scrollY - off); }, [target.sel, target.off || 0]);
  }

  for (let f = 0; f < hasta; f++) {
    const t = f / FPS;
    for (const p of pasos) {
      if (p.hecho || t + 1e-6 < p.t) continue;
      p.hecho = true;
      if (p.tipo === 'scroll') {
        const a = await page.evaluate(() => scrollY);
        scrollActual = { t0: p.t, t1: p.t + p.dur, a, b: await yDe(p.a) };
      } else if (p.tipo === 'tap') {
        const c = p.sel ? await centro(p.sel) : { x: p.x, y: p.y };
        taps.push({ t: p.t, ...c });
        // el clic real ocurre en el punto de presión del toque
        p.clic = c;
        pasos.push({ t: p.t + .2, tipo: '__clic', x: c.x, y: c.y, hecho: false });
      } else if (p.tipo === '__clic') {
        await page.mouse.click(p.x, p.y);
      } else if (p.tipo === 'escribir') {
        const n = p.texto.length;
        await page.locator(p.sel).first().focus();
        for (let i = 0; i < n; i++) pasos.push({ t: p.t + i / (p.cps || 9), tipo: '__tecla', c: p.texto[i], hecho: false });
      } else if (p.tipo === '__tecla') {
        await page.keyboard.insertText(p.c);
      } else if (p.tipo === 'eval') {
        await page.evaluate(p.fn);
      }
    }
    if (scrollActual) {
      const k = Math.min(1, Math.max(0, (t - scrollActual.t0) / (scrollActual.t1 - scrollActual.t0)));
      const y = scrollActual.a + (scrollActual.b - scrollActual.a) * ease(k);
      await page.evaluate(y => window.scrollTo({ top: y, behavior: 'instant' }), y);
      if (k >= 1) scrollActual = null;
    }
    const tap = taps.filter(x => t >= x.t && t <= x.t + .7).pop();
    await page.evaluate(([tp, k]) => { if (tp) window.__tap(tp.x, tp.y, k); else if (window.__tap && document.getElementById('__tap')) document.getElementById('__tap').style.display = 'none'; }, [tap || null, tap ? (t - tap.t) / .7 : 0]);
    if (f > 0) await page.clock.runFor(1000 / FPS);
    await page.evaluate(vt => window.__drive(vt), f * 1000 / FPS);
    if (f >= desde) await page.screenshot({ path: `${outDir}/f${String(f).padStart(5, '0')}.jpg`, type: 'jpeg', quality: 92 });
  }
  const abiertos = await page.evaluate(() => window.__abiertos);
  fs.writeFileSync(`${outDir}/enlaces_abiertos.json`, JSON.stringify(abiertos, null, 1));
  console.log('ok', outDir, hasta - desde, 'cuadros; enlaces:', abiertos.length);
  await browser.close();
})();
