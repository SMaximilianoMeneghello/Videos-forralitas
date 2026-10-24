// ============================================================
//  FONDO — red de "neuronas" animada + luces + grano de película
// ============================================================
(function () {
  const cv = document.getElementById("bg");
  const g = cv.getContext("2d");
  let W = 0, H = 0;
  let pts = [];
  let hue = 265;
  let lite = false;
  let burst = 0;
  let running = true;

  function resize() {
    // resolución baja a propósito: es fondo y ahorra batería/CPU en la netbook
    const scale = Math.min(1, 1400 / window.innerWidth);
    W = cv.width = Math.round(window.innerWidth * scale);
    H = cv.height = Math.round(window.innerHeight * scale);
    const n = Math.round((W * H) / 22000);
    pts = Array.from({ length: Math.min(n, 80) }, () => ({
      x: Math.random() * W, y: Math.random() * H,
      vx: (Math.random() - 0.5) * 0.25, vy: (Math.random() - 0.5) * 0.25,
      r: Math.random() * 1.6 + 0.6,
    }));
  }
  window.addEventListener("resize", resize);
  resize();

  function frame() {
    if (!running) return;
    requestAnimationFrame(frame);
    if (lite) { g.clearRect(0, 0, W, H); return; }
    g.clearRect(0, 0, W, H);
    const cx = W / 2, cy = H / 2;
    const LINK = 130;
    for (const p of pts) {
      if (burst > 0.01) {
        const dx = p.x - cx, dy = p.y - cy, d = Math.hypot(dx, dy) || 1;
        p.vx += (dx / d) * burst * 0.9;
        p.vy += (dy / d) * burst * 0.9;
      }
      p.vx *= 0.985; p.vy *= 0.985;
      // velocidad mínima suave
      if (Math.abs(p.vx) < 0.05) p.vx += (Math.random() - 0.5) * 0.04;
      if (Math.abs(p.vy) < 0.05) p.vy += (Math.random() - 0.5) * 0.04;
      p.x += p.vx; p.y += p.vy;
      if (p.x < -20) p.x = W + 20; if (p.x > W + 20) p.x = -20;
      if (p.y < -20) p.y = H + 20; if (p.y > H + 20) p.y = -20;
    }
    burst *= 0.9;
    g.lineWidth = 1;
    for (let i = 0; i < pts.length; i++) {
      const a = pts[i];
      for (let j = i + 1; j < pts.length; j++) {
        const b = pts[j];
        const dx = a.x - b.x, dy = a.y - b.y;
        const d2 = dx * dx + dy * dy;
        if (d2 < LINK * LINK) {
          const k = 1 - Math.sqrt(d2) / LINK;
          g.strokeStyle = `hsla(${hue}, 90%, 70%, ${k * 0.22})`;
          g.beginPath(); g.moveTo(a.x, a.y); g.lineTo(b.x, b.y); g.stroke();
        }
      }
    }
    g.fillStyle = `hsla(${hue}, 95%, 78%, 0.75)`;
    for (const p of pts) { g.beginPath(); g.arc(p.x, p.y, p.r, 0, Math.PI * 2); g.fill(); }
  }
  requestAnimationFrame(frame);

  // grano de película (se genera una vez)
  const nz = document.createElement("canvas");
  nz.width = nz.height = 160;
  const ng = nz.getContext("2d");
  const id = ng.createImageData(160, 160);
  for (let i = 0; i < id.data.length; i += 4) {
    const v = Math.random() * 255;
    id.data[i] = id.data[i + 1] = id.data[i + 2] = v;
    id.data[i + 3] = 255;
  }
  ng.putImageData(id, 0, 0);
  const grain = document.querySelector(".grain");
  if (grain) grain.style.backgroundImage = `url(${nz.toDataURL()})`;

  window.BG = {
    setHue(h) {
      const o = { h: hue };
      gsap.to(o, { h, duration: 1.2, ease: "power2.inOut", onUpdate: () => { hue = o.h; } });
    },
    burst(v = 1) { burst = v * 4; },
    setLite(v) { lite = v; },
  };
})();
