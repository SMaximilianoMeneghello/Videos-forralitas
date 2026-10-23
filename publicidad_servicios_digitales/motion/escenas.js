/* Escenas de la publicidad. Cada escena: construcción del DOM + función que lo actualiza para el tiempo t. */
const S = TL.secciones;
const ESC = [];
function escenaDef(nombre, desde, hasta, init, upd) { const c = capa(nombre); const ctx = init(c) || {}; ESC.push({ c, desde, hasta, ctx, upd }); }

/* ---------- piezas reutilizables ---------- */
function panelLineaTiempo(w, h) {
  const thumbs = [20, 65, 110, 170, 230, 280];
  const anchos = [.15, .15, .15, .25, .15, .15];
  let x = 0, clips = '';
  thumbs.forEach((f, i) => { clips += `<div class="clip" style="left:${x * 100}%;width:${anchos[i] * 100 - .6}%"><img src="${src('demo', f)}"><span>${['fiordo', 'fpv_01', 'bosque', 'cascada', 'costa', 'final'][i]}.mov</span></div>`; x += anchos[i]; });
  const kf = [.08, .22, .31, .47, .55, .7, .86].map(p => `<i class="kf" style="left:${p * 100}%"></i>`).join('');
  return $el(`<div class="nle abs" style="width:${w}px;height:${h}px">
    <style>.nle{border-radius:22px;background:linear-gradient(180deg,rgba(18,22,36,.92),rgba(10,12,22,.92));border:1px solid rgba(140,170,255,.22);box-shadow:0 30px 80px rgba(0,0,0,.6);overflow:hidden;font:600 14px Mono;color:#9fb0dd}
    .nle .reg{position:absolute;left:84px;right:16px;top:10px;height:26px;background:repeating-linear-gradient(90deg,rgba(160,180,255,.35) 0 1px,transparent 1px 24px)}
    .nle .pista{position:absolute;left:84px;right:16px;height:var(--h);}
    .nle .nom{position:absolute;left:16px;width:56px;height:var(--h);display:flex;align-items:center;color:#7d8cbb}
    .nle .clip{position:absolute;top:0;height:100%;border-radius:8px;overflow:hidden;background:linear-gradient(135deg,#2f6bff,#1d3fb0);border:1px solid rgba(255,255,255,.25)}
    .nle .clip img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:.75}
    .nle .clip span{position:absolute;left:8px;bottom:6px;font:600 12px Mono;color:#fff;text-shadow:0 1px 4px #000}
    .nle .tit{position:absolute;height:100%;border-radius:8px;background:linear-gradient(135deg,#7b3cff,#b07bff);display:flex;align-items:center;padding-left:10px;color:#fff;font:700 12px Mono}
    .nle .kf{position:absolute;top:50%;width:12px;height:12px;margin:-6px 0 0 -6px;background:#ffd34d;transform:rotate(45deg);box-shadow:0 0 10px #ffd34d}
    .nle .cab{position:absolute;top:8px;width:2px;bottom:8px;background:#4fa3ff;box-shadow:0 0 12px #4fa3ff;z-index:3}
    .nle .cab::before{content:"";position:absolute;top:-2px;left:-7px;width:16px;height:14px;background:#4fa3ff;clip-path:polygon(0 0,100% 0,50% 100%)}
    .nle canvas{position:absolute;inset:0;width:100%;height:100%}</style>
    <div class="reg"></div>
    <div class="nom" style="--h:${h * .16}px;top:${h * .14}px">V2</div><div class="pista p0" style="--h:${h * .16}px;top:${h * .14}px"><div class="tit" style="left:2%;width:22%">NORTE · título</div><div class="tit" style="left:44%;width:20%">SIN LÍMITES</div><div class="tit" style="left:86%;width:13%">cierre</div></div>
    <div class="nom" style="--h:${h * .26}px;top:${h * .33}px">V1</div><div class="pista p1" style="--h:${h * .26}px;top:${h * .33}px">${clips}</div>
    <div class="nom" style="--h:${h * .1}px;top:${h * .62}px">FX</div><div class="pista p2" style="--h:${h * .1}px;top:${h * .62}px">${kf}</div>
    <div class="nom" style="--h:${h * .18}px;top:${h * .76}px">A1</div><div class="pista p3" style="--h:${h * .18}px;top:${h * .76}px"><canvas width="900" height="60"></canvas></div>
    <div class="cab"></div></div>`);
}
function dibujarOnda(cv) { const g = cv.getContext('2d'), r = rng(9); g.fillStyle = 'rgba(79,163,255,.75)'; for (let x = 0; x < 900; x += 3) { const a = (Math.abs(Math.sin(x * .021)) * .6 + r() * .4) * (x % 120 < 8 ? 1 : .55); g.fillRect(x, 30 - a * 26, 2, a * 52); } }
function panelCodigo() {
  return $el(`<div class="abs" style="width:520px;padding:26px 30px;border-radius:20px;background:rgba(12,14,24,.94);border:1px solid rgba(140,170,255,.25);font:500 22px/1.6 Mono;color:#cdd6f4;box-shadow:0 30px 80px rgba(0,0,0,.6)">
  <div><span style="color:#b07bff">const</span> invitacion = {</div><div>&nbsp;&nbsp;nombre: <span style="color:#a6e3a1">'Valentina'</span>,</div><div>&nbsp;&nbsp;cuenta: <span style="color:#89b4fa">regresiva</span>(),</div><div>&nbsp;&nbsp;mapa: <span style="color:#f9e2af">true</span>,</div><div>};</div><div><span style="color:#89b4fa">animar</span>(<span style="color:#a6e3a1">'.hero'</span>, { y: <span style="color:#fab387">0</span> });</div></div>`);
}
function marcoImagen(w, h, radio = 26) { return $el(`<div class="abs" style="width:${w}px;height:${h}px;border-radius:${radio}px;overflow:hidden;box-shadow:0 0 0 1.5px rgba(255,255,255,.14),0 40px 100px rgba(0,0,0,.7)"><img style="width:100%;height:100%;object-fit:cover;display:block" alt=""></div>`); }
const WAPP = `<svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="48" fill="#25d366"/><path d="M50 20a29 29 0 0 0-25 43.700L21 79l16-4.200A29 29 0 1 0 50 20z" fill="none" stroke="#fff" stroke-width="5.500" stroke-linejoin="round"/><path d="M39 35c-1.500 0-3 1.500-3 4 0 6 8 17 18 20 3 1 5 0 6-2l1-3-6-3-3 3c-4-2-7-5-9-9l3-3-3-6z" fill="#fff"/></svg>`;
function tarjetaValentina() {
  return $el(`<div class="abs p3d" style="width:540px;height:960px">
   <style>
   .vcard .cara{position:absolute;inset:0;border-radius:22px;overflow:hidden}
   .vin{background:radial-gradient(90% 60% at 50% 30%,#22378a,#0c1745 60%,#060b26);box-shadow:inset 0 0 0 2px rgba(201,211,238,.35),inset 0 0 0 12px rgba(6,11,38,.6),inset 0 0 0 13.500px rgba(201,211,238,.25);text-align:center;color:#eef2fd}
   .vin .el{position:absolute;left:0;width:100%}
   .puerta{position:absolute;top:0;width:270px;height:960px;transform-style:preserve-3d}
   .puerta .f,.puerta .b{position:absolute;inset:0;backface-visibility:hidden;border-radius:22px}
   .puerta .f{background:linear-gradient(160deg,#2a3f8f,#14245e 60%,#0b1640);box-shadow:inset 0 0 0 2px rgba(201,211,238,.35);overflow:hidden}
   .puerta .b{transform:rotateY(180deg);background:linear-gradient(160deg,#1a2a6a,#0b1640)}
   .orn{position:absolute;inset:26px;border:1.5px solid rgba(201,211,238,.45);border-radius:12px}
   .sello2{position:absolute;top:50%;width:120px;height:120px;margin-top:-60px;border-radius:50%;background:radial-gradient(circle at 35% 30%,#fff,#d8e0f7 40%,#9fb2e6);box-shadow:0 8px 30px rgba(0,0,0,.5);font:400 72px/120px Allura;color:#1d3283;text-align:center}
   </style>
   <div class="vcard p3d" style="position:absolute;inset:0">
    <div class="cara vin">
      <svg class="el e1" style="top:150px" width="110" height="64" viewBox="0 0 120 70"><path d="M8 60 L14 18 L36 40 L60 6 L84 40 L106 18 L112 60 Z" fill="none" stroke="#e9eefc" stroke-width="3" stroke-linejoin="round"/><path d="M8 64 H112" stroke="#c9d3ee" stroke-width="4"/></svg>
      <div class="el e2" style="top:250px;font:600 20px Montserrat;letter-spacing:.5em;color:#c9d3ee">MIS XV AÑOS</div>
      <div class="el e3" style="top:300px;font:400 150px/1 Allura;color:#fff;text-shadow:0 0 30px rgba(110,143,232,.8)">Valentina</div>
      <div class="el e4" style="top:500px;height:1px;width:260px;left:140px;background:linear-gradient(90deg,transparent,#c9d3ee,transparent)"></div>
      <div class="el e5" style="top:540px;font:600 19px Montserrat;letter-spacing:.32em;color:#c9d3ee">SÁBADO</div>
      <div class="el e6" style="top:572px;font:500 90px/1 Cormorant;color:#fff">13</div>
      <div class="el e7" style="top:672px;font:600 19px Montserrat;letter-spacing:.32em;color:#c9d3ee">MARZO · 2027 · 21:30 H</div>
      <div class="el e8" style="top:745px;font:500 34px Cormorant;color:#fff">Salón Aurora</div>
      <div class="el e9" style="top:790px;font:500 16px Montserrat;letter-spacing:.1em;color:#9fb0dd">Ubicación de ejemplo · datos ficticios</div>
    </div>
    <div class="puerta pi" style="left:0;transform-origin:left center"><div class="f"><div class="orn"></div><div class="sello2" style="right:-60px">V</div></div><div class="b"></div></div>
    <div class="puerta pd" style="right:0;transform-origin:right center"><div class="f"><div class="orn"></div><div class="sello2" style="left:-60px;clip-path:inset(0 0 0 50%)">V</div></div><div class="b"></div></div>
   </div></div>`);
}

