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
  //  TABLERO DE ADELSON (sombra sobre tablero)
  // ----------------------------------------------------------
  function adelson(canvas) {
    const W = canvas.width, H = canvas.height;
    const g = canvas.getContext("2d");
    const N = 7, S = 90, SQUASH = 0.62;
    const cx = W / 2, cy = H / 2 + 40;
    const LIGHT = 205;
    const SHADOW = 0.55; // multiplicador de la sombra
    const A = [1, 0], B = [3, 3];
    const cyl = [5.5, 1.5];

    // transforma coordenadas del tablero a la pantalla
    function toScreen(bx, by) {
      const x = (bx - N / 2) * S, y = (by - N / 2) * S;
      const rx = x * Math.SQRT1_2 - y * Math.SQRT1_2;
      const ry = x * Math.SQRT1_2 + y * Math.SQRT1_2;
      return [cx + rx, cy + ry * SQUASH];
    }
    function boardTransform(c) {
      c.translate(cx, cy);
      c.scale(1, SQUASH);
      c.rotate(Math.PI / 4);
      c.translate(-N / 2 * S, -N / 2 * S);
    }
    function squarePath(c, i, j) {
      const p = [toScreen(i, j), toScreen(i + 1, j), toScreen(i + 1, j + 1), toScreen(i, j + 1)];
      c.beginPath(); c.moveTo(...p[0]); p.slice(1).forEach((q) => c.lineTo(...q)); c.closePath();
    }

    // Capa de sombra (blanca con sombra gris difuminada)
    const sh = document.createElement("canvas");
    sh.width = W; sh.height = H;
    const sg = sh.getContext("2d");
    sg.fillStyle = "#fff"; sg.fillRect(0, 0, W, H);
    sg.filter = "blur(20px)";
    sg.save();
    boardTransform(sg);
    sg.translate(cyl[0] * S, cyl[1] * S);
    sg.rotate(Math.atan2(1, -1)); // dirección (-1, +1) en el tablero
    const v = Math.round(255 * SHADOW);
    sg.fillStyle = `rgb(${v},${v},${v})`;
    sg.beginPath();
    sg.moveTo(0, -0.9 * S);
    sg.lineTo(5.6 * S, -1.6 * S);
    sg.lineTo(6.5 * S, 0);
    sg.lineTo(5.6 * S, 1.6 * S);
    sg.lineTo(0, 0.9 * S);
    sg.arc(0, 0, 0.9 * S, Math.PI / 2, -Math.PI / 2);
    sg.closePath();
    sg.fill();
    sg.restore();
    sg.filter = "none";

    const bC = toScreen(B[0] + 0.5, B[1] + 0.5).map(Math.round);
    const aC = toScreen(A[0] + 0.5, A[1] + 0.5).map(Math.round);
    const sVal = sg.getImageData(bC[0], bC[1], 1, 1).data[0];

    function draw(dark) {
      g.clearRect(0, 0, W, H);
      // espesor del tablero
      const L = toScreen(0, N), Bt = toScreen(N, N), R = toScreen(N, 0);
      const depth = 34;
      g.fillStyle = "#3b3b44";
      g.beginPath(); g.moveTo(...L); g.lineTo(...Bt); g.lineTo(Bt[0], Bt[1] + depth); g.lineTo(L[0], L[1] + depth); g.closePath(); g.fill();
      g.fillStyle = "#2a2a31";
      g.beginPath(); g.moveTo(...Bt); g.lineTo(...R); g.lineTo(R[0], R[1] + depth); g.lineTo(Bt[0], Bt[1] + depth); g.closePath(); g.fill();
      // casillas
      for (let i = 0; i < N; i++) {
        for (let j = 0; j < N; j++) {
          const val = (i + j) % 2 === 0 ? LIGHT : dark;
          g.fillStyle = `rgb(${val},${val},${val})`;
          squarePath(g, i, j);
          g.fill();
          g.strokeStyle = g.fillStyle; g.lineWidth = 1; g.stroke(); // evita líneas finas entre casillas
        }
      }
      // sombra multiplicada solo sobre el tablero
      g.save();
      const T = toScreen(0, 0);
      g.beginPath(); g.moveTo(...T); g.lineTo(...R); g.lineTo(...Bt); g.lineTo(...L); g.closePath(); g.clip();
      g.globalCompositeOperation = "multiply";
      g.drawImage(sh, 0, 0);
      g.restore();
      g.globalCompositeOperation = "source-over";
      // cilindro verde
      const base = toScreen(cyl[0], cyl[1]);
      const rw = 62, rh = rw * SQUASH * 0.9, hgt = 230;
      const grd = g.createLinearGradient(base[0] - rw, 0, base[0] + rw, 0);
      grd.addColorStop(0, "#0f5a2c"); grd.addColorStop(0.35, "#2fa35a"); grd.addColorStop(0.65, "#4cc777"); grd.addColorStop(1, "#1d7a40");
      g.fillStyle = grd;
      g.beginPath();
      g.ellipse(base[0], base[1], rw, rh, 0, 0, Math.PI);
      g.lineTo(base[0] - rw, base[1] - hgt);
      g.ellipse(base[0], base[1] - hgt, rw, rh, 0, Math.PI, 0, true);
      g.closePath(); g.fill();
      g.fillStyle = "#6fe39a";
      g.beginPath(); g.ellipse(base[0], base[1] - hgt, rw, rh, 0, 0, Math.PI * 2); g.fill();
      // letras A y B (corridas para no tapar el centro)
      g.font = "700 40px 'Space Grotesk', Arial, sans-serif";
      g.textAlign = "center"; g.textBaseline = "middle";
      g.fillStyle = "rgba(0,0,0,0.75)";
      g.fillText("A", aC[0], aC[1] - 2);
      g.fillText("B", bC[0], bC[1] - 2);
    }

    // Ajusta el gris oscuro para que A y B sean EXACTAMENTE iguales
    let dark = Math.round((LIGHT * sVal) / 255);
    const probe = (p) => g.getImageData(p[0] + 26, p[1] + 8, 1, 1).data[0];
    for (let k = 0; k < 4; k++) {
      draw(dark);
      const vb = probe(bC);
      const va = probe(aC);
      if (va === vb) break;
      dark += vb - va;
    }
    const finalGray = probe(bC);

    return {
      A: aC, B: bC, gray: finalGray,
      squareA: [toScreen(A[0], A[1]), toScreen(A[0] + 1, A[1]), toScreen(A[0] + 1, A[1] + 1), toScreen(A[0], A[1] + 1)],
      squareB: [toScreen(B[0], B[1]), toScreen(B[0] + 1, B[1]), toScreen(B[0] + 1, B[1] + 1), toScreen(B[0], B[1] + 1)],
    };
  }

  // ----------------------------------------------------------
  //  SERPIENTES GIRATORIAS (deriva periférica, estilo Kitaoka)
  // ----------------------------------------------------------
  function snakes(canvas) {
    const g = canvas.getContext("2d");
    const W = canvas.width, H = canvas.height;
    g.fillStyle = "#7d8a2e"; // fondo oliva para resaltar
    g.fillRect(0, 0, W, H);
    const COLS = ["#000000", "#1d3fe0", "#ffffff", "#f5e400"];
    const WID = [0.38, 0.12, 0.38, 0.12];
    function disc(cx, cy, R, dir) {
      const rings = 5;
      for (let k = 0; k < rings; k++) {
        const r1 = R * (1 - k / rings), r0 = R * (1 - (k + 1) / rings);
        const n = Math.max(8, Math.round(26 * (1 - k / rings)));
        const period = (Math.PI * 2) / n;
        const off = k % 2 ? period / 2 : 0;
        for (let s = 0; s < n; s++) {
          let a = s * period + off;
          for (let c = 0; c < 4; c++) {
            const idx = dir > 0 ? c : 3 - c;
            const span = period * WID[idx];
            g.fillStyle = COLS[idx];
            g.beginPath();
            g.arc(cx, cy, r1, a, a + span);
            g.arc(cx, cy, r0, a + span * 0.85, a - span * 0.15, true);
            g.closePath();
            g.fill();
            a += span;
          }
        }
      }
      g.fillStyle = "#7d8a2e";
      g.beginPath(); g.arc(cx, cy, R / 5 - 1, 0, Math.PI * 2); g.fill();
    }
    const R = 132;
    let row = 0;
    for (let y = 150; y < H + R; y += 285) {
      let col = 0;
      const shift = row % 2 ? 140 : 0;
      for (let x = 140 + shift - 280; x < W + R; x += 280) {
        disc(x, y, R, (row + col) % 2 ? 1 : -1);
        col++;
      }
      row++;
    }
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
  //  DESAFÍO DEL GORILA (atención selectiva)
  // ----------------------------------------------------------
  function gorillaSim(canvas) {
    const g = canvas.getContext("2d");
    const W = canvas.width, H = canvas.height;
    const DURATION = 22;
    const court = { x: 80, y: 60, w: W - 160, h: H - 120 };
    const r = rng(2024);

    const players = [];
    for (let i = 0; i < 6; i++) {
      const team = i < 3 ? "w" : "b";
      players.push({
        team,
        bx: court.x + 170 + (i % 3) * ((court.w - 340) / 2) + (r() - 0.5) * 80,
        by: court.y + (team === "w" ? 0.35 : 0.68) * court.h + (r() - 0.5) * 60,
        ax: 110 + r() * 90, ay: 60 + r() * 50,
        w1: 0.35 + r() * 0.3, w2: 0.3 + r() * 0.35, p1: r() * 6.28, p2: r() * 6.28,
      });
    }
    function pos(p, t) {
      // siempre dentro de la cancha
      const x = p.bx + Math.sin(t * p.w1 + p.p1) * p.ax, y = p.by + Math.cos(t * p.w2 + p.p2) * p.ay;
      return [clamp(x, court.x + 50, court.x + court.w - 50), clamp(y, court.y + 90, court.y + court.h - 90)];
    }
    // pases programados: 12 del equipo blanco
    function schedule(team, count, start, end, seed) {
      const rr = rng(seed);
      const ids = players.map((p, i) => (p.team === team ? i : -1)).filter((i) => i >= 0);
      const list = [];
      let holder = ids[0];
      for (let k = 0; k < count; k++) {
        const t0 = start + (k * (end - start)) / count + rr() * 0.4;
        let to = holder;
        while (to === holder) to = ids[Math.floor(rr() * ids.length)];
        list.push({ from: holder, to, t0, t1: t0 + 0.6, bounce: rr() < 0.5 });
        holder = to;
      }
      return list;
    }
    const passesW = schedule("w", 12, 0.8, 20.2, 11);
    const passesB = schedule("b", 9, 1.3, 20.5, 99);
    const WHITE_PASSES = passesW.length;

    function ballPos(passes, t) {
      let holder = passes[0].from;
      for (const ps of passes) {
        if (t < ps.t0) break;
        if (t <= ps.t1) {
          const k = (t - ps.t0) / (ps.t1 - ps.t0);
          const a = hand(players[ps.from], t), b = hand(players[ps.to], t);
          let x = lerp(a[0], b[0], k), y = lerp(a[1], b[1], k);
          // pase picado (forma de V hacia el piso) o pase de pecho (arco suave)
          y += ps.bounce ? 70 * (1 - Math.abs(2 * k - 1)) : -Math.sin(Math.PI * k) * 26;
          return [x, y];
        }
        holder = ps.to;
      }
      return hand(players[holder], t);
    }
    function hand(p, t) { const [x, y] = pos(p, t); return [x + 26, y - 6]; }

    function drawPerson(x, y, team, t, ph) {
      const body = team === "w" ? "#f7f7f7" : "#1c1c22";
      const edge = team === "w" ? "#c9c9cf" : "#000";
      const skin = "#e3b48f";
      const sw = Math.sin(t * 8 + ph) * 10;
      g.lineCap = "round";
      g.strokeStyle = "#3a2f2a"; g.lineWidth = 10;
      g.beginPath(); g.moveTo(x - 8, y + 36); g.lineTo(x - 10 + sw * 0.6, y + 78); g.stroke();
      g.beginPath(); g.moveTo(x + 8, y + 36); g.lineTo(x + 10 - sw * 0.6, y + 78); g.stroke();
      g.fillStyle = body; g.strokeStyle = edge; g.lineWidth = 2;
      g.beginPath(); g.roundRect(x - 22, y - 22, 44, 62, 14); g.fill(); g.stroke();
      g.strokeStyle = skin; g.lineWidth = 9;
      g.beginPath(); g.moveTo(x - 20, y - 10); g.lineTo(x - 30, y + 18 + sw * 0.4); g.stroke();
      g.beginPath(); g.moveTo(x + 20, y - 10); g.lineTo(x + 28, y - 4); g.stroke();
      g.fillStyle = skin;
      g.beginPath(); g.arc(x, y - 40, 17, 0, Math.PI * 2); g.fill();
      g.fillStyle = "#3a2a1e";
      g.beginPath(); g.arc(x, y - 46, 17, Math.PI, 0); g.fill();
    }

    function drawGorilla(x, y, t, thump) {
      const s = 1.35;
      g.save(); g.translate(x, y); g.scale(s, s);
      const sw = Math.sin(t * 6) * 8;
      g.fillStyle = "#121214";
      // piernas
      g.beginPath(); g.ellipse(-14, 50 + Math.abs(sw) * 0.2, 13, 26, 0.1, 0, Math.PI * 2); g.fill();
      g.beginPath(); g.ellipse(14, 50 + Math.abs(-sw) * 0.2, 13, 26, -0.1, 0, Math.PI * 2); g.fill();
      // cuerpo
      g.beginPath(); g.ellipse(0, 6, 34, 44, 0, 0, Math.PI * 2); g.fill();
      // brazos
      const up = thump ? Math.abs(Math.sin(t * 14)) : 0;
      g.lineCap = "round"; g.strokeStyle = "#121214"; g.lineWidth = 18;
      g.beginPath(); g.moveTo(-26, -18); g.lineTo(thump ? -10 : -44, thump ? 0 - up * 12 : 40 + sw); g.stroke();
      g.beginPath(); g.moveTo(26, -18); g.lineTo(thump ? 10 : 44, thump ? 0 - (1 - up) * 12 : 40 - sw); g.stroke();
      // cabeza
      g.beginPath(); g.arc(0, -48, 24, 0, Math.PI * 2); g.fill();
      g.fillStyle = "#3d3a3a";
      g.beginPath(); g.ellipse(0, -42, 15, 12, 0, 0, Math.PI * 2); g.fill();
      g.fillStyle = "#fff";
      g.beginPath(); g.arc(-7, -52, 3, 0, Math.PI * 2); g.arc(7, -52, 3, 0, Math.PI * 2); g.fill();
      g.restore();
    }

    function gorillaPos(t) {
      // entra por la derecha, se para en el medio, se golpea el pecho y sale por la izquierda
      const yy = court.y + court.h * 0.52;
      if (t < 7.5) return null;
      if (t < 10.5) return [lerp(W + 80, W / 2, (t - 7.5) / 3), yy, false];
      if (t < 12.3) return [W / 2, yy, true];
      if (t < 16) return [lerp(W / 2, -80, (t - 12.3) / 3.7), yy, false];
      return null;
    }

    let spotlight = false;
    function draw(t) {
      g.clearRect(0, 0, W, H);
      // piso
      const fl = g.createLinearGradient(0, court.y, 0, court.y + court.h);
      fl.addColorStop(0, "#d9dbe2"); fl.addColorStop(1, "#bfc3cc");
      g.fillStyle = fl;
      g.beginPath(); g.roundRect(court.x, court.y, court.w, court.h, 26); g.fill();
      // ascensores de fondo (como en el video original)
      g.fillStyle = "#a9adb7";
      g.fillRect(court.x + 120, court.y + 20, 150, 200);
      g.fillRect(court.x + court.w - 270, court.y + 20, 150, 200);
      g.fillStyle = "#9ca0aa";
      g.fillRect(court.x + 194, court.y + 20, 3, 200);
      g.fillRect(court.x + court.w - 196, court.y + 20, 3, 200);

      const gp = gorillaPos(t);
      // ordenar por profundidad
      const items = players.map((p, i) => ({ y: pos(p, t)[1], i }));
      if (gp) items.push({ y: gp[1], i: -1 });
      items.sort((a, b) => a.y - b.y);
      for (const it of items) {
        if (it.i === -1) drawGorilla(gp[0], gp[1], t, gp[2]);
        else { const p = players[it.i]; const [x, y] = pos(p, t); drawPerson(x, y, p.team, t, it.i); }
      }
      // pelotas
      [ballPos(passesW, t), ballPos(passesB, t)].forEach(([x, y]) => {
        g.fillStyle = "#e8742c";
        g.beginPath(); g.arc(x, y, 11, 0, Math.PI * 2); g.fill();
        g.strokeStyle = "#7a3510"; g.lineWidth = 2;
        g.beginPath(); g.arc(x, y, 11, 0, Math.PI * 2); g.moveTo(x - 11, y); g.lineTo(x + 11, y); g.stroke();
      });
      // reflector sobre el gorila
      if (spotlight && gp) {
        g.save();
        g.beginPath(); g.roundRect(court.x, court.y, court.w, court.h, 26); g.clip();
        const rg = g.createRadialGradient(gp[0], gp[1] - 10, 90, gp[0], gp[1] - 10, 260);
        rg.addColorStop(0, "rgba(0,0,0,0)"); rg.addColorStop(1, "rgba(0,0,0,0.78)");
        g.fillStyle = rg; g.fillRect(0, 0, W, H);
        g.strokeStyle = "#ffe14d"; g.lineWidth = 6; g.setLineDash([16, 12]);
        g.beginPath(); g.arc(gp[0], gp[1] - 10, 120, 0, Math.PI * 2); g.stroke();
        g.restore();
      }
    }

    return {
      DURATION, WHITE_PASSES, draw,
      setSpotlight(v) { spotlight = v; },
      gorillaWindow: [7.5, 16],
    };
  }

  // ----------------------------------------------------------
  //  ONDAS DE SONIDO (fondo animado)
  // ----------------------------------------------------------
  function waves(canvas) {
    const g = canvas.getContext("2d");
    const W = canvas.width, H = canvas.height;
    return function (t) {
      g.clearRect(0, 0, W, H);
      for (let k = 0; k < 4; k++) {
        g.beginPath();
        g.strokeStyle = `hsla(${190 + k * 40} 90% 65% / ${0.5 - k * 0.09})`;
        g.lineWidth = 3 - k * 0.5;
        for (let x = 0; x <= W; x += 8) {
          const env = Math.sin((x / W) * Math.PI);
          const y = H / 2 +
            Math.sin(x * 0.012 + t * (1.4 + k * 0.3) + k) * 60 * env * Math.sin(t * 0.7 + k) +
            Math.sin(x * 0.031 - t * 2.1) * 22 * env;
          x === 0 ? g.moveTo(x, y) : g.lineTo(x, y);
        }
        g.stroke();
      }
    };
  }

  window.ILLUSIONS = { brainParticles, adelson, snakes, sceneSVG, gorillaSim, waves, rng };
})();
