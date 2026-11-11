// ============================================================
//  ILUSIONES — todo dibujado con código (canvas / SVG)
//  para que funcione sin internet y sea exacto.
// ============================================================
(function () {
  // Generador pseudoaleatorio con semilla (siempre dibuja igual)
  function rng(seed) {
    let s = seed >>> 0;
    return () => {
      s = (s + 0x6d2b79f5) >>> 0;
      let t = s;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  const easeOutExpo = (x) => (x >= 1 ? 1 : 1 - Math.pow(2, -10 * x));
  const lerp = (a, b, k) => a + (b - a) * k;
  const clamp = (x, a, b) => Math.max(a, Math.min(b, x));

  // ----------------------------------------------------------
  //  CEREBRO DE PARTÍCULAS (portada)
  // ----------------------------------------------------------
  function brainShape(w, h) {
    const c = document.createElement("canvas");
    c.width = w; c.height = h;
    const g = c.getContext("2d");
    const sx = w / 600, sy = h / 430;
    g.scale(sx, sy);
    g.fillStyle = "#fff";
    // lóbulos del cerebro (vista lateral)
    [[150, 200, 125], [255, 135, 140], [375, 140, 135], [455, 215, 105], [300, 215, 150], [175, 265, 92], [400, 250, 110]].forEach(([x, y, r]) => {
      g.beginPath(); g.arc(x, y, r, 0, Math.PI * 2); g.fill();
    });
    // cerebelo
    g.beginPath(); g.ellipse(425, 335, 95, 55, -0.15, 0, Math.PI * 2); g.fill();
    // tronco
    g.save(); g.translate(355, 330); g.rotate(0.12); g.fillRect(-26, 0, 52, 100); g.restore();
    // surcos (circunvoluciones)
    g.globalCompositeOperation = "destination-out";
    g.lineCap = "round";
    g.lineJoin = "round";
    const r = rng(7);
    g.lineWidth = 9;
    // cisura lateral y surco central
    g.beginPath(); g.moveTo(140, 285); g.bezierCurveTo(230, 250, 300, 230, 390, 215); g.stroke();
    g.beginPath(); g.moveTo(330, 25); g.bezierCurveTo(300, 100, 320, 170, 275, 245); g.stroke();
    g.lineWidth = 6;
    for (let i = 0; i < 26; i++) {
      let x = 60 + r() * 480, y = 40 + r() * 280;
      g.beginPath(); g.moveTo(x, y);
      let ang = r() * Math.PI * 2;
      for (let k = 0; k < 6; k++) {
        ang += (r() - 0.5) * 1.8;
        x += Math.cos(ang) * 16; y += Math.sin(ang) * 16;
        g.lineTo(x, y);
      }
      g.stroke();
    }
    // líneas del cerebelo
    g.lineWidth = 4;
    for (let i = 0; i < 5; i++) {
      g.beginPath(); g.ellipse(425, 340 + i * 9 - 18, 80 - i * 6, 18, -0.15, Math.PI * 0.05, Math.PI * 0.95); g.stroke();
    }
    return g.getImageData(0, 0, w, h);
  }

  function brainParticles(canvas, opts = {}) {
    const g = canvas.getContext("2d");
    const W = canvas.width, H = canvas.height;
    const bw = opts.w || 520, bh = Math.round(bw * 430 / 600);
    const ox = (opts.cx || W / 2) - bw / 2, oy = (opts.cy || 260) - bh / 2;
    const img = brainShape(bw, bh);
    const stepPx = opts.step || 7;
    const r = rng(42);
    const pts = [];
    for (let y = 0; y < bh; y += stepPx) {
      for (let x = 0; x < bw; x += stepPx) {
        if (img.data[(y * bw + x) * 4 + 3] > 128) {
          const jx = x + (r() - 0.5) * 3, jy = y + (r() - 0.5) * 3;
          const ang = r() * Math.PI * 2, dist = 500 + r() * 900;
          pts.push({
            tx: ox + jx, ty: oy + jy,
            sx: W / 2 + Math.cos(ang) * dist, sy: H / 2 + Math.sin(ang) * dist * 0.6,
            d: r() * 1.4 + (x / bw) * 0.6, ph: r() * 6.28,
            b: Math.min(5, Math.floor((x / bw) * 6)), spark: 0,
          });
        }
      }
    }
    // colores por franja: violeta -> cian
    const cols = [];
    for (let i = 0; i < 6; i++) cols.push(`hsl(${275 - i * 17} 95% ${62 + i * 3}%)`);
    const buckets = cols.map(() => []);
    pts.forEach((p) => buckets[p.b].push(p));

    // sprite de brillo para chispas
    const spr = document.createElement("canvas");
    spr.width = spr.height = 40;
    const sg = spr.getContext("2d");
    const grd = sg.createRadialGradient(20, 20, 0, 20, 20, 20);
    grd.addColorStop(0, "rgba(255,255,255,1)");
    grd.addColorStop(0.3, "rgba(160,220,255,0.6)");
    grd.addColorStop(1, "rgba(120,80,255,0)");
    sg.fillStyle = grd; sg.fillRect(0, 0, 40, 40);

    const DUR = opts.duration || 2.8;
    let t0 = null;
    let explode = 0;
    function frame(t) {
      if (t0 === null) t0 = t;
      const T = (t - t0) / 1000;
      g.clearRect(0, 0, W, H);
      const size = 2.6;
      for (let b = 0; b < 6; b++) {
        g.fillStyle = cols[b];
        const arr = buckets[b];
        for (let i = 0; i < arr.length; i++) {
          const p = arr[i];
          const k = easeOutExpo(clamp((T - p.d) / DUR, 0, 1));
          let x = lerp(p.sx, p.tx, k), y = lerp(p.sy, p.ty, k);
          if (k >= 1) {
            x += Math.sin(T * 1.1 + p.ph) * 1.4;
            y += Math.cos(T * 1.3 + p.ph) * 1.4;
          }
          if (explode > 0) {
            const dx = p.tx - W / 2, dy = p.ty - H / 2;
            x += dx * explode * 2.5; y += dy * explode * 2.5;
          }
          p.x = x; p.y = y;
          g.globalAlpha = 0.35 + k * 0.6;
          g.fillRect(x, y, size, size);
        }
      }
      g.globalAlpha = 1;
      // chispas neuronales
      if (T > DUR) {
        for (let i = 0; i < 3; i++) {
          if (Math.random() < 0.5) pts[(Math.random() * pts.length) | 0].spark = 1;
        }
      }
      g.globalCompositeOperation = "lighter";
      for (let i = 0; i < pts.length; i++) {
        const p = pts[i];
        if (p.spark > 0.02) {
          const s = 10 + p.spark * 22;
          g.globalAlpha = p.spark;
          g.drawImage(spr, p.x - s / 2, p.y - s / 2, s, s);
          p.spark *= 0.9;
        }
      }
      g.globalAlpha = 1;
      g.globalCompositeOperation = "source-over";
    }
    return {
      frame,
      explode(v) { explode = v; },
    };
  }

  // ----------------------------------------------------------
  //  ESCENA "ENCONTRÁ LA DIFERENCIA" (ceguera al cambio)
  // ----------------------------------------------------------
  function sceneSVG(withTree) {
    return `
<svg viewBox="0 0 1100 560" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#5ab8ff"/><stop offset="1" stop-color="#cdeeff"/></linearGradient>
    <linearGradient id="grass" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#5cc75a"/><stop offset="1" stop-color="#2f8f3c"/></linearGradient>
  </defs>
  <rect width="1100" height="560" fill="url(#sky)"/>
  <circle cx="930" cy="95" r="52" fill="#ffd84a"/>
  <g fill="#fff" opacity=".95">
    <ellipse cx="200" cy="90" rx="70" ry="26"/><ellipse cx="245" cy="75" rx="50" ry="28"/><ellipse cx="160" cy="80" rx="40" ry="22"/>
    <ellipse cx="640" cy="120" rx="80" ry="24"/><ellipse cx="690" cy="104" rx="46" ry="26"/>
  </g>
  <path d="M0 330 L170 190 L300 300 L430 170 L620 330 Z" fill="#7a8fb3"/>
  <path d="M430 170 L470 205 L445 215 L415 200 Z" fill="#fff"/>
  <path d="M520 330 L700 210 L880 330 Z" fill="#8ea2c4"/>
  <rect y="320" width="1100" height="240" fill="url(#grass)"/>
  <path d="M0 470 Q550 420 1100 480 L1100 560 L0 560 Z" fill="#6b6b74"/>
  <path d="M0 515 Q550 468 1100 522" stroke="#f3f3f3" stroke-width="5" stroke-dasharray="40 30" fill="none"/>
  <!-- casa -->
  <rect x="160" y="250" width="250" height="170" fill="#f2d3a1"/>
  <path d="M140 258 L285 150 L430 258 Z" fill="#c2453b"/>
  <rect x="360" y="165" width="30" height="60" fill="#8a3a33"/>
  <rect x="190" y="290" width="60" height="55" fill="#7cc8ff" stroke="#fff" stroke-width="6"/>
  <rect x="320" y="290" width="60" height="55" fill="#7cc8ff" stroke="#fff" stroke-width="6"/>
  <rect x="260" y="330" width="50" height="90" fill="#7b4a2b"/>
  <circle cx="300" cy="378" r="4" fill="#ffd84a"/>
  <!-- cerco -->
  <g fill="#fff">${Array.from({ length: 9 }, (_, i) => `<rect x="${440 + i * 30}" y="368" width="14" height="60" rx="3"/>`).join("")}
    <rect x="436" y="385" width="268" height="9"/><rect x="436" y="408" width="268" height="9"/></g>
  <!-- árbol izquierdo -->
  <rect x="62" y="330" width="22" height="95" fill="#6e4a2c"/>
  <circle cx="73" cy="305" r="55" fill="#2e9b46"/><circle cx="45" cy="330" r="35" fill="#2a8a40"/><circle cx="103" cy="330" r="35" fill="#2a8a40"/>
  <!-- ÁRBOL QUE CAMBIA -->
  <g id="change" opacity="${withTree ? 1 : 0}">
    <rect x="835" y="300" width="28" height="135" fill="#6e4a2c"/>
    <circle cx="849" cy="265" r="72" fill="#2e9b46"/><circle cx="805" cy="300" r="45" fill="#2a8a40"/><circle cx="893" cy="300" r="45" fill="#2a8a40"/>
  </g>
  <!-- auto -->
  <g transform="translate(560 432)">
    <rect x="0" y="20" width="200" height="50" rx="16" fill="#e5484d"/>
    <path d="M38 22 L66 -12 L140 -12 L168 22 Z" fill="#e5484d"/>
    <path d="M52 20 L72 -4 L102 -4 L102 20 Z M110 20 L110 -4 L136 -4 L154 20 Z" fill="#bfe6ff"/>
    <circle cx="48" cy="72" r="20" fill="#222"/><circle cx="48" cy="72" r="8" fill="#aaa"/>
    <circle cx="152" cy="72" r="20" fill="#222"/><circle cx="152" cy="72" r="8" fill="#aaa"/>
  </g>
  <!-- flores -->
  <g>${[[480, 455], [520, 462], [930, 452], [980, 460], [130, 450]].map(([x, y]) => `<circle cx="${x}" cy="${y}" r="7" fill="#ff7ab6"/><circle cx="${x}" cy="${y}" r="3" fill="#fff36b"/>`).join("")}</g>
</svg>`;
  }

  // ----------------------------------------------------------
  //  CAFÉ WALL (Gregory & Heard, 1979)
  //  Baldosas negras y blancas, "junta" gris, filas corridas
  //  media baldosa (la ilusión es máxima en ese punto, Bach).
  // ----------------------------------------------------------
  function cafeWall(canvas) {
    const g = canvas.getContext("2d");
    const W = canvas.width, H = canvas.height;
    const T = 74, M = 4;          // baldosa y junta (mortar)
    const rows = Math.floor((H - M) / (T + M));
    const top = (H - rows * (T + M) - M) / 2;
    let shift = 0.5, guides = 0;
    function draw() {
      g.fillStyle = "#7f7f7f"; // junta gris: a mitad de camino entre blanco y negro
      g.fillRect(0, 0, W, H);
      for (let r = 0; r < rows; r++) {
        const y = top + M + r * (T + M);
        // filas alternas se corren en sentidos opuestos: desfase relativo = shift * T
        const off = (r % 2 ? 1 : -1) * shift * T / 2;
        for (let i = -2; i * T < W + 2 * T; i++) {
          g.fillStyle = (i % 2 === 0) ? "#000" : "#fff";
          g.fillRect(i * T + off, y, T, T);
        }
      }
      if (guides > 0) {
        g.save();
        g.globalAlpha = guides;
        g.strokeStyle = "#ff2d55"; g.lineWidth = 4;
        g.shadowColor = "#ff2d55"; g.shadowBlur = 12;
        for (let r = 0; r <= rows; r++) {
          const y = top + r * (T + M) + M / 2;
          g.beginPath(); g.moveTo(0, y); g.lineTo(W, y); g.stroke();
        }
        g.restore();
      }
    }
    draw();
    return {
      set(s, gd) { if (s !== undefined) shift = s; if (gd !== undefined) guides = gd; draw(); },
      get shift() { return shift; },
    };
  }

  // ----------------------------------------------------------
  //  REJILLA CENTELLEANTE (Bergen 1985; Schrauf et al. 1997)
  //  Fondo negro, barras grises, discos blancos en los cruces.
  //  Disco ≈ 1,5 × ancho de barra (28' vs 19' en la réplica de 2012).
  //  Si las barras se curvan, los puntos negros desaparecen (Bach).
  // ----------------------------------------------------------
  function scintGrid(canvas) {
    const g = canvas.getContext("2d");
    const W = canvas.width, H = canvas.height;
    const S = 104, BAR = 18, DISC = 27;
    const cols = Math.floor(W / S), rows = Math.floor(H / S);
    const ox = (W - (cols - 1) * S) / 2, oy = (H - (rows - 1) * S) / 2;
    const P = 2 * S; // período de la curva
    function draw(amp = 0) {
      g.fillStyle = "#000"; g.fillRect(0, 0, W, H);
      g.strokeStyle = "#5e5e5e"; g.lineWidth = BAR; g.lineCap = "butt";
      for (let r = 0; r < rows; r++) {
        const y0 = oy + r * S;
        g.beginPath();
        for (let x = -10; x <= W + 10; x += 6) {
          const y = y0 + amp * Math.sin((x / P) * Math.PI * 2);
          x === -10 ? g.moveTo(x, y) : g.lineTo(x, y);
        }
        g.stroke();
      }
      for (let c = 0; c < cols; c++) {
        const x0 = ox + c * S;
        g.beginPath();
        for (let y = -10; y <= H + 10; y += 6) {
          const x = x0 + amp * Math.sin((y / P) * Math.PI * 2);
          y === -10 ? g.moveTo(x, y) : g.lineTo(x, y);
        }
        g.stroke();
      }
      g.fillStyle = "#fff";
      for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
        const x0 = ox + c * S, y0 = oy + r * S;
        const x = x0 + amp * Math.sin((y0 / P) * Math.PI * 2);
        const y = y0 + amp * Math.sin((x0 / P) * Math.PI * 2);
        g.beginPath(); g.arc(x, y, DISC / 2, 0, Math.PI * 2); g.fill();
      }
    }
    draw(0);
    return { draw };
  }

  // ----------------------------------------------------------
  //  LILAC CHASER (Jeremy Hinton, 2005)
  //  12 discos lila difuminados en círculo, cruz negra al centro,
  //  fondo gris; falta un disco por vez y el "hueco" gira.
  // ----------------------------------------------------------
  function lilacChaser(canvas) {
    const g = canvas.getContext("2d");
    const W = canvas.width, H = canvas.height;
    const R = Math.min(W, H) * 0.36, rDisc = Math.min(W, H) * 0.06;
    // disco difuminado pre-renderizado (se dibuja una vez)
    const spr = document.createElement("canvas");
    const sz = Math.ceil(rDisc * 4);
    spr.width = spr.height = sz;
    const sg = spr.getContext("2d");
    sg.filter = `blur(${Math.round(rDisc * 0.45)}px)`;
    sg.fillStyle = "rgb(222,150,232)";
    sg.beginPath(); sg.arc(sz / 2, sz / 2, rDisc, 0, Math.PI * 2); sg.fill();
    let missing = 0;
    function draw() {
      g.fillStyle = "rgb(190,190,190)"; g.fillRect(0, 0, W, H);
      for (let i = 0; i < 12; i++) {
        if (i === missing) continue;
        const a = (i / 12) * Math.PI * 2 - Math.PI / 2;
        g.drawImage(spr, W / 2 + Math.cos(a) * R - sz / 2, H / 2 + Math.sin(a) * R - sz / 2);
      }
      g.fillStyle = "#000";
      const c = Math.min(W, H) * 0.03, t = Math.max(3, c * 0.18);
      g.fillRect(W / 2 - c, H / 2 - t / 2, 2 * c, t);
      g.fillRect(W / 2 - t / 2, H / 2 - c, t, 2 * c);
    }
    draw();
    return { step() { missing = (missing + 1) % 12; draw(); } };
  }

  // ----------------------------------------------------------
  //  ESPIRAL (efecto consecutivo de movimiento, Plateau 1849)
  //  Se dibuja una vez; el giro se hace rotando el <canvas>.
  // ----------------------------------------------------------
  function spiral(canvas) {
    const g = canvas.getContext("2d");
    const W = canvas.width, H = canvas.height, cx = W / 2, cy = H / 2;
    const Rmax = Math.min(W, H) / 2 - 12;
    g.fillStyle = "#fff";
    g.beginPath(); g.arc(cx, cy, Rmax, 0, Math.PI * 2); g.fill();
    // espiral de 2 brazos: el sector se oscurece si sin(2*(θ - k·r)) > 0
    const img = g.getImageData(0, 0, W, H);
    const d = img.data;
    const k = 0.045;
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      const dx = x - cx, dy = y - cy, r = Math.hypot(dx, dy);
      if (r > Rmax) continue;
      const th = Math.atan2(dy, dx);
      if (Math.sin(2 * (th - k * r)) > 0) { const i = (y * W + x) * 4; d[i] = d[i + 1] = d[i + 2] = 10; }
    }
    g.putImageData(img, 0, 0);
    g.fillStyle = "#e11d48";
    g.beginPath(); g.arc(cx, cy, 9, 0, Math.PI * 2); g.fill();
  }

  // ----------------------------------------------------------
  //  STEPPING FEET (Stuart Anstis, 2001–2003)
  //  Rayas verticales blanco/negro; un rectángulo azul oscuro y
  //  otro amarillo claro se mueven JUNTOS a velocidad constante.
  // ----------------------------------------------------------
  function steppingFeet(canvas) {
    const g = canvas.getContext("2d");
    const W = canvas.width, H = canvas.height;
    const STRIPE = 26, FOOT_W = STRIPE * 4, FOOT_H = 64;
    const SPEED = 110; // px por segundo
    let stripes = 1;
    const span = W - FOOT_W - 80;
    function draw(t) {
      g.fillStyle = "#808080"; g.fillRect(0, 0, W, H);
      g.globalAlpha = stripes;
      for (let x = 0; x < W; x += STRIPE * 2) {
        g.fillStyle = "#000"; g.fillRect(x, 0, STRIPE, H);
        g.fillStyle = "#fff"; g.fillRect(x + STRIPE, 0, STRIPE, H);
      }
      g.globalAlpha = 1;
      // ida y vuelta a velocidad constante (onda triangular)
      const p = (t * SPEED) % (2 * span);
      const x = 40 + (p < span ? p : 2 * span - p);
      g.fillStyle = "#1428c8"; g.fillRect(x, H * 0.3 - FOOT_H / 2, FOOT_W, FOOT_H);
      g.fillStyle = "#fff21e"; g.fillRect(x, H * 0.7 - FOOT_H / 2, FOOT_W, FOOT_H);
    }
    return { draw, setStripes(v) { stripes = v; } };
  }

  // ----------------------------------------------------------
  //  CEGUERA INDUCIDA POR MOVIMIENTO (Bonneh et al., 2001)
  //  Cruces azules que giran (12 rpm) + 3 puntos amarillos fijos.
  // ----------------------------------------------------------
  function mib(canvas) {
    const g = canvas.getContext("2d");
    const W = canvas.width, H = canvas.height, cx = W / 2, cy = H / 2;
    const R = Math.min(W, H) * 0.47;
    const STEP = R / 4.2;
    const crosses = [];
    for (let j = -4; j <= 4; j++) for (let i = -4; i <= 4; i++) {
      const x = i * STEP, y = j * STEP;
      if (Math.hypot(x, y) < R - 10) crosses.push([x, y]);
    }
    const dots = [[0, -0.42], [-0.37, 0.24], [0.37, 0.24]].map(([a, b]) => [a * R, b * R]);
    let speed = 1;
    let angle = 0, last = null;
    function draw(t) {
      if (last === null) last = t;
      angle += ((t - last) / 1000) * speed * (12 / 60) * Math.PI * 2; // 12 rpm
      last = t;
      g.fillStyle = "#000"; g.fillRect(0, 0, W, H);
      g.save(); g.translate(cx, cy); g.rotate(angle);
      g.fillStyle = "#2f54ff";
      const L = STEP * 0.32, T = Math.max(4, STEP * 0.08);
      for (const [x, y] of crosses) { g.fillRect(x - L, y - T / 2, 2 * L, T); g.fillRect(x - T / 2, y - L, T, 2 * L); }
      g.restore();
      g.fillStyle = "#ffe600";
      for (const [x, y] of dots) { g.beginPath(); g.arc(cx + x, cy + y, 7, 0, Math.PI * 2); g.fill(); }
      // punto de fijación que titila (como en la versión de Bach)
      g.fillStyle = Math.floor(t / 500) % 2 ? "#ff3355" : "#22c55e";
      g.beginPath(); g.arc(cx, cy, 6, 0, Math.PI * 2); g.fill();
    }
    return { draw, setSpeed(v) { speed = v; } };
  }

  // ----------------------------------------------------------
  //  ROTACIÓN AMBIGUA (estructura a partir del movimiento)
  //  Puntos en superficies 3D, proyección ortográfica y SIN
  //  pistas de profundidad: el sentido de giro es ambiguo.
  //  kind: "cube" | "cylinder" | "sphere"
  // ----------------------------------------------------------
  function spin3d(canvas, kind) {
    const g = canvas.getContext("2d");
    const W = canvas.width, H = canvas.height, cx = W / 2, cy = H / 2;
    const r = rng(kind.length * 97);
    const S = Math.min(W, H) * 0.3;
    const TILT = kind === "sphere" ? 0.18 : kind === "cylinder" ? 0 : 0.32; // vista levemente desde arriba
    const SWAP = kind === "cylinder"; // el tambor gira sobre un eje horizontal
    const dots = []; // [x,y,z,color]
    const lines = []; // [[x,y,z]...], color, width
    const fills = []; // polígonos (flechas) [[pts], color]

    if (kind === "cube") {
      for (let f = 0; f < 6; f++) for (let i = 0; i < 520; i++) {
        const a = (r() * 2 - 1) * S, b = (r() * 2 - 1) * S;
        const p = [[S, a, b], [-S, a, b], [a, S, b], [a, -S, b], [a, b, S], [a, b, -S]][f];
        dots.push([...p, "rgba(235,235,245,0.85)"]);
      }
      const v = [-S, S];
      for (const a of v) for (const b of v) {
        lines.push([[[-S, a, b], [S, a, b]], "#f2f2ff", 2.2]);
        lines.push([[[a, -S, b], [a, S, b]], "#f2f2ff", 2.2]);
        lines.push([[[a, b, -S], [a, b, S]], "#f2f2ff", 2.2]);
      }
      // flechas que dan la vuelta por las 4 caras laterales (a media altura)
      const arrow = (face) => {
        const L = S * 0.75, hw = S * 0.07, hh = S * 0.17, hl = S * 0.28;
        const pts2 = [[-L, -hw], [L - hl, -hw], [L - hl, -hh], [L, 0], [L - hl, hh], [L - hl, hw], [-L, hw]];
        return pts2.map(([u, w]) => face(u, w));
      };
      fills.push([arrow((u, w) => [-u, w, S]), "rgba(255,190,40,0.9)"]);
      fills.push([arrow((u, w) => [S, w, u]), "rgba(255,190,40,0.9)"]);
      fills.push([arrow((u, w) => [u, w, -S]), "rgba(255,190,40,0.9)"]);
      fills.push([arrow((u, w) => [-S, w, -u]), "rgba(255,190,40,0.9)"]);
    } else if (kind === "cylinder") {
      // tambor que gira sobre un eje HORIZONTAL, con una flecha pintada en su
      // superficie (como en el video): la flecha baja por adelante y sube por
      // atrás, pero en pantalla no se sabe cuál es cuál.
      const R = S * 1.2, HH = S * 0.5;
      const inArrow = (phi, y) => {
        const yy = Math.abs(y / HH);
        if (phi > -0.15 && phi < 1.35) return yy < 0.36;                 // cuerpo
        if (phi <= -0.15 && phi > -1.25) return yy < 0.86 * (phi + 1.25) / 1.1; // punta
        return false;
      };
      for (let i = 0; i < 4200; i++) {
        const phi = (r() * 2 - 1) * Math.PI, y = (r() * 2 - 1) * HH;
        const on = inArrow(phi, y);
        dots.push([R * Math.sin(phi), y, R * Math.cos(phi), on ? "rgba(255,80,80,0.95)" : "rgba(255,60,60,0.32)"]);
      }
      const rim = (y) => { const p = []; for (let k = 0; k <= 72; k++) { const a = (k / 72) * Math.PI * 2; p.push([R * Math.sin(a), y, R * Math.cos(a)]); } return p; };
      lines.push([rim(-HH), "#4d6bff", 2]); lines.push([rim(HH), "#4d6bff", 2]);
      const out = [];
      const add = (phi, yy) => out.push([R * Math.sin(phi), yy * HH, R * Math.cos(phi)]);
      for (let p = 1.35; p >= -0.15; p -= 0.04) add(p, -0.36);
      add(-0.15, -0.86);
      for (let k = 0; k <= 24; k++) { const p = -0.15 - 1.1 * k / 24; add(p, -0.86 * (1 - k / 24)); }
      for (let k = 0; k <= 24; k++) { const p = -1.25 + 1.1 * k / 24; add(p, 0.86 * k / 24); }
      add(-0.15, 0.36);
      for (let p = -0.15; p <= 1.35; p += 0.04) add(p, 0.36);
      add(1.35, -0.36);
      lines.push([out, "#7b8cff", 2.4]);
    } else {
      const R = S * 1.15;
      for (let i = 0; i < 4200; i++) {
        const u = r() * 2 - 1, th = r() * Math.PI * 2, s = Math.sqrt(1 - u * u);
        dots.push([R * s * Math.cos(th), R * u, R * s * Math.sin(th), "rgba(160,90,255,0.7)"]);
      }
      // disco interior inclinado (gira con la esfera)
      const RD = R * 0.62, tiltD = 0.9;
      // disco en un plano inclinado, corrido hacia la superficie de la esfera
      const disc = (a, rr) => { const x = rr * Math.cos(a), y = rr * Math.sin(a); return [x, y * Math.cos(tiltD), y * Math.sin(tiltD) + R * 0.38]; };
      for (let i = 0; i < 900; i++) dots.push([...disc(r() * Math.PI * 2, RD * Math.sqrt(r())), "rgba(255,240,140,0.9)"]);
      const rim = []; for (let k = 0; k <= 72; k++) rim.push(disc((k / 72) * Math.PI * 2, RD));
      lines.push([rim, "#e8f060", 2.4]);
    }

    let depth = 0; // 0 = sin pistas (ambiguo); 1 = puntos de adelante más grandes
    const ct = Math.cos(TILT), st = Math.sin(TILT);
    function proj(p, ca, sa) {
      const x = p[0] * ca + p[2] * sa, z = -p[0] * sa + p[2] * ca;
      const y = p[1] * ct - z * st, z2 = p[1] * st + z * ct;
      return SWAP ? [cx + y, cy + x, z2] : [cx + x, cy + y, z2];
    }
    function draw(t) {
      const a = (t / 1000) * (Math.PI * 2 / 7); // una vuelta cada 7 s
      const ca = Math.cos(a), sa = Math.sin(a);
      g.fillStyle = "#000"; g.fillRect(0, 0, W, H);
      for (const [pts, col] of fills) {
        g.fillStyle = col;
        g.beginPath();
        pts.forEach((p, i) => { const q = proj(p, ca, sa); i ? g.lineTo(q[0], q[1]) : g.moveTo(q[0], q[1]); });
        g.closePath(); g.fill();
      }
      for (const d of dots) {
        const q = proj(d, ca, sa);
        let s = 2.2;
        if (depth > 0) {
          const k = (q[2] / (S * 1.3) + 1) / 2; // 0 atrás … 1 adelante
          s = 2.2 + depth * (k * 3.2 - 1.2);
          g.globalAlpha = 1 - depth * (1 - k) * 0.8;
        }
        g.fillStyle = d[3];
        g.fillRect(q[0] - s / 2, q[1] - s / 2, s, s);
      }
      g.globalAlpha = 1;
      for (const [pts, col, w] of lines) {
        g.strokeStyle = col; g.lineWidth = w;
        g.beginPath();
        pts.forEach((p, i) => { const q = proj(p, ca, sa); i ? g.lineTo(q[0], q[1]) : g.moveTo(q[0], q[1]); });
        g.stroke();
      }
    }
    return { draw, setDepth(v) { depth = v; } };
  }

  window.ILLUSIONS = { rng, brainParticles, sceneSVG, cafeWall, scintGrid, lilacChaser, spiral, steppingFeet, mib, spin3d };
})();