/* =====================================================================
   1. INTRO: viaje a través de composiciones digitales
   ===================================================================== */
escenaDef('intro', 0, 6.3, c => {
  const tun = $el('<div class="abs p3d" style="left:540px;top:860px;width:0;height:0"></div>'); c.appendChild(tun);
  const items = [
    { t0: .3, k: 'nle', x: -60, y: -40, r: -6 }, { t0: .75, k: 'demo', i: 200, x: 230, y: 160, r: 5 }, { t0: 1.2, k: 'tel', s: 'inv', i: 170, x: -250, y: 100, r: -8 },
    { t0: 1.65, k: 'web', s: 'tiendaD', i: 90, x: 160, y: -260, r: 4 }, { t0: 2.1, k: 'card', s: 'mateo', i: 270, x: -200, y: -230, r: -5 }, { t0: 2.55, k: 'code', x: 230, y: 250, r: 6 },
    { t0: 3.0, k: 'tel', s: 'brasaM', i: 120, x: -260, y: 200, r: -7 }, { t0: 3.45, k: 'web', s: 'servD', i: 90, x: 190, y: -100, r: 5 }, { t0: 3.9, k: 'demo', i: 110, x: -140, y: -60, r: -4 },
    { t0: 4.35, k: 'card', s: 'infantil', i: 140, x: 250, y: 170, r: 6 }, { t0: 4.8, k: 'web', s: 'brasaD', i: 100, x: -170, y: 140, r: -5 }, { t0: 5.2, k: 'tel', s: 'inv', i: 400, x: 40, y: -20, r: 0 }
  ];
  items.forEach(it => {
    let el;
    if (it.k === 'nle') { el = panelLineaTiempo(760, 300); dibujarOnda(el.querySelector('canvas')); }
    else if (it.k === 'code') el = panelCodigo();
    else if (it.k === 'demo') { el = marcoImagen(360, 640); poner(el.querySelector('img'), 'demo', it.i); }
    else if (it.k === 'card') { el = marcoImagen(340, 604); poner(el.querySelector('img'), it.s, it.i); }
    else if (it.k === 'tel') { el = telefono(300, 640); poner(el.querySelector('img'), it.s, it.i); }
    else { el = navegador(720, 496, 'tu-negocio · demo'); poner(el.querySelector('img'), it.s, it.i); }
    el.style.left = '0'; el.style.top = '0'; tun.appendChild(el); it.el = el;
  });
  return { tun, items };
}, (t, x) => {
  tr(x.tun, `rotateZ(${Math.sin(t * .6) * 4}deg)`);
  for (const it of x.items) {
    const k = (t - it.t0) / 2.1;
    if (k < 0 || k > 1) { vis(it.el, 0); continue; }
    const z = -3400 + 4700 * Math.pow(k, 2.3);
    const o = Math.min(pr(k, 0, .25), 1 - pr(z, 600, 1200));
    vis(it.el, o);
    tr(it.el, `translate(-50%,-50%) translate3d(${it.x}px,${it.y}px,${z}px) rotateZ(${it.r}deg) rotateY(${it.x * -.02}deg)`);
  }
});

/* =====================================================================
   2. TÍTULO: TUS IDEAS MERECEN ALGO EXTRAORDINARIO + servicios
   ===================================================================== */
escenaDef('titulo', 5.7, 14.1, c => {
  const blq = lineas([['TUS IDEAS', '', 'font-size:132px'], ['MERECEN ALGO', '', 'font-size:100px;margin-top:6px'], ['EXTRAORDINARIO', 'grad', 'font-size:92px;margin-top:10px']], 'cen titular p3d', 'top:560px');
  c.appendChild(blq);
  blq.querySelectorAll('.linea').forEach(l => ajustar(l, 980));
  const servicios = [['play', 'EDICIÓN DE VIDEOS'], ['tarjeta', 'INVITACIONES DIGITALES'], ['web', 'INVITACIONES WEB'], ['codigo', 'PÁGINAS WEB']];
  const chips = servicios.map(([i, txt], j) => { const ch = chip(i, txt, `left:50%;top:${860 + j * 150}px;font-size:38px;padding:20px 34px 20px 22px`); c.appendChild(ch); return ch; });
  return { blq, chips };
}, (t, x) => {
  animarChars(x.blq, t, 6.2, .03, .75, 13.3);
  const k = salida(pr(t, 6.1, 9.5)), up = suave(pr(t, 10.0, 10.9));
  tr(x.blq, `translateY(${-up * 330}px) scale(${lerp(1.1, 1, k) * lerp(1, .74, up)}) rotateX(${lerp(14, 0, k)}deg)`);
  document.documentElement.style.setProperty('--gp', ((t * 22) % 220) + '%');
  const tDig = palabraDe('v02', 'experiencias') - .3;
  x.chips.forEach((ch, j) => {
    const q = salida(pr(t, tDig + j * .2, tDig + j * .2 + .7)), s = suave(pr(t, 13.2 + j * .05, 13.7 + j * .05));
    vis(ch, q * (1 - s));
    tr(ch, `translateX(-50%) translateY(${(1 - q) * 80 - s * 120}px) rotateX(${(1 - q) * -80}deg) scale(${.9 + .1 * q})`);
    ch.style.filter = q < .98 || s > 0 ? `blur(${(1 - q) * 10 + s * 12}px)` : 'none';
  });
});

/* =====================================================================
   3. EDICIÓN: interfaz de edición que se arma y empuja a la demo
   ===================================================================== */
escenaDef('nle', 13.9, 17.6, c => {
  const cont = $el('<div class="abs p3d" style="inset:0;transform-origin:540px 668px"></div>'); c.appendChild(cont);
  const visor = $el(`<div class="abs" style="left:260px;top:170px;width:560px;height:996px;border-radius:18px;overflow:hidden;box-shadow:0 0 0 1.5px rgba(140,170,255,.35),0 40px 120px rgba(0,0,0,.7)">
    <img style="width:100%;height:100%;object-fit:cover"><div style="position:absolute;inset:40px;border:1px dashed rgba(255,255,255,.35)"></div>
    <div class="tc" style="position:absolute;left:20px;top:16px;font:600 22px Mono;color:#fff;text-shadow:0 2px 8px #000">00:00:00:00</div>
    <div style="position:absolute;right:20px;top:16px;font:600 18px Mono;color:#cfe0ff;text-shadow:0 2px 8px #000">1080×1920 · 30 FPS</div></div>`);
  cont.appendChild(visor);
  const nle = panelLineaTiempo(960, 330); nle.style.left = '60px'; nle.style.top = '1230px'; dibujarOnda(nle.querySelector('canvas')); cont.appendChild(nle);
  return { cont, visor, img: visor.querySelector('img'), tc: visor.querySelector('.tc'), nle, clips: [...nle.querySelectorAll('.clip,.tit')], kfs: [...nle.querySelectorAll('.kf')], cab: nle.querySelector('.cab'), onda: nle.querySelector('canvas') };
}, (t, x) => {
  const e = salida(pr(t, 14.0, 14.8));
  vis(x.visor, e); tr(x.visor, `translateY(${(1 - e) * 60}px) scale(${.92 + .08 * e})`);
  const f = (t - 14.0) * 30; poner(x.img, 'raw', Math.min(299, Math.max(0, f + 40)));
  const fr2 = Math.max(0, Math.floor(f + 40)); x.tc.textContent = `00:00:${String(Math.floor(fr2 / 30)).padStart(2, '0')}:${String(fr2 % 30).padStart(2, '0')}`;
  const n = salida(pr(t, 14.15, 14.9)); vis(x.nle, n); tr(x.nle, `translateY(${(1 - n) * 200}px)`);
  x.clips.forEach((cp, i) => { const q = salida(pr(t, 14.3 + i * .09, 14.9 + i * .09)); cp.style.transform = `translateX(${(1 - q) * 700}px)`; cp.style.opacity = q; });
  x.kfs.forEach((k, i) => { const q = eob(pr(t, 15.5 + i * .06, 15.8 + i * .06)); k.style.transform = `rotate(45deg) scale(${q})`; });
  x.onda.style.clipPath = `inset(0 ${100 - 100 * salida(pr(t, 14.9, 15.9))}% 0 0)`;
  x.cab.style.left = (84 + (960 - 100) * pr(t, 14.6, 17.4)) + 'px';
  // empuje de cámara hacia el visor
  const p = suave(pr(t, 16.55, 17.45));
  tr(x.cont, `scale(${lerp(1, 1.93, p)}) translateY(${p * 2}px)`);
  op(x.nle, n * (1 - pr(t, 16.5, 16.9)));
});

