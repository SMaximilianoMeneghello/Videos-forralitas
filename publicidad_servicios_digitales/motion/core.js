/* Núcleo de la composición: utilidades, capas de imagen, fondo, efectos y subtítulos.
   Todo se dibuja en función del tiempo t (determinista), así cada cuadro se puede renderizar por separado. */
const W = 1080, H = 1920, FPS = 30;
const BUILD = '../build';
const cl = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const pr = (t, a, b) => cl((t - a) / (b - a));
const lerp = (a, b, x) => a + (b - a) * x;
const eo = x => 1 - Math.pow(1 - cl(x), 3);
const eo5 = x => 1 - Math.pow(1 - cl(x), 5);
const ei = x => Math.pow(cl(x), 3);
const eio = x => (x = cl(x), x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
const eob = x => { x = cl(x); const c1 = 1.6, c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); };
// curva bezier tipo After Effects (ease in/out con influencia)
function bez(p1x, p1y, p2x, p2y) {
  return x => { x = cl(x); let lo = 0, hi = 1, u = .5;
    for (let i = 0; i < 22; i++) { u = (lo + hi) / 2; const bx = 3 * (1 - u) * (1 - u) * u * p1x + 3 * (1 - u) * u * u * p2x + u * u * u; if (bx < x) lo = u; else hi = u; }
    return 3 * (1 - u) * (1 - u) * u * p1y + 3 * (1 - u) * u * u * p2y + u * u * u; };
}
const suave = bez(.7, 0, .2, 1), salida = bez(.16, 1, .3, 1), entrada = bez(.7, 0, .84, 0);
function rng(seed) { return () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const $el = (html) => { const d = document.createElement('div'); d.innerHTML = html.trim(); return d.firstChild; };
const escena = document.getElementById('escena');
function capa(nombre) { const c = $el(`<div class="capa" id="c_${nombre}"></div>`); escena.appendChild(c); return c; }
function mostrar(el, on) { const v = on ? 'block' : 'none'; if (el.style.display !== v) el.style.display = v; }
function tr(el, s) { el.style.transform = s; }
function op(el, o) { el.style.opacity = cl(o); }
function vis(el, o) { op(el, o); const v = o > .002 ? '' : 'hidden'; if (el.style.visibility !== v) el.style.visibility = v; }
function palabra(id, i) { return VOZ[id].palabras[i].t; }
function palabraDe(id, txt, desde = 0) { const p = VOZ[id].palabras; for (let i = desde; i < p.length; i++) if (p[i].w.toLowerCase().startsWith(txt.toLowerCase())) return p[i].t; return VOZ[id].t; }

/* ---------- capas de secuencias de imágenes (capturas reales y la demo) ---------- */
let pendientes = [];
const SEQ = {
  inv: { dir: 'cap/invitacion15_movil', n: 780, d: 5 }, mateo: { dir: 'cap/invitacion18_mateo', n: 285, d: 5 },
  infantil: { dir: 'cap/cel_cumple_infantil', n: 150, d: 5 }, comunion: { dir: 'cap/cel_comunion', n: 150, d: 5 },
  aniversario: { dir: 'cap/cel_aniversario', n: 150, d: 5 }, baby: { dir: 'cap/cel_baby_shower', n: 150, d: 5 },
  tiendaD: { dir: 'cap/tienda_desktop', n: 270, d: 5 }, tiendaM: { dir: 'cap/tienda_movil', n: 210, d: 5 },
  servD: { dir: 'cap/servicios_desktop', n: 315, d: 5 }, servM: { dir: 'cap/servicios_movil', n: 180, d: 5 },
  brasaD: { dir: 'cap/brasa_desktop', n: 270, d: 5 }, brasaM: { dir: 'cap/brasa_movil', n: 210, d: 5 },
  demo: { dir: 'demo', n: 300, d: 4 }, raw: { dir: 'demo_raw', n: 300, d: 4 }
};
function src(seq, i) { const s = SEQ[seq]; i = Math.max(0, Math.min(s.n - 1, Math.round(i))); return `${BUILD}/${s.dir}/f${String(i).padStart(s.d, '0')}.jpg`; }
function poner(img, seq, i) {
  const u = src(seq, i);
  if (img.dataset.u !== u) { img.dataset.u = u; img.src = u; pendientes.push(img.decode().catch(() => {})); }
}
// segundos de captura -> índice de cuadro
const fr = s => s * FPS;
// mapa de tiempo por tramos [(t_publicidad, t_captura)]
function mapa(puntos, t) {
  if (t <= puntos[0][0]) return puntos[0][1];
  for (let i = 1; i < puntos.length; i++) if (t <= puntos[i][0]) { const [a, x] = puntos[i - 1], [b, y] = puntos[i]; return lerp(x, y, (t - a) / (b - a)); }
  return puntos[puntos.length - 1][1];
}

/* ---------- componentes ---------- */
function telefono(w, h, extra = '') {
  return $el(`<div class="tel" style="width:${w}px;height:${h}px;--r:${Math.round(w * .14)}px;--b:${Math.round(w * .032)}px"><div class="pant"><img alt="">${extra}<div class="isla"></div><div class="brillo"></div></div></div>`);
}
function navegador(w, h, url) {
  return $el(`<div class="nav" style="width:${w}px;height:${h}px"><div class="barra"><i style="background:#ff5f57"></i><i style="background:#febc2e"></i><i style="background:#28c840"></i><div class="url"><svg width="12" height="14" viewBox="0 0 12 14"><rect x="1" y="6" width="10" height="7" rx="1.5" fill="#8b93ad"/><path d="M3 6V4a3 3 0 0 1 6 0v2" stroke="#8b93ad" fill="none" stroke-width="1.6"/></svg>${url}</div></div><div class="cont"><img alt=""></div></div>`);
}
const ICO = {
  play: '<path d="M8 5l12 7-12 7z"/>', tarjeta: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 9h18M7 14h5"/>',
  web: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>', codigo: '<path d="M8 8l-5 4 5 4M16 8l5 4-5 4M14 5l-4 14"/>',
  reloj: '<circle cx="12" cy="13" r="8"/><path d="M12 9v4l3 2M9 2h6"/>', pin: '<path d="M12 21s-7-6.500-7-12a7 7 0 0 1 14 0c0 5.500-7 12-7 12z"/><circle cx="12" cy="9" r="2.500"/>',
  galeria: '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="M21 16l-5-5-9 9"/>', check: '<path d="M5 12l5 5 9-10"/>',
  musica: '<path d="M9 18V6l11-2v12"/><circle cx="6.500" cy="18" r="2.500"/><circle cx="17.500" cy="16" r="2.500"/>', chispa: '<path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.500 2.500M15.500 15.500L18 18M6 18l2.500-2.500M15.500 8.500L18 6"/>',
  carrito: '<path d="M4 5h2l2 11h10l2-8H7"/><circle cx="10" cy="20" r="1.500"/><circle cx="17" cy="20" r="1.500"/>', filtro: '<path d="M4 5h16l-6 8v6l-4-2v-4z"/>',
  movil: '<rect x="7" y="2" width="10" height="20" rx="2"/><path d="M11 18h2"/>', form: '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 8h8M8 12h8M8 16h5"/>',
  menu: '<path d="M4 6h16M4 12h16M4 18h10"/>', enlace: '<path d="M10 14a4 4 0 0 0 6 0l3-3a4 4 0 0 0-6-6l-1 1M14 10a4 4 0 0 0-6 0l-3 3a4 4 0 0 0 6 6l1-1"/>',
  color: '<circle cx="12" cy="12" r="9"/><path d="M12 3v18M3 12h18"/>', capas: '<path d="M12 3l9 5-9 5-9-5z"/><path d="M3 13l9 5 9-5"/>'
};
function chip(icono, texto, extraCss = '') { return $el(`<div class="chip abs" style="${extraCss}"><span class="ico"><svg viewBox="0 0 24 24">${ICO[icono]}</svg></span>${texto}</div>`); }
// texto dividido en caracteres dentro de líneas con máscara
function lineas(lista, clase, estilo) {
  const d = $el(`<div class="${clase}" style="${estilo}"></div>`);
  lista.forEach(([txt, cls, st]) => {
    const l = $el(`<span class="linea ${cls || ''}" style="${st || ''}"></span>`);
    [...txt].forEach(c => { const s = document.createElement('span'); s.className = 'ch' + (cls && cls.includes('grad') ? ' grad' : ''); s.textContent = c; l.appendChild(s); });
    d.appendChild(l);
  });
  return d;
}
// animación de caracteres: entrada desde abajo con desenfoque y rotación 3D
function animarChars(cont, t, t0, paso = .025, dur = .7, sal = null) {
  cont.querySelectorAll('.linea').forEach((l, li) => {
    l.querySelectorAll('.ch').forEach((c, i) => {
      const k = salida(pr(t, t0 + li * .14 + i * paso, t0 + li * .14 + i * paso + dur));
      let y = (1 - k) * 110, o = k, b = (1 - k) * 12, rx = (1 - k) * -70;
      if (sal) { const q = suave(pr(t, sal + i * .012, sal + i * .012 + .4)); y -= q * 110; o *= 1 - q; b += q * 10; }
      c.style.transform = `translateY(${y}%) rotateX(${rx}deg)`; c.style.opacity = o; c.style.filter = b > .3 ? `blur(${b}px)` : 'none';
    });
  });
}
// ajusta el tamaño de fuente para que una línea no supere el ancho dado
function ajustar(el, maxW) { let fs = parseFloat(getComputedStyle(el).fontSize); el.style.whiteSpace = 'nowrap'; while (el.scrollWidth > maxW && fs > 10) { fs -= 2; el.style.fontSize = fs + 'px'; } }

/* ---------- fondo animado ---------- */
const fc = document.getElementById('fondo').getContext('2d');
const R = rng(77);
const polvo = Array.from({ length: 140 }, () => ({ x: R() * W, y: R() * H, z: .2 + R() * 1, f: R() * 6.3, v: 8 + R() * 30 }));
const grano = document.createElement('canvas'); grano.width = 540; grano.height = 960;
{ const g = grano.getContext('2d'), id = g.createImageData(540, 960); for (let i = 0; i < id.data.length; i += 4) { const v = R() * 255; id.data[i] = id.data[i + 1] = id.data[i + 2] = v; id.data[i + 3] = 18; } g.putImageData(id, 0, 0); }
// paleta por sección: [color blob 1, color blob 2, intensidad, rejilla]
function ambiente(t) {
  const P = [
    [0, [47, 107, 255], [123, 60, 255], .55, 0], [6, [47, 107, 255], [123, 60, 255], .7, 0],
    [14, [40, 110, 255], [30, 200, 255], .55, 1], [27.5, [40, 110, 255], [123, 60, 255], .55, 1],
    [45, [123, 60, 255], [200, 90, 255], .65, 0], [63, [47, 107, 255], [123, 60, 255], .6, 0],
    [86.5, [47, 107, 255], [80, 200, 255], .55, 1], [109, [47, 107, 255], [123, 60, 255], .75, 0], [123, [37, 160, 110], [47, 107, 255], .6, 0]
  ];
  let a = P[0], b = P[0];
  for (let i = 0; i < P.length; i++) { if (t >= P[i][0]) { a = P[i]; b = P[i + 1] || P[i]; } }
  const k = b === a ? 0 : eio(pr(t, b[0] - 1.2, b[0]));
  const mix = (u, v) => u.map((x, i) => Math.round(lerp(x, v[i], k)));
  return { c1: mix(a[1], b[1]), c2: mix(a[2], b[2]), i: lerp(a[3], b[3], k), grid: lerp(a[4], b[4], k) };
}
function dibujarFondo(t) {
  const A = ambiente(t);
  fc.globalCompositeOperation = 'source-over';
  fc.fillStyle = '#04050a'; fc.fillRect(0, 0, W, H);
  fc.globalCompositeOperation = 'lighter';
  const blobs = [[A.c1, .3, .25, 0], [A.c2, .75, .6, 2.1], [A.c1, .2, .85, 4.2], [A.c2, .6, .1, 5.3]];
  blobs.forEach(([c, bx, by, f], i) => {
    const x = W * (bx + .18 * Math.sin(t * .23 + f)), y = H * (by + .07 * Math.cos(t * .19 + f * 1.3)), r = 760;
    const g = fc.createRadialGradient(x, y, 0, x, y, r);
    g.addColorStop(0, `rgba(${c},${.32 * A.i})`); g.addColorStop(.5, `rgba(${c},${.1 * A.i})`); g.addColorStop(1, `rgba(${c},0)`);
    fc.fillStyle = g; fc.fillRect(0, 0, W, H);
  });
  fc.globalCompositeOperation = 'source-over';
  // rejilla en perspectiva (piso digital)
  if (A.grid > .01) {
    fc.save(); fc.globalAlpha = .22 * A.grid; fc.strokeStyle = `rgb(${A.c1})`; fc.lineWidth = 1.2;
    const hz = H * .63;
    for (let i = -14; i <= 14; i++) { fc.beginPath(); fc.moveTo(W / 2 + i * 30, hz); fc.lineTo(W / 2 + i * 260, H); fc.stroke(); }
    for (let j = 0; j < 16; j++) { const z = ((j + t * .8) % 16) / 16, y = hz + (H - hz) * z * z; fc.globalAlpha = .22 * A.grid * z; fc.beginPath(); fc.moveTo(0, y); fc.lineTo(W, y); fc.stroke(); }
    const g = fc.createLinearGradient(0, hz - 40, 0, hz + 200); g.addColorStop(0, '#04050a'); g.addColorStop(1, 'rgba(4,5,10,0)');
    fc.globalAlpha = 1; fc.fillStyle = g; fc.fillRect(0, hz - 40, W, 240); fc.restore();
  }
  // polvo luminoso con profundidad
  for (const p of polvo) {
    const y = ((p.y - t * p.v * p.z) % H + H) % H, x = p.x + Math.sin(t * .4 + p.f) * 30 * p.z;
    const a = (.15 + .5 * Math.max(0, Math.sin(t * 1.3 + p.f))) * p.z;
    fc.fillStyle = `rgba(190,210,255,${a * .55})`; fc.beginPath(); fc.arc(x, y, .6 + p.z * 1.6, 0, 6.29); fc.fill();
  }
}

/* ---------- efectos superpuestos (rayas de velocidad, chispas, viñeta, grano) ---------- */
const fx = document.getElementById('fx').getContext('2d');
const rayas = Array.from({ length: 90 }, () => ({ a: R() * 6.283, d: R(), v: .6 + R() * 1.4, w: .5 + R() * 2 }));
function dibujarFx(t, opciones) {
  fx.clearRect(0, 0, W, H);
  // rayas radiales de "viaje" a través de la escena
  if (opciones.rayas > 0) {
    fx.save(); fx.globalCompositeOperation = 'lighter';
    for (const r of rayas) {
      const d = ((r.d + t * r.v * .9) % 1), d2 = Math.min(1, d + .08 * r.v);
      const cx = W / 2, cy = H * .45, R1 = 80 + d * d * 1300, R2 = 80 + d2 * d2 * 1300;
      fx.strokeStyle = `rgba(150,190,255,${opciones.rayas * d * .55})`; fx.lineWidth = r.w * (.5 + d * 2);
      fx.beginPath(); fx.moveTo(cx + Math.cos(r.a) * R1, cy + Math.sin(r.a) * R1); fx.lineTo(cx + Math.cos(r.a) * R2, cy + Math.sin(r.a) * R2); fx.stroke();
    }
    fx.restore();
  }
  // estallidos de partículas
  for (const b of RAFAGAS) {
    const dt = t - b.t; if (dt < 0 || dt > 2.2) continue;
    fx.save(); fx.globalCompositeOperation = 'lighter';
    for (const p of b.ps) {
      const k = 1 - Math.exp(-dt * 3), x = b.x + Math.cos(p.a) * p.v * k, y = b.y + Math.sin(p.a) * p.v * k + 60 * dt * dt;
      const a = (1 - pr(dt, .8, 2.2)) * p.o;
      fx.fillStyle = `rgba(${p.c},${a})`; fx.beginPath(); fx.arc(x, y, p.r * (1 - dt / 3), 0, 6.29); fx.fill();
    }
    fx.restore();
  }
  // viñeta
  const v = fx.createRadialGradient(W / 2, H * .46, H * .3, W / 2, H * .5, H * .78);
  v.addColorStop(0, 'rgba(0,0,0,0)'); v.addColorStop(1, 'rgba(0,0,0,.55)');
  fx.fillStyle = v; fx.fillRect(0, 0, W, H);
  // grano animado
  fx.globalAlpha = .55; const gx = (t * 997 % 300) | 0, gy = (t * 613 % 500) | 0;
  fx.drawImage(grano, -gx, -gy, W * 1.4, H * 1.4); fx.globalAlpha = 1;
  // fundido general
  if (opciones.negro > 0) { fx.fillStyle = `rgba(0,0,0,${opciones.negro})`; fx.fillRect(0, 0, W, H); }
}
const RAFAGAS = [];
function rafaga(t, x, y, n, colores, vel = 600, seed = 1) {
  const r = rng(seed); RAFAGAS.push({ t, x, y, ps: Array.from({ length: n }, () => ({ a: r() * 6.283, v: vel * (.3 + r()), r: 1.5 + r() * 4, o: .5 + r() * .5, c: colores[(r() * colores.length) | 0] })) });
}

/* ---------- subtítulos palabra por palabra ---------- */
const subsEl = document.getElementById('subs');
let subActual = -1;
function subtitulos(t, visible = true) {
  let idx = -1;
  for (let i = 0; i < SUBS.length; i++) if (t >= SUBS[i].t - .05 && t < SUBS[i].fin) idx = i;
  if (!visible) idx = -1;
  if (idx !== subActual) {
    subActual = idx;
    subsEl.innerHTML = idx < 0 ? '' : SUBS[idx].palabras.map(p => `<span>${p.w}</span>`).join(' ');
  }
  if (idx >= 0) {
    const s = SUBS[idx], spans = subsEl.children;
    s.palabras.forEach((p, i) => {
      const k = salida(pr(t, p.t - .04, p.t + .16));
      spans[i].classList.toggle('on', t >= p.t - .04 && t < p.t + p.d + .05);
      spans[i].style.opacity = .25 + .75 * k;
      spans[i].style.transform = `translateY(${(1 - k) * 14}px) scale(${.96 + .04 * k})`;
    });
    const fade = Math.min(pr(t, s.t - .05, s.t + .1), 1 - pr(t, s.fin - .12, s.fin));
    subsEl.style.opacity = fade;
  }
}

/* ---------- transiciones globales ---------- */
const flashEl = document.getElementById('flash'), hazEl = document.getElementById('haz');
function flashes(t, lista) {
  let f = 0;
  for (const [t0, inten, dur] of lista) { const d = t - t0; if (d >= -.06 && d <= dur) f = Math.max(f, inten * (d < 0 ? (d + .06) / .06 : Math.pow(1 - d / dur, 2))); }
  flashEl.style.opacity = f;
}
function barridos(t, lista) {
  let x = null;
  for (const t0 of lista) { const d = t - t0; if (d >= 0 && d <= .55) x = lerp(-600, 1500, eio(d / .55)); }
  if (x === null) hazEl.style.display = 'none'; else { hazEl.style.display = 'block'; hazEl.style.left = x + 'px'; }
}
