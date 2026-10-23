/* Invitación web de demostración — Mis XV Valentina (datos ficticios) */
(() => {
  // ====== Configuración del evento (editar para cada cliente) ======
  const EVENTO = {
    nombre: 'Valentina',
    fecha: new Date('2027-03-13T21:30:00-03:00'),
    // Número del organizador en formato internacional sin "+", p. ej. "549XXXXXXXXXX".
    // Vacío = modo demostración: WhatsApp se abre para elegir el contacto.
    whatsapp: ''
  };

  const $ = s => document.querySelector(s);
  const body = document.body;
  body.classList.add('cerrada');

  // ====== Brillos de fondo ======
  const cv = $('#brillos'), ctx = cv.getContext('2d');
  let W = 0, H = 0, dpr = Math.min(2, window.devicePixelRatio || 1);
  const pts = [];
  function medir() {
    W = cv.width = innerWidth * dpr; H = cv.height = innerHeight * dpr;
  }
  medir(); addEventListener('resize', medir);
  let semilla = 7;
  const rnd = () => (semilla = (semilla * 16807) % 2147483647) / 2147483647;
  for (let i = 0; i < 70; i++) pts.push({ x: rnd(), y: rnd(), r: .6 + rnd() * 1.8, v: .004 + rnd() * .012, f: rnd() * 6.28, s: .5 + rnd() * 2 });
  function dibujar(t) {
    ctx.clearRect(0, 0, W, H);
    for (const p of pts) {
      const y = ((p.y - t * p.v / 1000) % 1 + 1) % 1;
      const a = .25 + .75 * Math.max(0, Math.sin(t / 1000 * p.s + p.f));
      const x = p.x * W + Math.sin(t / 1600 + p.f) * 12 * dpr, yy = y * H, r = p.r * dpr * (.6 + a * .6);
      ctx.fillStyle = `rgba(233,238,252,${a * .8})`;
      ctx.beginPath(); ctx.arc(x, yy, r, 0, 6.283); ctx.fill();
      if (a > .85) { ctx.strokeStyle = `rgba(233,238,252,${(a - .85) * 4})`; ctx.lineWidth = dpr * .6; ctx.beginPath(); ctx.moveTo(x - r * 4, yy); ctx.lineTo(x + r * 4, yy); ctx.moveTo(x, yy - r * 4); ctx.lineTo(x, yy + r * 4); ctx.stroke(); }
    }
    requestAnimationFrame(dibujar);
  }
  requestAnimationFrame(dibujar);

  // ====== Música ======
  const audio = $('#audio'), btnM = $('#btnMusica');
  audio.volume = .55;
  function musica(on) {
    btnM.setAttribute('aria-pressed', on); btnM.setAttribute('aria-label', on ? 'Pausar música' : 'Reproducir música');
    if (on) audio.play().catch(() => {}); else audio.pause();
  }
  btnM.addEventListener('click', () => musica(audio.paused));

  // ====== Apertura ======
  const portada = $('#portada');
  function abrir() {
    if (portada.classList.contains('abriendo')) return;
    portada.classList.add('abriendo');
    musica(true);
    setTimeout(() => portada.classList.add('saliendo'), 1300);
    setTimeout(() => { body.classList.remove('cerrada'); body.classList.add('abierta'); }, 1700);
    setTimeout(() => portada.classList.add('fuera'), 2800);
  }
  $('#btnAbrir').addEventListener('click', abrir);
  $('#btnAbrir2').addEventListener('click', abrir);

  // ====== Cuenta regresiva ======
  const cel = { d: $('#cDias'), h: $('#cHoras'), m: $('#cMin'), s: $('#cSeg') };
  const dos = n => String(n).padStart(2, '0');
  function poner(el, v) { if (el.textContent !== v) { el.textContent = v; el.classList.remove('tic'); void el.offsetWidth; el.classList.add('tic'); } }
  function tick() {
    let ms = Math.max(0, EVENTO.fecha - Date.now());
    const d = Math.floor(ms / 864e5); ms -= d * 864e5;
    const h = Math.floor(ms / 36e5); ms -= h * 36e5;
    const m = Math.floor(ms / 6e4); ms -= m * 6e4;
    poner(cel.d, String(d)); poner(cel.h, dos(h)); poner(cel.m, dos(m)); poner(cel.s, dos(Math.floor(ms / 1000)));
  }
  tick(); setInterval(tick, 1000);

  // ====== Revelado al desplazar ======
  const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }), { threshold: .18 });
  document.querySelectorAll('.rv').forEach(el => io.observe(el));

  // ====== Galería ======
  const visor = $('#visor');
  document.querySelectorAll('.foto').forEach(f => f.addEventListener('click', () => { visor.querySelector('img').src = f.dataset.src; visor.classList.add('on'); }));
  visor.addEventListener('click', () => visor.classList.remove('on'));

  // ====== Confirmación de asistencia ======
  const modal = $('#modal'), cant = $('#fCant'), toast = $('#toast');
  let n = 1;
  $('#btnRsvp').addEventListener('click', () => { modal.classList.add('on'); setTimeout(() => $('#fNombre').focus(), 300); });
  modal.querySelector('.cerrar').addEventListener('click', () => modal.classList.remove('on'));
  modal.addEventListener('click', e => { if (e.target === modal) modal.classList.remove('on'); });
  modal.querySelectorAll('.contador button').forEach(b => b.addEventListener('click', () => { n = Math.min(10, Math.max(1, n + +b.dataset.d)); cant.textContent = n; }));
  function avisar(txt) { toast.textContent = txt; toast.classList.add('on'); setTimeout(() => toast.classList.remove('on'), 2600); }
  $('#formRsvp').addEventListener('submit', e => {
    e.preventDefault();
    const nombre = $('#fNombre').value.trim();
    const msg = $('#fMsg').value.trim();
    const texto = `¡Hola! Confirmo mi asistencia a los XV de ${EVENTO.nombre}.\nNombre: ${nombre}\nPersonas: ${n}` + (msg ? `\nMensaje: ${msg}` : '');
    const url = `https://wa.me/${EVENTO.whatsapp}?text=${encodeURIComponent(texto)}`;
    modal.classList.remove('on');
    avisar('✓ ¡Gracias, ' + (nombre.split(' ')[0] || 'te esperamos') + '! Abriendo WhatsApp…');
    setTimeout(() => window.open(url, '_blank', 'noopener'), 900);
  });
  window.__evento = EVENTO;
})();