/* =====================================================================
   4. DEMO de edición a pantalla completa (10 s)
   ===================================================================== */
escenaDef('demo', 17.45, 27.75, c => {
  const img = $el('<img class="abs" style="left:0;top:0;width:1080px;height:1920px">'); c.appendChild(img);
  const tag = $el('<div class="abs tag" style="left:50px;top:70px">● DEMO DE EDICIÓN · 10 s</div>'); c.appendChild(tag);
  const cred = $el('<div class="abs" style="left:0;width:1080px;top:1862px;text-align:center;font:500 17px Mono;color:rgba(255,255,255,.55)">Tomas de drone: Wikimedia Commons · CC BY 3.0 · ver créditos</div>'); c.appendChild(cred);
  return { img, tag, cred };
}, (t, x) => {
  poner(x.img, 'demo', Math.min(299, (t - 17.5) * 30));
  op(x.tag, pr(t, 17.9, 18.3) * (1 - pr(t, 20.2, 20.6)));
  op(x.cred, pr(t, 18.0, 18.5) * (1 - pr(t, 26.8, 27.3)));
  op(x.img, 1 - pr(t, 27.5, 27.75));
});

/* =====================================================================
   5. EDICIÓN 2: antes / después + técnicas
   ===================================================================== */
escenaDef('edicion2', 27.45, 37.0, c => {
  const tit = lineas([['EDICIÓN', '', 'font-size:96px'], ['PROFESIONAL', 'grad', 'font-size:84px']], 'cen titular', 'top:120px'); c.appendChild(tit);
  tit.querySelectorAll('.linea').forEach(l => ajustar(l, 980));
  const visor = $el(`<div class="abs p3d" style="left:250px;top:420px;width:580px;height:1031px;border-radius:24px;overflow:hidden;box-shadow:0 0 0 1.5px rgba(140,170,255,.35),0 40px 120px rgba(0,0,0,.75)">
    <img class="r" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover"><img class="g" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover">
    <div class="div" style="position:absolute;top:0;bottom:0;width:3px;margin-left:-1.5px;background:#fff;box-shadow:0 0 18px #4fa3ff"><div style="position:absolute;top:50%;left:50%;width:56px;height:56px;margin:-28px;border-radius:50%;background:rgba(10,14,30,.75);border:2px solid #fff;display:grid;place-items:center;font:700 20px Mono">⇆</div></div>
    <div class="tag" style="position:absolute;left:18px;top:18px">ANTES</div><div class="tag" style="position:absolute;right:18px;top:18px;color:#fff;border-color:#4fa3ff">DESPUÉS</div></div>`);
  c.appendChild(visor);
  const defs = [['capas', 'MOTION<br>GRAPHICS', 'animaciones', 30, 560, 'L'], ['chispa', 'EFECTOS<br>VISUALES', 'efectos', 700, 760, 'R'], ['play', 'TRANSICIONES<br>CINEMATOGRÁFICAS', 'transiciones', 20, 1060, 'L'], ['color', 'COLOR · RITMO<br>Y SONIDO', 'detalle', 690, 1290, 'R']];
  const chips = defs.map(([i, txt, w, l, top, lado]) => { const ch = chip(i, `<span style="line-height:1.15">${txt}</span>`, `left:${l}px;top:${top}px;font-size:26px;padding:14px 24px 14px 16px`); c.appendChild(ch); return { ch, t: palabraDe('v04', w) - .1, lado }; });
  return { tit, visor, r: visor.querySelector('.r'), g: visor.querySelector('.g'), div: visor.querySelector('.div'), chips };
}, (t, x) => {
  animarChars(x.tit, t, 27.9, .03, .7, 36.3);
  const e = salida(pr(t, 27.6, 28.5)), s = suave(pr(t, 36.2, 36.9));
  vis(x.visor, e * (1 - s));
  tr(x.visor, `translateY(${(1 - e) * 120}px) scale(${(.85 + .15 * e) * (1 - .15 * s)}) rotateY(${Math.sin(t * .5) * 6}deg) rotateX(${(1 - e) * 20}deg)`);
  const f = 135 + ((t - 27.5) * 30) % 75;
  poner(x.r, 'raw', f); poner(x.g, 'demo', f);
  const pos = 50 + 32 * Math.sin((t - 28.3) * 1.25) * pr(t, 28.3, 29);
  x.g.style.clipPath = `inset(0 0 0 ${pos}%)`; x.div.style.left = pos + '%';
  x.chips.forEach(({ ch, t: t0, lado }) => {
    const q = salida(pr(t, t0, t0 + .6)), o = q * (1 - s);
    vis(ch, o); tr(ch, `translateX(${(1 - q) * (lado === 'L' ? -300 : 300)}px) translateY(${Math.sin(t * 1.5 + t0) * 6}px)`);
    ch.style.filter = q < .97 ? `blur(${(1 - q) * 12}px)` : 'none';
  });
});

/* =====================================================================
   6. FORMATOS para redes
   ===================================================================== */
escenaDef('formatos', 36.5, 43.2, c => {
  const tit = lineas([['CONTENIDO', '', 'font-size:92px'], ['PARA REDES', 'grad', 'font-size:92px']], 'cen titular', 'top:120px'); c.appendChild(tit);
  tit.querySelectorAll('.linea').forEach(l => ajustar(l, 980));
  const cont = $el('<div class="abs p3d" style="left:540px;top:900px;width:0;height:0"></div>'); c.appendChild(cont);
  const mk = (w, h, r, etiqueta) => { const m = marcoImagen(w, h, r); const lab = $el(`<div class="tag" style="position:absolute;left:50%;bottom:-62px;transform:translateX(-50%)">${etiqueta}</div>`); m.style.overflow = 'visible'; m.querySelector('img').style.borderRadius = r + 'px'; m.appendChild(lab); cont.appendChild(m); return m; };
  const cuad = mk(360, 360, 22, '1:1 · FEED'), vert = mk(330, 412, 22, '4:5 · PUBLICACIÓN');
  const tel = telefono(380, 800); cont.appendChild(tel);
  const lt = $el('<div class="tag" style="position:absolute;left:50%;bottom:-62px;transform:translateX(-50%)">9:16 · REELS Y STORIES</div>'); tel.appendChild(lt);
  const usos = [['redes', 'REDES SOCIALES'], ['eventos', 'EVENTOS'], ['marcas', 'MARCAS'], ['emprendimientos', 'EMPRENDIMIENTOS'], ['proyectos', 'PROYECTOS PERSONALES']];
  const pills = usos.map(([w, txt], i) => { const p = $el(`<div class="chip abs" style="font-size:26px;padding:14px 26px;left:50%;top:${1390 + Math.floor(i / 3) * 96}px">${txt}</div>`); c.appendChild(p); return { p, t: palabraDe('v05', w) - .05, i }; });
  return { tit, cuad, vert, tel, pills };
}, (t, x) => {
  animarChars(x.tit, t, 36.8, .03, .7, 42.7);
  const e = salida(pr(t, 36.6, 37.6)), s = suave(pr(t, 42.6, 43.1));
  const f = 20 + ((t - 36.6) * 30) % 270;
  [[x.cuad, -300, -60, -150, 22], [x.vert, 300, 40, -150, -22], [x.tel, 0, -20, 80, 0]].forEach(([el, px, py, pz, ry], i) => {
    const q = salida(pr(t, 36.7 + i * .15, 37.6 + i * .15));
    vis(el, q * (1 - s));
    tr(el, `translate(-50%,-50%) translate3d(${px * (1 + s)}px,${py + (1 - q) * 400 + Math.sin(t * 1.2 + i) * 10}px,${pz}px) rotateY(${ry + Math.sin(t * .7 + i) * 4}deg)`);
    poner(el.querySelector('img'), 'demo', f);
  });
  // reparte las píldoras en filas centradas
  const filas = [x.pills.slice(0, 3), x.pills.slice(3)];
  filas.forEach(fila => {
    const anchos = fila.map(p => p.p.offsetWidth), total = anchos.reduce((a, b) => a + b, 0) + 16 * (fila.length - 1);
    let xx = -total / 2;
    fila.forEach((p, j) => { p.x = xx; xx += anchos[j] + 16; });
  });
  x.pills.forEach(p => {
    const q = eob(pr(t, p.t, p.t + .45));
    vis(p.p, pr(t, p.t, p.t + .2) * (1 - s)); tr(p.p, `translateX(${p.x}px) scale(${q})`);
  });
});

/* =====================================================================
   7. HACÉ QUE TUS VIDEOS DESTAQUEN
   ===================================================================== */
escenaDef('destacan', 42.9, 45.1, c => {
  const bg = $el(`<img class="abs" style="left:0;top:0;width:1080px;height:1920px;object-fit:cover;filter:blur(14px) brightness(.35) saturate(1.2)">`); c.appendChild(bg);
  const pal = [['HACÉ QUE', 108, 650, ''], ['TUS VIDEOS', 124, 800, ''], ['DESTAQUEN', 132, 975, 'grad']].map(([txt, fs, top, cls]) => { const d = $el(`<div class="cen titular ${cls}" style="top:${top}px;font-size:${fs}px">${txt}</div>`); c.appendChild(d); ajustar(d, 1000); return d; });
  return { bg, pal };
}, (t, x) => {
  poner(x.bg, 'demo', 150 + (t - 43) * 30);
  const tiempos = [43.0, 43.35, 43.7];
  const sal = ei(pr(t, 44.6, 45.05));
  x.pal.forEach((p, i) => {
    const k = ei(pr(t, tiempos[i] - .18, tiempos[i]));
    const sh = (1 - pr(t, tiempos[i], tiempos[i] + .35)) * (t > tiempos[i] ? 1 : 0);
    vis(p, k * (1 - sal));
    tr(p, `scale(${lerp(2.4, 1, k) * (1 + sal * 1.6)}) translate(${Math.sin(t * 90) * 10 * sh}px,${Math.cos(t * 77) * 8 * sh}px)`);
    p.style.filter = k < .99 ? `blur(${(1 - k) * 22}px)` : (sal > 0 ? `blur(${sal * 14}px)` : 'none');
  });
  op(x.bg, pr(t, 42.9, 43.1) * (1 - sal));
});

/* =====================================================================
   8. INVITACIONES DIGITALES: tarjeta que se despliega + variedad
   ===================================================================== */
escenaDef('invitaciones', 44.9, 63.2, c => {
  const tit = lineas([['INVITACIONES', '', 'font-size:84px'], ['DIGITALES', 'grad', 'font-size:84px']], 'cen titular', 'top:110px'); c.appendChild(tit);
  tit.querySelectorAll('.linea').forEach(l => ajustar(l, 980));
  const mundo = $el('<div class="abs p3d" style="left:540px;top:900px;width:0;height:0"></div>'); c.appendChild(mundo);
  const val = tarjetaValentina(); mundo.appendChild(val);
  const otras = [['mateo', 40], ['infantil', 0], ['comunion', 0], ['aniversario', 0], ['baby', 0]].map(([s, ini]) => { const m = marcoImagen(540, 960, 26); mundo.appendChild(m); return { m, s, ini, img: m.querySelector('img') }; });
  const defs = [['chispa', 'DISEÑO<br>PERSONALIZADO', 'personalizado'], ['tarjeta', 'ELEGANTES<br>Y ANIMADAS', 'elegante'], ['enlace', 'LISTAS PARA<br>COMPARTIR', 'sorprender']];
  const chips = defs.map(([i, txt, w], j) => { const ch = chip(i, `<span style="line-height:1.15">${txt}</span>`, `left:50%;top:${1330 + j * 0}px;font-size:26px;padding:14px 24px 14px 16px`); c.appendChild(ch); return { ch, t: palabraDe('v08', w) - .1, j }; });
  const tag = $el('<div class="abs tag" style="left:50%;top:1500px;transform:translateX(-50%)">EJEMPLOS DE DEMOSTRACIÓN · DATOS FICTICIOS</div>'); c.appendChild(tag);
  const chispas = document.createElement('canvas'); chispas.width = 540; chispas.height = 960; chispas.style.cssText = 'position:absolute;left:0;top:0;pointer-events:none;mix-blend-mode:screen'; val.querySelector('.vin').appendChild(chispas);
  return { tit, mundo, val, vc: val.querySelector('.vcard'), pi: val.querySelector('.pi'), pd: val.querySelector('.pd'), els: [...val.querySelectorAll('.vin .el')], otras, chips, tag, chispas };
}, (t, x) => {
  animarChars(x.tit, t, 45.2, .03, .7, 62.5);
  // --- apertura de la tarjeta (45–51) ---
  const ent = salida(pr(t, 45.0, 46.4));
  const ab = suave(pr(t, 46.5, 47.9));
  tr(x.pi, `rotateY(${-165 * ab}deg)`); tr(x.pd, `rotateY(${165 * ab}deg)`);
  const fd = 1 - pr(t, palabraDe('v07', 'quince') - .1, palabraDe('v07', 'quince') + .4); op(x.pi, fd); op(x.pd, fd);
  x.els.forEach((el, i) => { const q = salida(pr(t, 47.3 + i * .12, 48.0 + i * .12)); el.style.opacity = q; el.style.transform = `translateY(${(1 - q) * 30}px)`; el.style.filter = q < .98 ? `blur(${(1 - q) * 8}px)` : 'none'; });
  // chispas sobre la tarjeta
  const g = x.chispas.getContext('2d'); g.clearRect(0, 0, 540, 960);
  if (t > 47 && t < 63) { const r = rng(4); for (let i = 0; i < 60; i++) { const px = r() * 540, py = ((r() * 960 - (t - 47) * (20 + r() * 40)) % 960 + 960) % 960, a = Math.max(0, Math.sin(t * 3 + i)) * .9; g.fillStyle = `rgba(233,238,252,${a})`; g.beginPath(); g.arc(px, py, .8 + r() * 1.8, 0, 6.29); g.fill(); } }
  // --- disposición: tarjeta sola -> fila -> carrusel 3D ---
  const tQ = palabraDe('v07', 'quince'), tD = palabraDe('v07', 'dieciocho'), tC = palabraDe('v07', 'cumpleaños'), tE = palabraDe('v07', 'celebraciones');
  const fila = suave(pr(t, tQ - .1, tQ + .6));
  const anillo = suave(pr(t, 56.0, 57.3));
  const sal = ei(pr(t, 62.4, 63.05));
  const ang0 = (t - 56) * 24 + sal * 160;
  // posiciones: [x, y, z, escala] para cada tarjeta en "fila" y en "anillo"
  const posFila = [[-330, -60, 0, .52], [0, -40, 60, .62], [330, -60, 0, .52], [-330, 460, -260, .4], [0, 470, -260, .4], [330, 460, -260, .4]];
  const apar = [0, tD, tC, tE, tE + .15, tE + .3];
  const todas = [{ el: x.val }, ...x.otras.map(o => ({ el: o.m, o }))];
  todas.forEach((it, i) => {
    let px, py, pz, sc;
    const sola = [0, -10, lerp(-900, 0, ent), lerp(.55, .86, ent)];
    const a = (ang0 + i * 60) * Math.PI / 180, Rr = 620;
    const ring = [Math.sin(a) * Rr, -80, Math.cos(a) * Rr - Rr * .7, .56];
    const base = i === 0 ? sola : [posFila[i][0], posFila[i][1] + 400, -800, .2];
    const pf = posFila[i];
    const ap = i === 0 ? 1 : salida(pr(t, apar[i], apar[i] + .7));
    const mezclaF = i === 0 ? fila : ap;
    px = lerp(base[0], pf[0], mezclaF); py = lerp(base[1], pf[1], mezclaF); pz = lerp(base[2], pf[2], mezclaF); sc = lerp(base[3], pf[3], mezclaF);
    px = lerp(px, ring[0], anillo); py = lerp(py, ring[1], anillo); pz = lerp(pz, ring[2], anillo); sc = lerp(sc, ring[3], anillo);
    pz -= sal * 900;
    const o = (i === 0 ? 1 : pr(t, apar[i], apar[i] + .3)) * (1 - pr(t, 62.8, 63.1));
    vis(it.el, o);
    const ry = i === 0 ? lerp(lerp(38, -6, ent) + Math.sin(t * .8) * 4 * (1 - fila), 0, fila) : (1 - ap) * 70;
    tr(it.el, `translate(-50%,-50%) translate3d(${px}px,${py}px,${pz}px) rotateY(${ry}deg) scale(${sc})`);
    it.el.style.zIndex = Math.round(1000 + pz);
    const blur = anillo > 0 ? Math.max(0, -pz - 250) / 160 * anillo : 0;
    it.el.style.filter = blur > .3 ? `blur(${blur}px) brightness(${1 - blur * .06})` : 'none';
    if (it.o) { const loop = it.o.s === 'mateo' ? 285 : 150; const ini = it.o.s === 'mateo' ? 45 : 30; const tt = (t - apar[i]) * 30 * (it.o.s === 'mateo' ? 1.3 : 1); const f = tt < loop - ini ? ini + tt : (loop - 60) + ((tt - (loop - ini)) % 59); poner(it.o.img, it.o.s, Math.max(0, f)); }
  });
  // chips de la frase 3
  x.chips.forEach(({ ch, t: t0, j }) => {
    const q = salida(pr(t, t0, t0 + .55)), out = j < 2 ? pr(t, x.chips[j + 1].t - .05, x.chips[j + 1].t + .25) : pr(t, 62.3, 62.7);
    vis(ch, q * (1 - out)); tr(ch, `translateX(-50%) translateY(${(1 - q) * 60 - out * 60}px) rotateX(${(1 - q) * -60}deg)`);
  });
  op(x.tag, pr(t, 51.5, 52) * (1 - pr(t, 55.6, 56)));
});

/* =====================================================================
   9. INVITACIÓN WEB INTERACTIVA: imagen vs web + recorrido real
   ===================================================================== */
const MAPA_INV = [[63.6, 0], [65.4, 1.8], [68.4, 4.8], [70.2, 6.2], [71.2, 9.6], [72.6, 11.2], [73.8, 14.3], [75.0, 18.2], [76.2, 21.6], [81.0, 25.9]];
escenaDef('webinv', 62.9, 86.7, c => {
  const ia = $el('<div class="abs tag" style="left:110px;top:400px">IMAGEN DIGITAL</div>'), wa = $el('<div class="abs tag" style="left:640px;top:400px;color:#fff;border-color:#4fa3ff;box-shadow:0 0 24px rgba(79,163,255,.5)">INVITACIÓN WEB</div>');
  const tit = lineas([['INVITACIONES', '', 'font-size:84px'], ['WEB INTERACTIVAS', 'grad', 'font-size:84px']], 'cen titular', 'top:110px'); c.appendChild(tit);
  tit.querySelectorAll('.linea').forEach(l => ajustar(l, 980));
  const imgCard = marcoImagen(330, 587, 22); imgCard.style.left = '75px'; imgCard.style.top = '480px'; poner(imgCard.querySelector('img'), 'inv', 170); c.appendChild(imgCard);
  const desc1 = $el('<div class="abs" style="left:75px;width:330px;top:1100px;text-align:center;font:600 26px Inter;color:#9aa6c8">Se mira y listo.</div>');
  const desc2 = $el('<div class="abs" style="left:600px;width:420px;top:1215px;text-align:center;font:700 26px Inter;color:#cfe0ff">Se toca, se abre,<br>se recorre y se confirma.</div>');
  const vs = $el('<div class="abs" style="left:468px;top:740px;width:84px;height:84px;border-radius:50%;display:grid;place-items:center;font:800 26px Unbounded;background:linear-gradient(135deg,#2f6bff,#7b3cff);box-shadow:0 0 40px rgba(79,163,255,.6)">VS</div>');
  [ia, wa, desc1, desc2, vs].forEach(e => c.appendChild(e));
  const mundo = $el('<div class="abs" style="left:0;top:0;width:1080px;height:1920px;transform-style:flat"></div>'); c.appendChild(mundo);
  const tel = telefono(600, 1254); mundo.appendChild(tel);
  const tagDemo = $el('<div class="abs tag" style="left:50%;top:140px;transform:translateX(-50%)">GRABACIÓN REAL EN NAVEGADOR · DATOS FICTICIOS</div>'); c.appendChild(tagDemo);
  const llamadas = [['chispa', 'APERTURA<br>ANIMADA', 68.8, 70.9, 'L', 470], ['reloj', 'CUENTA REGRESIVA<br>EN VIVO', 71.2, 73.3, 'R', 640], ['pin', 'UBICACIÓN EN<br>GOOGLE MAPS', 73.4, 75.0, 'L', 860], ['galeria', 'GALERÍA<br>DE FOTOS', 74.9, 76.4, 'R', 1000], ['check', 'CONFIRMACIÓN<br>POR WHATSAPP', 76.5, 80.9, 'L', 1150], ['musica', 'MÚSICA CON<br>CONTROLES', 78.3, 80.9, 'R', 1290]];
  const chips = llamadas.map(([i, txt, a, b, lado, y]) => { const ch = chip(i, `<span style="line-height:1.15">${txt}</span>`, `${lado === 'L' ? 'left:24px' : 'right:24px'};top:${y}px;font-size:25px;padding:12px 22px 12px 14px`); c.appendChild(ch); return { ch, a, b, lado }; });
  // compartir
  const card = $el(`<div class="abs" style="left:190px;top:330px;width:700px;border-radius:26px;overflow:hidden;background:#0f1424;border:1.5px solid rgba(140,170,255,.35);box-shadow:0 40px 100px rgba(0,0,0,.7)">
    <div style="height:300px;overflow:hidden"><img style="width:100%;height:auto;margin-top:-330px"></div>
    <div style="padding:22px 26px"><div style="font:800 34px Inter">Mis XV · Valentina</div><div style="font:500 24px Inter;color:#9fb0dd;margin-top:6px">Abrí la invitación ✦ 13 de marzo</div>
    <div style="display:flex;gap:10px;align-items:center;margin-top:14px;font:600 20px Mono;color:#4fa3ff"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#4fa3ff" stroke-width="2">${ICO.enlace}</svg>enlace único del evento</div></div></div>`);
  poner(card.querySelector('img'), 'inv', 170); c.appendChild(card);
  const nombres = ['Mamá', 'Abuela', 'Tía Laura', 'Las chicas', 'Primos'];
  const contactos = nombres.map((n, i) => { const a = (i - 2) * 26 * Math.PI / 180; const el = $el(`<div class="abs" style="left:${540 + Math.sin(a) * 430 - 70}px;top:${1100 + (1 - Math.cos(a)) * 900 - 70}px;width:140px;text-align:center"><div style="width:110px;height:110px;margin:0 auto;border-radius:50%;background:linear-gradient(135deg,hsl(${220 + i * 22},80%,60%),hsl(${260 + i * 22},70%,45%));display:grid;place-items:center;font:800 40px Inter;box-shadow:0 10px 30px rgba(0,0,0,.5)">${n[0]}</div><div style="font:600 22px Inter;margin-top:10px">${n}</div><div class="ok" style="font:700 22px Inter;color:#4fa3ff">✓✓ enviado</div></div>`); c.appendChild(el); return el; });
  const vuelos = nombres.map(() => { const v = $el('<div class="abs" style="left:0;top:0;width:90px;height:60px;border-radius:14px;background:linear-gradient(135deg,#2f6bff,#7b3cff);box-shadow:0 0 24px rgba(79,163,255,.7);display:grid;place-items:center"><svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2">' + ICO.enlace + '</svg></div>'); c.appendChild(v); return v; });
  const tit2 = lineas([['UN ENLACE.', '', 'font-size:86px'], ['TODOS INVITADOS.', 'grad', 'font-size:78px']], 'cen titular', 'top:820px'); c.appendChild(tit2);
  tit2.querySelectorAll('.linea').forEach(l => ajustar(l, 980));
  return { tit, ia, wa, imgCard, desc1, desc2, vs, mundo, tel, img: tel.querySelector('img'), tagDemo, chips, card, contactos, vuelos, tit2 };
}, (t, x) => {
  animarChars(x.tit, t, 63.2, .025, .7, 68.0);
  // comparación (63–68.3)
  const e = salida(pr(t, 63.0, 63.9)), fuera = suave(pr(t, 67.8, 68.7));
  [x.ia, x.imgCard, x.desc1].forEach(el => { vis(el, e * (1 - fuera)); tr(el, `translateX(${-fuera * 500}px) translateY(${(1 - e) * 60}px)`); el.style.filter = fuera > 0 ? `blur(${fuera * 10}px) grayscale(1)` : 'grayscale(.6)'; });
  [x.wa, x.desc2, x.vs].forEach(el => { vis(el, e * (1 - fuera)); });
  // teléfono: chico a la derecha -> grande al centro -> se achica para compartir
  const comp = suave(pr(t, 81.0, 81.9));
  const cx = lerp(lerp(820, 540, fuera), 300, comp), cy = lerp(lerp(840, 857, fuera), 1290, comp), sc = lerp(lerp(.56, 1, fuera), .42, comp);
  const zoom = suave(pr(t, 71.0, 71.6)) * (1 - suave(pr(t, 72.9, 73.5)));
  vis(x.tel, e * (1 - pr(t, 81.6, 82.3)));
  tr(x.tel, `translate(${cx - 300}px,${cy - 627}px) scale(${sc * (1 + zoom * .16)}) rotateY(${Math.sin(t * .6) * 7 * (1 - comp)}deg) rotateX(${Math.sin(t * .45) * 3}deg)`);
  x.tel.style.transformOrigin = `300px ${lerp(627, 380, zoom)}px`;
  poner(x.img, 'inv', fr(mapa(MAPA_INV, t)));
  op(x.tagDemo, pr(t, 69.0, 69.5) * (1 - pr(t, 80.6, 81)));
  x.chips.forEach(({ ch, a, b, lado }) => { const q = salida(pr(t, a, a + .5)), s = suave(pr(t, b - .3, b)); vis(ch, q * (1 - s)); tr(ch, `translateX(${(1 - q) * (lado === 'L' ? -260 : 260)}px) translateY(${Math.sin(t * 1.4 + a) * 5}px)`); ch.style.filter = q < .97 ? `blur(${(1 - q) * 10}px)` : 'none'; });
  // compartir (81–86.5)
  const ce = salida(pr(t, 81.7, 82.5)), cs = suave(pr(t, 85.9, 86.5));
  vis(x.card, ce * (1 - cs)); tr(x.card, `translateY(${(1 - ce) * 260}px) scale(${.7 + .3 * ce}) rotateX(${(1 - ce) * 30}deg)`);
  animarChars(x.tit2, t, 82.5, .025, .7, 85.9);
  x.contactos.forEach((cn, i) => { const t0 = 83.0 + i * .28; const q = eob(pr(t, t0 - .3, t0 + .2)); vis(cn, pr(t, t0 - .3, t0) * (1 - cs)); tr(cn, `scale(${q})`); cn.querySelector('.ok').style.opacity = pr(t, t0 + .5, t0 + .7); });
  x.vuelos.forEach((v, i) => {
    const t0 = 83.0 + i * .28, k = pr(t, t0, t0 + .5); const a = (i - 2) * 26 * Math.PI / 180;
    const x0 = 540, y0 = 560, x1 = 540 + Math.sin(a) * 430, y1 = 1100 + (1 - Math.cos(a)) * 900;
    const u = suave(k); vis(v, k > 0 && k < 1 ? Math.sin(k * Math.PI) * 1.2 : 0);
    tr(v, `translate(${lerp(x0, x1, u) - 45}px,${lerp(y0, y1, u) - 30 - Math.sin(u * Math.PI) * 160}px) scale(${.6 + .4 * Math.sin(u * Math.PI)})`);
  });
});

/* =====================================================================
   10. PÁGINAS WEB: wireframe -> tienda -> servicios -> gastronomía
   ===================================================================== */
const MAPAS_WEB = {
  tiendaD: [[88.8, 0], [96.5, 9.0]], tiendaM: [[91.3, 0], [96.5, 6.9]],
  servD: [[96.5, 0], [102.5, 10.4]], servM: [[96.8, 0], [102.5, 6.0]],
  brasaD: [[102.5, 0], [108.6, 9.0]], brasaM: [[102.8, 0], [108.6, 7.0]]
};
escenaDef('webs', 86.4, 109.3, c => {
  const tit = lineas([['TU NEGOCIO', '', 'font-size:96px'], ['EN INTERNET', 'grad', 'font-size:96px']], 'cen titular', 'top:110px'); c.appendChild(tit);
  tit.querySelectorAll('.linea').forEach(l => ajustar(l, 980));
  const mundo = $el('<div class="abs p3d" style="left:0;top:0;width:1080px;height:1920px"></div>'); c.appendChild(mundo);
  const navs = [['tiendaD', 'orbe-tienda · demo'], ['servD', 'habitar-servicios · demo'], ['brasaD', 'brasa-burgers · demo']].map(([s, u]) => { const n = navegador(960, 646, u); mundo.appendChild(n); return { n, s, img: n.querySelector('img') }; });
  const tels = ['tiendaM', 'servM', 'brasaM'].map(s => { const tl = telefono(290, 628); mundo.appendChild(tl); return { tl, s, img: tl.querySelector('img') }; });
  // wireframe
  const wf = $el(`<svg class="abs" style="left:60px;top:516px" width="960" height="600" viewBox="0 0 960 600"><g fill="none" stroke="#4fa3ff" stroke-width="2.5">
    <rect x="30" y="20" width="120" height="30" rx="6"/><rect x="560" y="26" width="300" height="18" rx="9"/><rect x="890" y="18" width="40" height="34" rx="17"/>
    <rect x="30" y="100" width="420" height="40" rx="8"/><rect x="30" y="160" width="360" height="40" rx="8"/><rect x="30" y="230" width="300" height="16" rx="8"/><rect x="30" y="258" width="260" height="16" rx="8"/>
    <rect x="30" y="310" width="170" height="54" rx="27"/><rect x="215" y="310" width="190" height="54" rx="27"/><rect x="510" y="90" width="420" height="420" rx="28"/>
    <path d="M510 90 L930 510 M930 90 L510 510"/><rect x="30" y="420" width="90" height="40" rx="6"/><rect x="140" y="420" width="90" height="40" rx="6"/><rect x="250" y="420" width="90" height="40" rx="6"/></g></svg>`);
  mundo.appendChild(wf);
  const wfEls = [...wf.querySelectorAll('rect,path')];
  wfEls.forEach(e => { e.setAttribute('pathLength', 1); e.style.strokeDasharray = 1; e.style.strokeDashoffset = 1; e.dataset.l = 1; });
  const rubros = ['COMERCIOS', 'SERVICIOS', 'GASTRONOMÍA', 'SALUD', 'EDUCACIÓN', 'PROFESIONALES'];
  const pills = rubros.map((r, i) => { const p = $el(`<div class="chip abs" style="font-size:24px;padding:12px 22px">${r}</div>`); c.appendChild(p); return p; });
  const etiquetas = ['TIENDA ONLINE', 'LANDING DE SERVICIOS', 'GASTRONOMÍA'].map(e => { const d = $el(`<div class="abs tag" style="left:60px;top:440px;font-size:22px;color:#fff;border-color:#4fa3ff">${e}</div>`); c.appendChild(d); return d; });
  const ll = [
    ['filtro', 'CATÁLOGO<br>CON FILTROS', 92.4, 94.0], ['carrito', 'CARRITO<br>DE COMPRAS', 94.2, 96.2], ['movil', 'ADAPTADA<br>A CELULARES', 92.0, 96.2, 1],
    ['web', 'SECCIÓN DE<br>SERVICIOS', 97.6, 99.0], ['galeria', 'GALERÍA DE<br>TRABAJOS', 98.7, 100.0], ['form', 'FORMULARIO<br>DE CONTACTO', 99.8, 102.3],
    ['menu', 'MENÚ<br>DIGITAL', 104.1, 105.5], ['carrito', 'PEDIDO<br>ARMADO', 105.4, 107.2], ['check', 'PEDIDOS POR<br>WHATSAPP', 107.4, 108.9]
  ];
  const chips = ll.map(([i, txt, a, b, alto]) => { const ch = chip(i, `<span style="line-height:1.15">${txt}</span>`, `left:60px;top:${alto ? 1340 : 1200}px;font-size:25px;padding:12px 22px 12px 14px`); c.appendChild(ch); return { ch, a, b }; });
  return { tit, navs, tels, wf, wfEls, pills, etiquetas, chips };
}, (t, x) => {
  animarChars(x.tit, t, 86.8, .03, .7, null);
  const tsub = suave(pr(t, 90.0, 90.8));
  tr(x.tit, `translateY(${-tsub * 40}px) scale(${1 - tsub * .32})`); x.tit.style.transformOrigin = '540px 0';
  // wireframe
  const wfE = salida(pr(t, 86.9, 87.6)), wfS = pr(t, 88.6, 89.6);
  vis(x.wf, wfE * (1 - wfS));
  x.wfEls.forEach((e, i) => { const k = suave(pr(t, 87.0 + i * .08, 87.9 + i * .08)); e.style.strokeDashoffset = e.dataset.l * (1 - k); });
  const sitios = [[88.6, 96.2, 96.9], [96.2, 102.2, 102.9], [102.2, 109.4, 109.4]];
  x.navs.forEach((nv, i) => {
    const [a, b, b2] = sitios[i];
    const ent = i === 0 ? salida(pr(t, 86.9, 87.7)) : suave(pr(t, a, a + .7));
    const sal = i === 2 ? 0 : suave(pr(t, b, b2));
    // al final: pila de las tres webs en profundidad
    const pila = suave(pr(t, 108.0, 108.9));
    let tx = (1 - ent) * 700 - sal * 700, ry = (1 - ent) * 70 - sal * 70 + Math.sin(t * .5) * 4, tz = 0, ty = 0;
    if (pila > 0) { const k = 2 - i; tx = -k * 60 * pila; ty = -k * 90 * pila; tz = -k * 260 * pila; ry = 10 * pila; }
    const o = (i === 0 ? 1 : ent) * (1 - sal) + (pila > 0 && i < 2 ? pila * .8 : 0);
    vis(nv.n, Math.min(1, o) * (1 - pr(t, 109.0, 109.3)));
    nv.n.style.left = '60px'; nv.n.style.top = '470px';
    tr(nv.n, `translate3d(${tx}px,${ty}px,${tz}px) rotateY(${ry}deg) rotateX(4deg) scale(${1 - pila * .12})`);
    const m = MAPAS_WEB[nv.s];
    if (o > 0) {
      if (i === 0) nv.img.style.opacity = pr(t, 88.6, 89.6);
      poner(nv.img, nv.s, fr(mapa(m, t)));
    }
  });
  const telT = [[91.3, 96.2], [96.8, 102.2], [102.8, 108.0]];
  x.tels.forEach((tl, i) => {
    const [a, b] = telT[i];
    const q = salida(pr(t, a, a + .8)), s = suave(pr(t, b, b + .6));
    vis(tl.tl, q * (1 - s));
    tl.tl.style.left = '720px'; tl.tl.style.top = '880px';
    tr(tl.tl, `translate3d(${(1 - q) * 400 + s * 400}px,${Math.sin(t * 1.1) * 10}px,140px) rotateY(${-16 + Math.sin(t * .7) * 4}deg)`);
    if (q > 0) poner(tl.img, tl.s, fr(mapa(MAPAS_WEB[tl.s], t)));
  });
  // rubros
  const anchos = x.pills.map(p => p.offsetWidth);
  const filas = [[0, 1, 2], [3, 4, 5]];
  filas.forEach((f, fi) => { const tot = f.reduce((a, j) => a + anchos[j], 0) + 14 * (f.length - 1); let xx = 540 - tot / 2; f.forEach(j => { x.pills[j].style.left = xx + 'px'; x.pills[j].style.top = (1220 + fi * 92) + 'px'; xx += anchos[j] + 14; }); });
  x.pills.forEach((p, j) => { const q = eob(pr(t, 87.6 + j * .14, 88.0 + j * .14)), s = suave(pr(t, 90.6, 91.2)); vis(p, pr(t, 87.6 + j * .14, 87.8 + j * .14) * (1 - s)); tr(p, `scale(${q * (1 - s * .3)}) translateY(${s * 40}px)`); });
  x.etiquetas.forEach((e, i) => { const [a, b] = [[90.5, 96.2], [96.6, 102.2], [102.6, 108.0]][i]; const q = salida(pr(t, a, a + .5)); vis(e, q * (1 - pr(t, b, b + .4))); tr(e, `translateX(${(1 - q) * -40}px)`); });
  x.chips.forEach(({ ch, a, b }) => { const q = salida(pr(t, a, a + .5)), s = suave(pr(t, b - .3, b)); vis(ch, q * (1 - s)); tr(ch, `translateX(${(1 - q) * -260}px) translateY(${Math.sin(t * 1.3 + a) * 5}px)`); ch.style.filter = q < .97 ? `blur(${(1 - q) * 10}px)` : 'none'; });
});

/* =====================================================================
   11. CIERRE: convergencia + mensajes + servicios + escribinos
   ===================================================================== */
escenaDef('cierre', 108.9, 123.3, c => {
  const mundo = $el('<div class="abs p3d" style="left:540px;top:860px;width:0;height:0"></div>'); c.appendChild(mundo);
  const pDemo = marcoImagen(300, 533, 22); const pTel = telefono(250, 540); const pNav = navegador(470, 330, 'tu-web · demo');
  [pDemo, pTel, pNav].forEach(p => { p.style.left = '0'; p.style.top = '0'; mundo.appendChild(p); });
  poner(pTel.querySelector('img'), 'inv', 170); poner(pNav.querySelector('img'), 'tiendaD', 120);
  const glow = $el('<div class="abs" style="left:540px;top:860px;width:600px;height:600px;margin:-300px;border-radius:50%;background:radial-gradient(circle,rgba(190,215,255,.95),rgba(79,163,255,.5) 25%,rgba(123,60,255,.2) 50%,transparent 70%)"></div>'); c.appendChild(glow);
  const t1 = lineas([['TUS IDEAS.', '', 'font-size:120px'], ['NUESTRA', '', 'font-size:104px;margin-top:14px'], ['CREATIVIDAD.', 'grad', 'font-size:104px']], 'cen titular', 'top:620px'); c.appendChild(t1);
  const t2 = lineas([['HACEMOS QUE TUS', '', 'font-size:70px'], ['PROYECTOS', '', 'font-size:110px;margin-top:8px'], ['DESTAQUEN', 'grad', 'font-size:110px']], 'cen titular', 'top:640px'); c.appendChild(t2);
  [t1, t2].forEach(b => b.querySelectorAll('.linea').forEach(l => ajustar(l, 980)));
  const serv = [['play', 'EDICIÓN DE VIDEOS'], ['tarjeta', 'INVITACIONES DIGITALES Y WEB'], ['codigo', 'DESARROLLO DE PÁGINAS WEB']].map(([i, txt], j) => {
    const r = $el(`<div class="abs" style="left:90px;top:${900 + j * 150}px;width:900px;height:120px;display:flex;align-items:center;gap:28px;border-bottom:1px solid rgba(160,190,255,.25)"><span style="width:84px;height:84px;border-radius:24px;display:grid;place-items:center;background:linear-gradient(135deg,#2f6bff,#7b3cff);box-shadow:0 0 30px rgba(79,163,255,.5)"><svg viewBox="0 0 24 24" style="width:42px;height:42px;fill:none;stroke:#fff;stroke-width:2;stroke-linecap:round;stroke-linejoin:round">${ICO[i]}</svg></span><span style="font:800 40px Inter;letter-spacing:.02em">${txt}</span></div>`);
    c.appendChild(r); return r; });
  const t3 = lineas([['CONTANOS', '', 'font-size:96px'], ['QUÉ TENÉS', '', 'font-size:96px'], ['EN MENTE', 'grad', 'font-size:96px']], 'cen titular', 'top:380px'); c.appendChild(t3);
  t3.querySelectorAll('.linea').forEach(l => ajustar(l, 980));
  const barra = $el(`<div class="abs" style="left:70px;top:1180px;width:940px;height:110px;border-radius:55px;background:rgba(18,22,38,.92);border:1.5px solid rgba(160,190,255,.35);display:flex;align-items:center;padding:0 16px 0 40px;box-shadow:0 30px 80px rgba(0,0,0,.6)"><span class="txt" style="flex:1;font:500 36px Inter;color:#fff;white-space:nowrap;overflow:hidden"></span><span class="env" style="width:80px;height:80px;border-radius:50%;background:#25d366;display:grid;place-items:center"><svg width="38" height="38" viewBox="0 0 24 24"><path d="M3 12l18-8-7 18-3-7z" fill="#fff"/></svg></span></div>`); c.appendChild(barra);
  const burbuja = $el('<div class="abs" style="left:0;top:0;padding:26px 34px;border-radius:34px 34px 8px 34px;background:linear-gradient(135deg,#1fa855,#25d366);font:600 34px Inter;white-space:nowrap;box-shadow:0 20px 60px rgba(37,211,102,.4)">Hola, quiero consultar por un proyecto ✓✓</div>'); c.appendChild(burbuja);
  return { mundo, pDemo, pTel, pNav, glow, t1, t2, serv, t3, barra, txt: barra.querySelector('.txt'), env: barra.querySelector('.env'), burbuja };
}, (t, x) => {
  // órbita y convergencia (109–112.4)
  const conv = ei(pr(t, 111.4, 112.4)), ent = salida(pr(t, 109.0, 109.9));
  const ang = (t - 109) * 55;
  [[x.pDemo, 0, 'demo'], [x.pTel, 120], [x.pNav, 240]].forEach(([p, a0, s]) => {
    const a = (ang + a0) * Math.PI / 180, Rr = 400 * (1 - conv) * ent + 40;
    vis(p, ent * (1 - pr(t, 112.2, 112.45)));
    tr(p, `translate(-50%,-50%) translate3d(${Math.sin(a) * Rr}px,${Math.cos(a) * Rr * .35 - 40}px,${Math.cos(a) * Rr - 200}px) scale(${lerp(1.3, .25, conv)}) rotateY(${Math.sin(a) * -25}deg)`);
    if (s) poner(p.querySelector('img'), 'demo', 255 + ((t - 109) * 30) % 44);
  });
  const g = Math.max(pr(t, 111.6, 112.4) * (1 - pr(t, 112.4, 113.2)), 0);
  vis(x.glow, g * .75); tr(x.glow, `scale(${.3 + g * 1.1})`);
  animarChars(x.t1, t, 112.55, .035, .7, 115.6);
  animarChars(x.t2, t, palabraDe('v16', 'Dale') - .3 > 115.7 ? 115.8 : 115.8, .03, .7, 119.0);
  const up = suave(pr(t, 117.3, 118.0));
  tr(x.t2, `translateY(${-up * 360}px) scale(${1 - up * .25})`);
  x.serv.forEach((r, j) => { const q = salida(pr(t, 117.7 + j * .22, 118.4 + j * .22)), s = suave(pr(t, 118.9 + j * .05, 119.4 + j * .05)); vis(r, q * (1 - s)); tr(r, `translateX(${(1 - q) * -200}px) translateY(${-s * 80}px)`); r.style.filter = q < .97 ? `blur(${(1 - q) * 10}px)` : 'none'; });
  // escribinos (119–123)
  animarChars(x.t3, t, 119.35, .025, .7, 122.6);
  const be = salida(pr(t, 119.7, 120.3)), bs = suave(pr(t, 122.5, 122.9));
  vis(x.barra, be * (1 - bs)); tr(x.barra, `translateY(${(1 - be) * 100}px)`);
  const msg = 'Hola, quiero consultar por un proyecto';
  const n = Math.floor(pr(t, 120.2, 121.7) * msg.length); x.txt.textContent = msg.slice(0, n) + (t < 121.9 && (t * 2 % 1) < .5 ? '|' : '');
  tr(x.env, `scale(${1 + .15 * Math.sin(pr(t, 121.8, 122.2) * Math.PI)})`);
  const vb = suave(pr(t, 122.0, 122.6)), vb2 = ei(pr(t, 122.6, 123.1));
  vis(x.burbuja, pr(t, 121.95, 122.05) * (1 - pr(t, 123.0, 123.2)));
  const bx = lerp(lerp(560, 330, vb), 540, vb2), by = lerp(lerp(1180, 900, vb), 540, vb2);
  tr(x.burbuja, `translate(${bx - 380}px,${by}px) scale(${lerp(.6, 1, vb) * (1 - vb2 * .7)})`);
  x.burbuja.style.filter = vb2 > 0 ? `blur(${vb2 * 6}px)` : 'none';
});

/* =====================================================================
   12. CONTACTO: WhatsApp + número + pedido de presupuesto
   ===================================================================== */
escenaDef('contacto', 122.9, 132.6, c => {
  const anillos = [0, 1, 2].map(() => { const a = $el('<div class="abs" style="left:540px;top:500px;width:300px;height:300px;margin:-150px;border-radius:50%;border:4px solid #25d366"></div>'); c.appendChild(a); return a; });
  const ico = $el(`<div class="abs" style="left:540px;top:500px;width:270px;height:270px;margin:-135px;filter:drop-shadow(0 0 50px rgba(37,211,102,.65))">${WAPP}</div>`); c.appendChild(ico);
  const tit = lineas([['¡PEDÍ TU', '', 'font-size:104px'], ['PRESUPUESTO!', 'grad', 'font-size:104px']], 'cen titular', 'top:700px'); c.appendChild(tit);
  tit.querySelectorAll('.linea').forEach(l => ajustar(l, 1000));
  const lab = $el('<div class="cen" style="top:985px"><span class="chip" style="font-size:28px"><span style="width:14px;height:14px;border-radius:50%;background:#25d366;box-shadow:0 0 14px #25d366"></span>CONSULTAS POR WHATSAPP</span></div>'); c.appendChild(lab);
  const num = $el(`<div class="cen" style="top:1090px;font:900 100px/1 'Inter Display',Inter;letter-spacing:-.01em;color:#fff;text-shadow:0 0 40px rgba(79,163,255,.55)">${[...'+54 9 381 585 9396'].map(ch => `<span class="dig" style="display:inline-block;white-space:pre">${ch}</span>`).join('')}</div>`); c.appendChild(num);
  ajustar(num, 1010);
  const link = $el('<div class="cen" style="top:1230px;font:600 34px Mono;color:#7fb4ff">wa.me/5493815859396</div>'); c.appendChild(link);
  const pie = $el('<div class="cen" style="top:1350px;font:700 26px Inter;letter-spacing:.16em;color:#aab6d8">EDICIÓN DE VIDEOS · INVITACIONES · PÁGINAS WEB</div>'); c.appendChild(pie);
  ajustar(pie, 980);
  const haz = $el('<div class="abs" style="left:0;top:1060px;width:240px;height:170px;background:linear-gradient(90deg,transparent,rgba(255,255,255,.55),transparent);transform:skewX(-20deg);mix-blend-mode:overlay;filter:blur(6px)"></div>'); c.appendChild(haz);
  return { anillos, ico, tit, lab, num, digs: [...num.querySelectorAll('.dig')], link, pie, haz };
}, (t, x) => {
  const ie = eob(pr(t, 122.9, 123.6));
  vis(x.ico, pr(t, 122.9, 123.1)); tr(x.ico, `scale(${ie * (1 + Math.sin(t * 4) * .025)})`);
  x.anillos.forEach((a, i) => { const k = ((t - 123.3 + i * .55) / 1.65) % 1; vis(a, t > 123.3 ? (1 - k) * .7 : 0); tr(a, `scale(${.9 + k * 1.3})`); });
  animarChars(x.tit, t, 123.25, .03, .7, null);
  const le = salida(pr(t, 123.8, 124.3)); vis(x.lab, le); tr(x.lab, `translateY(${(1 - le) * 30}px)`);
  x.digs.forEach((d, i) => { const t0 = 124.0 + i * .045; const q = eob(pr(t, t0, t0 + .45)); d.style.opacity = pr(t, t0, t0 + .15); d.style.transform = `translateY(${(1 - q) * 70}px) scale(${.6 + .4 * q})`; d.style.filter = q < .98 ? `blur(${(1 - q) * 8}px)` : 'none'; });
  const lk = salida(pr(t, 124.9, 125.4)); vis(x.link, lk); tr(x.link, `translateY(${(1 - lk) * 20}px)`);
  const pe = salida(pr(t, 125.4, 126)); vis(x.pie, pe);
  const hz = pr(t, 129.4, 130.3); vis(x.haz, hz > 0 && hz < 1 ? 1 : 0); x.haz.style.left = lerp(-300, 1200, eio(hz)) + 'px';
});

/* ===================================================================== render */
rafaga(5.8, 540, 860, 70, ['190,215,255', '123,60,255', '79,163,255'], 900, 2);
rafaga(112.4, 540, 860, 110, ['190,215,255', '123,60,255', '79,163,255', '255,255,255'], 1000, 3);
rafaga(123.0, 540, 500, 60, ['37,211,102', '190,215,255', '79,163,255'], 700, 4);
const FLASHES = [[5.78, .95, .55], [13.95, .45, .4], [17.38, .55, .35], [27.5, .3, .4], [43.0, .3, .2], [43.35, .3, .2], [43.7, .4, .25], [44.98, .75, .45], [63.0, .5, .4], [86.48, .45, .4], [109.0, .55, .45], [112.4, .55, .45], [123.0, .4, .4]];
const BARRIDOS = [13.7, 36.35, 56.0, 81.0, 96.15, 102.15, 119.0];
async function render(t) {
  pendientes = [];
  dibujarFondo(t);
  for (const e of ESC) { const on = t >= e.desde && t < e.hasta; mostrar(e.c, on); if (on) e.upd(t, e.ctx); }
  const rayas = pr(t, .3, 1.0) * (1 - pr(t, 5.4, 6.0)) + .5 * pr(t, 16.6, 17.2) * (1 - pr(t, 17.4, 17.6));
  const negro = Math.max(1 - pr(t, 0, .35), pr(t, 132.0, 132.5));
  dibujarFx(t, { rayas, negro });
  subtitulos(t, !(t > 17.45 && t < 27.6));
  flashes(t, FLASHES); barridos(t, BARRIDOS);
  await Promise.all(pendientes);
}
window.render = render; window.DURACION = TL.duracion;
