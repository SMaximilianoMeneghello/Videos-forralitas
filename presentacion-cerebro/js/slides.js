// ============================================================
//  DIAPOSITIVAS — "YOUR BRAIN IS LYING TO YOU" (en inglés)
//
//  Cada diapositiva tiene:
//   id, title    -> nombre (se ve en el control remoto)
//   hue          -> color principal (0-360)
//   transition   -> dive | warp | sweep | glitch | burst | iris | rise
//   notes[]      -> qué decir en cada parte: en (inglés) + es (traducción).
//                   Hay una nota por cada parte: la 0 al entrar, la 1 cuando
//                   aparece la parte 1, etc. Solo se ven en tu celular.
//   hold[]       -> segundos EXTRA de espera en cada parte (para votar o
//                   mirar fijo). El tiempo total de cada parte se calcula
//                   solo: lo que tarda decir la nota + hold.
//   facts[]      -> datos clave para tu celular (por si te olvidás algo)
//   html         -> contenido (en pantalla van solo puntos clave)
//   enter / step -> animaciones especiales
//
//  Las partes avanzan SOLAS. El botón SIGUIENTE pasa de diapositiva.
//
//  Atributos de animación en el HTML:
//   data-in="up|down|left|right|zoom|fade|letters|blur|pop|slowmo|stamp|flip|draw"
//   data-d="0.5"     -> retardo en segundos
//   data-step="1"    -> aparece recién en la parte 1, 2, ...
//   data-count="50"  -> número que cuenta hacia arriba
// ============================================================
(function () {
  const I = window.ILLUSIONS;

  // cuenta regresiva en un elemento (span) y llama a onEnd al terminar
  function countdown(ctx, el, secs, onEnd) {
    let s = secs;
    el.textContent = s;
    ctx.tween(el.parentElement, { opacity: 0, scale: 0.6 }, { opacity: 1, scale: 1, duration: 0.6, ease: "back.out(2)" });
    ctx.every(1000, () => {
      s--;
      if (s >= 0) { el.textContent = s; ctx.sfx.tick(s <= 3); }
      if (s === 0) ctx.after(300, () => { onEnd && onEnd(); });
    });
  }

  const memorySVG = (changed) => `
<svg viewBox="0 0 480 360" preserveAspectRatio="none">
  <defs><linearGradient id="msky${changed ? 1 : 0}" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="${changed ? "#3b1d6e" : "#ff9a5a"}"/><stop offset="1" stop-color="${changed ? "#e2557a" : "#ffd27a"}"/></linearGradient></defs>
  <rect width="480" height="360" fill="url(#msky${changed ? 1 : 0})"/>
  <circle cx="${changed ? 120 : 330}" cy="${changed ? 90 : 170}" r="${changed ? 34 : 56}" fill="${changed ? "#fff4d6" : "#fff2a8"}"/>
  <rect y="200" width="480" height="160" fill="${changed ? "#1f5a8a" : "#2a8ec2"}"/>
  <path d="M0 260 Q120 240 240 262 T480 258 L480 360 L0 360 Z" fill="#f2d49b"/>
  <g fill="#1b1b22">
    <circle cx="150" cy="232" r="11"/><rect x="141" y="242" width="18" height="40" rx="7"/>
    <circle cx="190" cy="238" r="9"/><rect x="183" y="246" width="15" height="32" rx="6"/>
    ${changed ? `<circle cx="232" cy="236" r="10"/><rect x="224" y="245" width="16" height="36" rx="6"/>` : ""}
  </g>
  ${changed ? `<g><line x1="390" y1="120" x2="380" y2="250" stroke="#fff" stroke-width="2"/><ellipse cx="392" cy="100" rx="22" ry="28" fill="#ff3b6b"/></g>` : `<path d="M60 120 l14 -8 l14 8 M100 100 l12 -7 l12 7" stroke="#3b2a20" stroke-width="4" fill="none"/>`}
</svg>`;

  // círculos de Ebbinghaus (centros naranjas IGUALES: r = 52)
  const ring = (cx, cy, n, dist, r) => Array.from({ length: n }, (_, i) => {
    const a = (i / n) * Math.PI * 2;
    return `<circle cx="${(cx + Math.cos(a) * dist).toFixed(1)}" cy="${(cy + Math.sin(a) * dist).toFixed(1)}" r="${r}"/>`;
  }).join("");
  const ebbSVG = `
<svg viewBox="0 0 1380 560" class="ebb">
  <g class="blue" fill="#3b82f6">
    <g class="ring-l">${ring(400, 280, 6, 172, 80)}</g>
    <g class="ring-r">${ring(980, 280, 8, 92, 24)}</g>
  </g>
  <g class="or-l"><circle cx="400" cy="280" r="52" fill="#ff8a1f"/></g>
  <g class="or-r"><circle cx="980" cy="280" r="52" fill="#ff8a1f"/></g>
  <g class="measure" opacity="0" stroke="#22d3ee" stroke-width="4" stroke-dasharray="12 10">
    <line x1="0" y1="228" x2="1380" y2="228"/><line x1="0" y1="332" x2="1380" y2="332"/>
  </g>
</svg>`;

  const S = [];

  // 1 ─────────────────────────────────────────────── PORTADA
  S.push({
    id: "portada", title: "Cover", hue: 265, transition: "burst",
    notes: [
      { en: "Hello everyone! My name is ___, and today I'm going to talk about something you use every second: your brain. Quick question: who thinks that what you see is reality, exactly as it is? Raise your hand! … Well, today I'm going to show you that your brain is lying to you… all the time.",
        es: "¡Hola a todos! Me llamo ___ y hoy voy a hablar de algo que usan cada segundo: su cerebro. Pregunta rápida: ¿quién cree que lo que ve es la realidad, tal cual es? ¡Levanten la mano! … Bueno, hoy les voy a demostrar que su cerebro les miente… todo el tiempo." },
    ],
    facts: [
      "Tema: las ilusiones muestran los ATAJOS que usa el cerebro para ver rápido.",
      "Plan: 9 ilusiones en vivo + memoria + juego final con los celulares.",
    ],
    html: (cfg) => `
      <canvas class="fill brain-cv" width="1600" height="900"></canvas>
      <div class="portada">
        <div class="kicker" data-in="fade" data-d="1.4">${cfg.materia ? cfg.materia + " · " : ""}Presentation</div>
        <h1 class="h-xl" data-in="letters" data-d="1.8">YOUR BRAIN</h1>
        <h1 class="h-xl accent glitch" data-text="IS LYING TO YOU" data-in="letters" data-d="2.3">IS LYING TO YOU</h1>
        <p class="lead" data-in="up" data-d="3.1">9 live illusions · 1 final game</p>
        <div class="presenter" data-in="fade" data-d="3.7">Presented by <b>${cfg.presentador}</b></div>
      </div>`,
    enter(ctx) {
      const b = I.brainParticles(ctx.$(".brain-cv"), { cx: 800, cy: 225, w: ctx.lite ? 380 : 430, step: ctx.lite ? 9 : 7 });
      ctx.raf((t) => b.frame(t));
      ctx.after(3300, () => ctx.$(".glitch").classList.add("on"));
      ctx.after(1500, () => ctx.sfx.boom(0.6));
    },
  });

  // 2 ─────────────────────────────────────────────── EL CEREBRO PREDICE
  S.push({
    id: "realidad", title: "What you see is not reality", hue: 200, transition: "dive",
    notes: [
      { en: "Every second, your senses send your brain about eleven million bits of information. But your conscious mind can only process about fifty. That's a huge difference!",
        es: "Cada segundo, tus sentidos le mandan al cerebro unos once millones de bits de información. Pero tu mente consciente solo puede procesar unos cincuenta. ¡Es una diferencia enorme!" },
      { en: "And your brain is expensive. It's only two percent of your body weight, but it uses about twenty percent of your energy.",
        es: "Y tu cerebro es caro: es solo el 2% de tu peso, pero usa cerca del 20% de tu energía." },
      { en: "So, to save energy, it takes shortcuts. It doesn't check everything: it predicts what is out there. Most of the time it's right… but today we are going to catch it lying.",
        es: "Entonces, para ahorrar energía, toma atajos. No revisa todo: predice lo que hay afuera. Casi siempre acierta… pero hoy lo vamos a agarrar mintiendo." },
    ],
    hold: [2, 1, 0],
    facts: [
      "≈11.000.000 bits/s llegan de los sentidos; la mente consciente procesa ≈50. Es una estimación clásica (Manfred Zimmermann), no un número exacto.",
      "El cerebro adulto pesa 1,3–1,4 kg (≈2% del cuerpo) y usa ≈20% de la energía en reposo.",
      "Idea de toda la expo: el cerebro PREDICE para ahorrar energía → cuando se equivoca = ilusión.",
    ],
    html: () => `
      <div class="col center wrap">
        <div class="kicker" data-in="fade">The big idea</div>
        <h2 class="h-l" data-in="letters" data-d=".2">What you see is <span class="accent">not</span> reality</h2>
        <div class="row stats">
          <div class="card stat" data-in="left" data-d=".9">
            <div class="stat-label">👁️ Senses → brain</div>
            <div class="big-num" data-count="11000000">0</div>
            <div class="stat-unit">bits per second</div>
            <div class="dots-field"></div>
          </div>
          <div class="vs" data-in="zoom" data-d="1.3">VS</div>
          <div class="card stat" data-in="right" data-d="1.1">
            <div class="stat-label">🧠 Conscious mind</div>
            <div class="big-num accent" data-count="50">0</div>
            <div class="stat-unit">bits per second</div>
            <div class="dots-one"><i></i></div>
          </div>
        </div>
        <div class="row pills" data-step="1" data-in="up">
          <span class="pill">⚖️ <b>2%</b> of your weight</span><span class="arrow-r">→</span><span class="pill hot">⚡ <b>20%</b> of your energy</span>
        </div>
        <p class="punch small" data-step="2" data-in="letters">Shortcuts → it <span class="accent">PREDICTS</span> → sometimes it’s <span class="accent2">wrong</span></p>
      </div>`,
    enter(ctx) {
      let h = "";
      for (let i = 0; i < 260; i++) h += `<i style="animation-delay:${(Math.random() * 2).toFixed(2)}s"></i>`;
      ctx.$(".dots-field").innerHTML = h;
    },
  });

  // 3 ─────────────────────────────────────────────── CAFÉ WALL
  S.push({
    id: "cafe", title: "1 · Café wall", hue: 0, transition: "sweep",
    notes: [
      { en: "Illusion number one. Look at the gray lines between the tiles. Are they straight, or are they tilted? Raise your hand if you think they're tilted!",
        es: "Ilusión número uno. Miren las líneas grises entre las baldosas. ¿Son rectas o están inclinadas? ¡Levanten la mano si creen que están inclinadas!" },
      { en: "They are perfectly straight and parallel! These red lines prove it. The tiles are shifted half a tile, and the gray lines confuse the cells in your eyes that detect edges.",
        es: "¡Son perfectamente rectas y paralelas! Estas líneas rojas lo prueban. Las baldosas están corridas media baldosa, y las líneas grises confunden a las células del ojo que detectan bordes." },
      { en: "Watch the tiles move. When they line up, the lines look straight. When they shift, the lines tilt again. A scientist, Richard Gregory, saw this on the wall of a real café in England, in 1979.",
        es: "Miren cómo se mueven las baldosas. Cuando se alinean, las líneas se ven rectas. Cuando se corren, se inclinan de nuevo. Un científico, Richard Gregory, vio esto en la pared de un café de verdad en Inglaterra, en 1979." },
    ],
    hold: [5, 1, 4],
    facts: [
      "Café Wall: Richard Gregory y Priscilla Heard, 1979 (pared de un café en Bristol, Inglaterra).",
      "Clave: filas corridas MEDIA baldosa + junta GRIS. Con junta blanca o negra la ilusión casi desaparece.",
      "Las líneas son 100% rectas y paralelas (las rojas lo muestran).",
    ],
    html: () => `
      <div class="ill">
        <div class="ill-head"><div class="kicker" data-in="fade">Illusion 1 · Café wall</div>
          <h2 class="h-m" data-in="letters" data-d=".2">Are the gray lines <span class="accent">tilted?</span></h2></div>
        <div class="ill-stage" data-in="slowmo" data-d=".4"><canvas class="cafe-cv" width="1380" height="560"></canvas></div>
        <div class="chips">
          <span class="chip2 vote" data-in="up" data-d="1.2">✋ Tilted</span><span class="chip2 vote" data-in="up" data-d="1.35">✋ Straight</span>
          <span class="chip2 ok" data-step="1" data-in="stamp">✔ 100% straight &amp; parallel</span>
          <span class="chip2" data-step="2" data-in="up">Gregory &amp; Heard · 1979</span>
        </div>
      </div>`,
    enter(ctx) { ctx.data.w = I.cafeWall(ctx.$(".cafe-cv")); },
    step(ctx, n) {
      const w = ctx.data.w;
      ctx.$$(".chip2.vote").forEach((c) => ctx.tween(c, { opacity: 0, scale: 0.8, duration: 0.4, onComplete: () => (c.style.display = "none") }));
      if (n === 1) {
        const o = { g: 0 };
        ctx.tween(o, { g: 1, duration: 1.4, ease: "power2.inOut", onUpdate: () => w.set(undefined, o.g) });
      }
      if (n === 2) {
        // las filas se alinean y se vuelven a correr, una y otra vez
        const o = { s: 0.5, g: 1 };
        ctx.tween(o, { g: 0, duration: 0.8, onUpdate: () => w.set(o.s, o.g) });
        ctx.tween(o, { s: 0, duration: 2.4, ease: "sine.inOut", yoyo: true, repeat: -1, delay: 0.9, onUpdate: () => w.set(o.s, o.g) });
      }
    },
  });

  // 4 ─────────────────────────────────────────────── EBBINGHAUS
  S.push({
    id: "ebbinghaus", title: "2 · Ebbinghaus circles", hue: 28, transition: "warp",
    notes: [
      { en: "Illusion number two. Which orange circle is bigger: the one on the left, or the one on the right? Vote!",
        es: "Ilusión número dos. ¿Qué círculo naranja es más grande: el de la izquierda o el de la derecha? ¡Voten!" },
      { en: "Let's take away the blue circles… and put the orange ones together.",
        es: "Saquemos los círculos azules… y juntemos los naranjas." },
      { en: "They are exactly the same size! Your brain doesn't measure things alone: it compares them with what is around them. Next to big circles, a circle looks small. Next to small circles, it looks big. This is the Ebbinghaus illusion.",
        es: "¡Son exactamente del mismo tamaño! Tu cerebro no mide las cosas solas: las compara con lo que tienen alrededor. Al lado de círculos grandes, un círculo parece chico. Al lado de círculos chicos, parece grande. Es la ilusión de Ebbinghaus." },
    ],
    hold: [6, 1, 0],
    facts: [
      "Ilusión de Ebbinghaus (Hermann Ebbinghaus); la publicó Titchener en 1901.",
      "El cerebro juzga el TAMAÑO por COMPARACIÓN con lo de alrededor.",
      "Dato curioso: en chicos menores de 10 años la ilusión es más débil (Doherty y colegas, 2010).",
    ],
    html: () => `
      <div class="ill">
        <div class="ill-head"><div class="kicker" data-in="fade">Illusion 2 · Size</div>
          <h2 class="h-m" data-in="letters" data-d=".2">Which <span class="accent">orange</span> circle is bigger?</h2></div>
        <div class="ill-stage clear" data-in="zoom" data-d=".5">${ebbSVG}</div>
        <div class="chips">
          <span class="chip2 vote" data-in="up" data-d="1.2">✋ Left</span><span class="chip2 vote" data-in="up" data-d="1.35">✋ Right</span><span class="chip2 vote" data-in="up" data-d="1.5">✋ Same</span>
          <span class="chip2 ok" data-step="2" data-in="stamp">✔ Exactly the same size</span>
          <span class="chip2" data-step="2" data-in="up" data-d=".5">Size = comparison</span>
        </div>
      </div>`,
    step(ctx, n) {
      ctx.$$(".chip2.vote").forEach((c) => ctx.tween(c, { opacity: 0, scale: 0.8, duration: 0.4, onComplete: () => (c.style.display = "none") }));
      if (n === 1) {
        ctx.tween(ctx.$(".ring-l"), { opacity: 0, scale: 1.4, svgOrigin: "400 280", duration: 1.2, ease: "power2.in" });
        ctx.tween(ctx.$(".ring-r"), { opacity: 0, scale: 0.4, svgOrigin: "980 280", duration: 1.2, ease: "power2.in", delay: 0.2 });
        ctx.tween(ctx.$(".or-l"), { x: 236, duration: 1.4, delay: 1.5, ease: "expo.inOut" });
        ctx.tween(ctx.$(".or-r"), { x: -236, duration: 1.4, delay: 1.5, ease: "expo.inOut" });
        ctx.sfx.whoosh(0.6);
      }
      if (n === 2) ctx.tween(ctx.$(".measure"), { opacity: 1, duration: 0.8 });
    },
  });

  // 5 ─────────────────────────────────────────────── REJILLA CENTELLEANTE
  S.push({
    id: "grid", title: "3 · Scintillating grid", hue: 210, transition: "glitch",
    notes: [
      { en: "Illusion number three. Look at this grid and count the black dots. Move your eyes around… How many black dots can you see?",
        es: "Ilusión número tres. Miren esta rejilla y cuenten los puntos negros. Muevan los ojos… ¿Cuántos puntos negros ven?" },
      { en: "Zero! There are no black dots. All the dots are white. The black dots appear where you are NOT looking, and they disappear when you look at them.",
        es: "¡Cero! No hay ningún punto negro. Todos los puntos son blancos. Los negros aparecen donde NO estás mirando, y desaparecen cuando los mirás." },
      { en: "And look what happens if I bend the lines… the black dots are gone! This is the Scintillating Grid. Scientists still don't completely agree on why it happens.",
        es: "Y miren qué pasa si curvo las líneas… ¡los puntos negros desaparecen! Es la rejilla centelleante. Los científicos todavía no se ponen totalmente de acuerdo en por qué pasa." },
    ],
    hold: [7, 1, 3],
    facts: [
      "Rejilla centelleante (Scintillating grid): Bergen 1985; estudiada por Schrauf y colegas en 1997.",
      "Fondo negro, barras grises y discos BLANCOS. Los puntos negros aparecen en la visión periférica.",
      "Si las líneas se curvan, los puntos negros desaparecen (lo muestra Michael Bach).",
      "Michael Bach (científico de la visión, Univ. de Friburgo) la marca como ilusión 'fuerte'.",
    ],
    html: () => `
      <div class="ill">
        <div class="ill-head"><div class="kicker" data-in="fade">Illusion 3 · Scintillating grid</div>
          <h2 class="h-m" data-in="letters" data-d=".2">Count the <span class="accent">black</span> dots</h2></div>
        <div class="ill-stage" data-in="slowmo" data-d=".4"><canvas class="grid-cv" width="1380" height="560"></canvas></div>
        <div class="chips">
          <span class="chip2 ok" data-step="1" data-in="stamp">0 black dots · all of them are white</span>
          <span class="chip2" data-step="2" data-in="up">Bend the lines → the dots vanish</span>
        </div>
      </div>`,
    enter(ctx) { ctx.data.g = I.scintGrid(ctx.$(".grid-cv")); },
    step(ctx, n) {
      if (n === 2) {
        const o = { a: 0 };
        ctx.tween(o, { a: 26, duration: 2.5, ease: "power2.inOut", onUpdate: () => ctx.data.g.draw(o.a) });
        ctx.sfx.shimmer();
      }
    },
  });

  // 6 ─────────────────────────────────────────────── LILAC CHASER
  S.push({
    id: "lilac", title: "4 · Lilac chaser (stare)", hue: 300, transition: "iris",
    notes: [
      { en: "Illusion number four. Look ONLY at the black cross in the middle. Don't move your eyes! Watch the pink dots with the corner of your eye.",
        es: "Ilusión número cuatro. Miren SOLO la cruz negra del medio. ¡No muevan los ojos! Miren los puntos rosas con el rabillo del ojo." },
      { en: "Keep looking at the cross… What happens to the pink dots? And what color is the dot running around?",
        es: "Sigan mirando la cruz… ¿Qué les pasa a los puntos rosas? ¿Y de qué color es el punto que da vueltas?" },
      { en: "The pink dots disappear, and a GREEN dot runs in a circle. But there is NO green on the screen! Your eyes get tired of pink and show the opposite color. This is the Lilac Chaser, created by Jeremy Hinton in 2005.",
        es: "Los puntos rosas desaparecen y un punto VERDE da vueltas. ¡Pero NO hay verde en la pantalla! Tus ojos se cansan del rosa y muestran el color opuesto. Es el Lilac Chaser, creado por Jeremy Hinton en 2005." },
    ],
    hold: [1, 17, 0],
    facts: [
      "Lilac chaser (o ilusión Pac-Man): Jeremy Hinton, 2005. 12 puntos lila difuminados sobre gris.",
      "Mezcla 3 efectos: POSTIMAGEN (el verde = color opuesto al lila), desvanecimiento de TROXLER (si mirás fijo, lo borroso se borra) y fenómeno PHI (el hueco parece moverse).",
      "Si mueven los ojos, vuelve el rosa. Bach la marca como 'fuerte'.",
    ],
    html: () => `
      <div class="ill">
        <div class="ill-head"><div class="kicker" data-in="fade">Illusion 4 · Lilac chaser</div>
          <h2 class="h-m" data-in="letters" data-d=".2">Stare at the <span class="accent">cross</span></h2></div>
        <div class="ill-row">
          <div class="side">
            <div class="pt" data-in="left" data-d=".8"><i>👁️</i><span>Look <b>only</b> at the ✚</span></div>
            <div class="pt" data-in="left" data-d="1"><i>🚫</i><span>Don’t move your eyes</span></div>
            <div class="pt" data-in="left" data-d="1.2"><i>⏱️</i><span>About <b>20 seconds</b></span></div>
          </div>
          <div class="ill-stage sq" data-in="zoom" data-d=".5"><canvas class="lilac-cv" width="560" height="560"></canvas>
            <div class="stare"><span>20</span></div></div>
          <div class="side">
            <div class="pt" data-step="2" data-in="right"><i>🟢</i><span>A <b>green</b> dot appears…</span></div>
            <div class="pt" data-step="2" data-in="right" data-d=".3"><i>🚫</i><span>…but there’s <b>no green</b> on the screen</span></div>
            <div class="pt" data-step="2" data-in="right" data-d=".6"><i>👻</i><span>The pink dots <b>fade away</b></span></div>
          </div>
        </div>
      </div>`,
    enter(ctx) {
      const l = I.lilacChaser(ctx.$(".lilac-cv"));
      ctx.every(110, () => l.step());
    },
    step(ctx, n) { if (n === 1) countdown(ctx, ctx.$(".stare span"), 20); },
  });

  // 7 ─────────────────────────────────────────────── BANDERA (POSTIMAGEN)
  S.push({
    id: "postimagen", title: "5 · Flag afterimage (stare)", hue: 30, transition: "iris",
    notes: [
      { en: "Illusion number five. Everybody, look at the white dot in the middle, without moving your eyes. When the screen turns white, keep looking at the dot!",
        es: "Ilusión número cinco. Todos miren el punto blanco del medio, sin mover los ojos. ¡Cuando la pantalla se ponga blanca, sigan mirando el punto!" },
      { en: "(Stay quiet during the countdown.) When it turns white, ask: What did you see?",
        es: "(Silencio durante la cuenta.) Cuando se ponga blanca, preguntá: ¿Qué vieron?" },
      { en: "You saw the light blue and white flag, right? But it was never on the screen! The cells that detect color got tired, so on white they show the opposite colors. This is called a negative afterimage.",
        es: "Vieron la bandera celeste y blanca, ¿no? ¡Pero nunca estuvo en la pantalla! Las células que detectan el color se cansaron, así que sobre el blanco muestran los colores opuestos. Se llama postimagen negativa." },
    ],
    hold: [1, 23, 0],
    facts: [
      "Postimagen negativa: los conos (células del color) se adaptan/cansan; sobre blanco aparece el color COMPLEMENTARIO.",
      "En la pantalla: marrón → se ve celeste · negro → se ve blanco · azul → se ve amarillo (el sol).",
      "Funciona mejor con poca luz en el aula y mirando fijo el punto.",
    ],
    html: () => `
      <div class="col center wrap">
        <div class="kicker" data-in="fade">Illusion 5 · Afterimage</div>
        <h2 class="h-m" data-in="letters" data-d=".2">Stare at the dot for <span class="accent">20 seconds</span></h2>
        <div class="flag-wrap" data-in="zoom" data-d=".6">
          <div class="flag inv">
            <div class="fs" style="background:#8b5320"></div>
            <div class="fs mid" style="background:#000"><div class="sun-inv"></div></div>
            <div class="fs" style="background:#8b5320"></div>
          </div>
          <div class="fix-dot"></div>
        </div>
        <div class="countdown"><span>20</span></div>
      </div>
      <div class="white-screen"><div class="fix-dot"></div><div class="ws-q">Can you see it? 👀</div>
        <div class="ws-explain">🇦🇷 You saw the <b>real flag</b>… but it was <b>never</b> on the screen<br>Tired color cells → <b>opposite colors</b> = afterimage</div>
      </div>`,
    step(ctx, n) {
      const ws = ctx.$(".white-screen");
      const goWhite = () => {
        if (ctx.data.white) return;
        ctx.data.white = true;
        gsap.set(ws, { display: "flex", opacity: 1 });
        ctx.bodyClass("no-vignette");
        ctx.sfx.boom(0.35);
        ctx.tween(ctx.$(".ws-q"), { opacity: 0 }, { opacity: 1, delay: 4, duration: 1 });
      };
      if (n === 1) countdown(ctx, ctx.$(".countdown span"), 20, goWhite);
      if (n === 2) {
        goWhite();
        ctx.tween(ctx.$(".ws-q"), { opacity: 0, duration: 0.3 });
        ctx.tween(ctx.$(".ws-explain"), { opacity: 0, y: 40 }, { opacity: 1, y: 0, duration: 1, ease: "expo.out" });
      }
    },
  });

  // 8 ─────────────────────────────────────────────── ESPIRAL (MOVIMIENTO CONSECUTIVO)
  S.push({
    id: "espiral", title: "6 · Spiral (stare 25 s)", hue: 330, transition: "burst",
    notes: [
      { en: "Illusion number six. Look at the red dot in the center of the spiral, and don't move your eyes for twenty-five seconds.",
        es: "Ilusión número seis. Miren el punto rojo del centro de la espiral y no muevan los ojos durante veinticinco segundos." },
      { en: "(Stay quiet.) Keep looking at the center… When it stops, look at the picture, or at your hand!",
        es: "(Silencio.) Sigan mirando el centro… ¡Cuando se frene, miren la imagen o su mano!" },
      { en: "It looks like it's moving or breathing, right? But it's a still picture! The cells in your brain that detect movement got tired, so now they show movement in the opposite direction. This is the motion aftereffect, also called the waterfall illusion.",
        es: "Parece que se mueve o que respira, ¿no? ¡Pero es una imagen quieta! Las células del cerebro que detectan el movimiento se cansaron, así que ahora muestran movimiento en la dirección contraria. Es el efecto consecutivo de movimiento, también llamado ilusión de la cascada." },
    ],
    hold: [1, 24, 0],
    facts: [
      "Efecto consecutivo de movimiento (motion aftereffect / ilusión de la cascada). La espiral la describió Joseph Plateau en 1849.",
      "Después de ~30 s de mirar movimiento, lo quieto parece moverse AL REVÉS. Dura unos segundos.",
      "Las neuronas del movimiento están en el CEREBRO, no en el ojo (Bach). Si a alguien lo marea, que mire para otro lado.",
    ],
    html: () => `
      <div class="ill">
        <div class="ill-head"><div class="kicker" data-in="fade">Illusion 6 · Motion aftereffect</div>
          <h2 class="h-m" data-in="letters" data-d=".2">Stare at the <span class="accent">red dot</span></h2></div>
        <div class="ill-row">
          <div class="side">
            <div class="pt" data-in="left" data-d=".8"><i>🎯</i><span>Look at the <b>center</b></span></div>
            <div class="pt" data-in="left" data-d="1"><i>⏱️</i><span><b>25 seconds</b>, don’t look away</span></div>
            <div class="pt" data-in="left" data-d="1.2"><i>✋</i><span>Then look at the <b>picture</b> or your <b>hand</b></span></div>
          </div>
          <div class="ill-stage sq round" data-in="zoom" data-d=".5"><canvas class="spiral-cv" width="540" height="540"></canvas>
            <div class="stare"><span>25</span></div></div>
          <div class="side">
            <div class="pt" data-step="2" data-in="right"><i>🌊</i><span>Still things look like they <b>move</b></span></div>
            <div class="pt" data-step="2" data-in="right" data-d=".3"><i>😴</i><span>Motion cells got <b>tired</b></span></div>
            <div class="pt" data-step="2" data-in="right" data-d=".6"><i>📜</i><span>Plateau · <b>1849</b></span></div>
          </div>
        </div>
        <div class="after-pic">${I.sceneSVG(true)}</div>
      </div>`,
    enter(ctx) {
      const cv = ctx.$(".spiral-cv");
      I.spiral(cv);
      ctx.data.spin = ctx.tween(cv, { rotation: -360, duration: 1.6, ease: "none", repeat: -1 });
    },
    step(ctx, n) {
      const showPic = () => {
        if (ctx.data.pic) return;
        ctx.data.pic = true;
        ctx.data.spin.kill();
        const p = ctx.$(".after-pic");
        gsap.set(p, { display: "block" });
        ctx.tween(p, { opacity: 0 }, { opacity: 1, duration: 0.15 });
        ctx.sfx.boom(0.3);
      };
      if (n === 1) countdown(ctx, ctx.$(".stare span"), 25, showPic);
      if (n === 2) { showPic(); ctx.tween(ctx.$(".after-pic"), { scale: 0.62, y: -40, duration: 1.2, ease: "expo.inOut", delay: 4 }); }
    },
  });

  // 9 ─────────────────────────────────────────────── STEPPING FEET
  S.push({
    id: "pasos", title: "7 · Stepping feet", hue: 52, transition: "dive",
    notes: [
      { en: "Illusion number seven. Watch the blue and the yellow rectangles. They look like two feet walking: step, step, step. Which one is faster?",
        es: "Ilusión número siete. Miren el rectángulo azul y el amarillo. Parecen dos pies caminando: paso, paso, paso. ¿Cuál es más rápido?" },
      { en: "Now I take away the black and white stripes…",
        es: "Ahora saco las rayas blancas y negras…" },
      { en: "They move together, at exactly the same speed, all the time! When something has high contrast with the background, it looks faster. With low contrast, it looks slower. This is the Stepping Feet illusion, by Stuart Anstis.",
        es: "¡Se mueven juntos, a la misma velocidad, todo el tiempo! Cuando algo tiene mucho contraste con el fondo, parece más rápido. Con poco contraste, parece más lento. Es la ilusión de los pasos, de Stuart Anstis." },
    ],
    hold: [6, 1, 0],
    facts: [
      "Stepping feet (ilusión de los pasos): Stuart Anstis, publicada entre 2001 y 2003.",
      "La velocidad que percibimos depende del CONTRASTE: mucho contraste = parece más rápido.",
      "Con fondo gris liso se ve que van juntos. Bach la marca como 'fuerte'.",
    ],
    html: () => `
      <div class="ill">
        <div class="ill-head"><div class="kicker" data-in="fade">Illusion 7 · Stepping feet</div>
          <h2 class="h-m" data-in="letters" data-d=".2">Which one is <span class="accent">faster?</span></h2></div>
        <div class="ill-stage" data-in="slowmo" data-d=".4"><canvas class="feet-cv" width="1380" height="500"></canvas></div>
        <div class="chips">
          <span class="chip2 vote" data-in="up" data-d="1.2">✋ Blue</span><span class="chip2 vote" data-in="up" data-d="1.35">✋ Yellow</span><span class="chip2 vote" data-in="up" data-d="1.5">✋ Same</span>
          <span class="chip2 ok" data-step="2" data-in="stamp">✔ Same speed, always together</span>
          <span class="chip2" data-step="2" data-in="up" data-d=".5">High contrast = looks faster</span>
        </div>
      </div>`,
    enter(ctx) {
      const f = I.steppingFeet(ctx.$(".feet-cv"));
      ctx.data.f = f;
      ctx.raf((t) => f.draw(t / 1000));
    },
    step(ctx, n) {
      ctx.$$(".chip2.vote").forEach((c) => ctx.tween(c, { opacity: 0, scale: 0.8, duration: 0.4, onComplete: () => (c.style.display = "none") }));
      if (n === 1) {
        const o = { s: 1 };
        ctx.tween(o, { s: 0, duration: 2.5, ease: "power2.inOut", onUpdate: () => ctx.data.f.setStripes(o.s) });
      }
    },
  });

  // 10 ────────────────────────────────────────────── CEGUERA INDUCIDA POR MOVIMIENTO
  S.push({
    id: "mib", title: "8 · Disappearing dots", hue: 225, transition: "warp",
    notes: [
      { en: "Illusion number eight. Look at the small dot in the center. There are three yellow dots. Don't move your eyes, and tell me what happens to the yellow dots.",
        es: "Ilusión número ocho. Miren el puntito del centro. Hay tres puntos amarillos. No muevan los ojos y díganme qué les pasa a los puntos amarillos." },
      { en: "Do they disappear? One… two… sometimes all three!",
        es: "¿Desaparecen? Uno… dos… ¡a veces los tres!" },
      { en: "Now I stop the blue crosses. The yellow dots were ALWAYS there! They never disappeared. Your brain decided they were not important, and deleted them. This is called motion-induced blindness.",
        es: "Ahora freno las cruces azules. ¡Los puntos amarillos estuvieron SIEMPRE! Nunca desaparecieron. Tu cerebro decidió que no eran importantes y los borró. Se llama ceguera inducida por movimiento." },
    ],
    hold: [1, 14, 0],
    facts: [
      "Ceguera inducida por movimiento (motion-induced blindness): Bonneh, Cooperman y Sagi, revista Nature, 2001.",
      "Los puntos amarillos NUNCA se apagan: el cerebro los borra de la conciencia.",
      "Ayuda mirar fijo el centro; si parpadeás o movés los ojos, vuelven.",
    ],
    html: () => `
      <div class="ill">
        <div class="ill-head"><div class="kicker" data-in="fade">Illusion 8 · Motion-induced blindness</div>
          <h2 class="h-m" data-in="letters" data-d=".2">Keep the <span class="accent">yellow dots</span></h2></div>
        <div class="ill-row">
          <div class="side">
            <div class="pt" data-in="left" data-d=".8"><i>🎯</i><span>Look at the <b>center</b> dot</span></div>
            <div class="pt" data-in="left" data-d="1"><i>🟡</i><span>Watch the <b>3 yellow</b> dots</span></div>
            <div class="pt" data-in="left" data-d="1.2"><i>🤔</i><span>Do they <b>disappear?</b></span></div>
          </div>
          <div class="ill-stage sq" data-in="zoom" data-d=".5"><canvas class="mib-cv" width="560" height="560"></canvas></div>
          <div class="side">
            <div class="pt" data-step="2" data-in="right"><i>✅</i><span>They were <b>always</b> there</span></div>
            <div class="pt" data-step="2" data-in="right" data-d=".3"><i>🧠</i><span>Your brain <b>deleted</b> them</span></div>
            <div class="pt" data-step="2" data-in="right" data-d=".6"><i>📜</i><span>Bonneh et al. · <b>2001</b></span></div>
          </div>
        </div>
      </div>`,
    enter(ctx) {
      const m = I.mib(ctx.$(".mib-cv"));
      ctx.data.m = m;
      ctx.raf((t) => m.draw(t));
    },
    step(ctx, n) {
      if (n === 2) {
        const o = { v: 1 };
        ctx.tween(o, { v: 0, duration: 1.5, onUpdate: () => ctx.data.m.setSpeed(o.v) });
      }
    },
  });

  // 11 ────────────────────────────────────────────── ROTACIÓN AMBIGUA
  S.push({
    id: "giro", title: "9 · Which way is it spinning?", hue: 45, transition: "glitch",
    notes: [
      { en: "Last illusion. Which way is this cube spinning: to the left, or to the right? … Some of you say left, some say right! Keep looking: it can change direction in your head!",
        es: "Última ilusión. ¿Para qué lado gira este cubo: a la izquierda o a la derecha? … ¡Algunos dicen izquierda y otros derecha! Sigan mirando: ¡puede cambiar de sentido en tu cabeza!" },
      { en: "Now this arrow on a tube. Is it pointing up or down? Which way is it turning? Look again… it changes!",
        es: "Ahora esta flecha sobre un tubo. ¿Apunta para arriba o para abajo? ¿Para qué lado gira? Miren otra vez… ¡cambia!" },
      { en: "And this ball. Which way is the yellow circle turning?",
        es: "Y esta pelota. ¿Para qué lado gira el círculo amarillo?" },
      { en: "The truth is: both answers are correct! These are just dots moving on a flat screen. There is no information about what is in front and what is behind, so your brain has to guess. Now I add depth: the dots in front are bigger. Now everybody sees the same direction!",
        es: "La verdad: ¡las dos respuestas son correctas! Son solo puntos moviéndose en una pantalla plana. No hay información de qué está adelante y qué está atrás, así que tu cerebro tiene que adivinar. Ahora agrego profundidad: los puntos de adelante son más grandes. ¡Ahora todos ven el mismo sentido!" },
    ],
    hold: [7, 6, 5, 2],
    facts: [
      "Ilusiones de rotación ambigua (biestables): 'estructura a partir del movimiento' / efecto de profundidad cinética.",
      "Sin pistas de profundidad hay DOS interpretaciones igual de válidas; el cerebro elige una y a veces cambia sola.",
      "Es la misma familia que el cubo de Necker (Louis Necker, 1832).",
      "Al agregar profundidad (puntos de adelante más grandes) la ambigüedad desaparece.",
    ],
    html: () => `
      <div class="ill">
        <div class="ill-head"><div class="kicker" data-in="fade">Illusion 9 · Bistable motion</div>
          <h2 class="h-m" data-in="letters" data-d=".2">Which way is it <span class="accent">spinning?</span></h2></div>
        <div class="ill-row">
          <div class="side">
            <div class="pt big" data-in="left" data-d=".8"><i>⟲</i><span>To the <b>left?</b></span></div>
            <div class="pt big" data-in="left" data-d="1"><i>⟳</i><span>To the <b>right?</b></span></div>
            <div class="pt obj-name" data-in="left" data-d="1.2"><i>🧊</i><span>A cube</span></div>
          </div>
          <div class="ill-stage sq dark" data-in="zoom" data-d=".5"><canvas class="spin-cv" width="580" height="580"></canvas></div>
          <div class="side">
            <div class="pt" data-step="3" data-in="right"><i>✌️</i><span><b>Both</b> are correct</span></div>
            <div class="pt" data-step="3" data-in="right" data-d=".3"><i>🫥</i><span>No depth → the brain <b>guesses</b></span></div>
            <div class="pt" data-step="3" data-in="right" data-d=".6"><i>👓</i><span>Add depth → <b>one</b> answer</span></div>
          </div>
        </div>
      </div>`,
    enter(ctx) {
      const cv = ctx.$(".spin-cv");
      ctx.data.obj = I.spin3d(cv, "cube");
      ctx.raf((t) => ctx.data.obj.draw(t));
    },
    step(ctx, n) {
      const cv = ctx.$(".spin-cv");
      const names = { 1: ["🧪", "An arrow on a tube"], 2: ["🔮", "A ball with a disc"] };
      if (n === 1 || n === 2) {
        ctx.tween(cv, { opacity: 0, duration: 0.35, onComplete: () => {
          ctx.data.obj = I.spin3d(cv, n === 1 ? "cylinder" : "sphere");
          ctx.tween(cv, { opacity: 1, duration: 0.5 });
        } });
        const nm = ctx.$(".obj-name");
        nm.innerHTML = `<i>${names[n][0]}</i><span>${names[n][1]}</span>`;
        ctx.tween(nm, { scale: 0.8, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.6, ease: "back.out(2)" });
        ctx.sfx.whoosh(0.5);
      }
      if (n === 3) {
        const o = { d: 0 };
        ctx.tween(o, { d: 1, duration: 2, delay: 1, onUpdate: () => ctx.data.obj.setDepth(o.d) });
      }
    },
  });

  // 12 ────────────────────────────────────────────── MEMORIA
  S.push({
    id: "memoria", title: "Your memory lies too", hue: 330, transition: "dive",
    notes: [
      { en: "It's not only your eyes. Do you remember your fifth birthday perfectly? Spoiler: probably not. Memories are not saved like a video: your brain rebuilds them every time you remember them.",
        es: "No son solo los ojos. ¿Se acuerdan perfecto de su cumpleaños de cinco años? Spoiler: probablemente no. Los recuerdos no se guardan como un video: el cerebro los rearma cada vez que los recordás." },
      { en: "And every time it rebuilds them, they can change a little… and you don't even notice.",
        es: "Y cada vez que los rearma, pueden cambiar un poquito… y ni te das cuenta." },
      { en: "The psychologist Elizabeth Loftus did a famous experiment: about one in four people “remembered” getting lost in a shopping mall as a child… something that NEVER happened.",
        es: "La psicóloga Elizabeth Loftus hizo un experimento famoso: alrededor de una de cada cuatro personas “recordó” haberse perdido en un shopping de chico… algo que NUNCA pasó." },
    ],
    hold: [1, 2, 0],
    facts: [
      "Los recuerdos se REARMAN (reconstruyen) cada vez que los recordás → pueden cambiar.",
      "Elizabeth Loftus y Jacqueline Pickrell, 1995: ≈25% 'recordó' haberse perdido en un shopping de chico (falso).",
      "Loftus y Palmer, 1974: si preguntás a qué velocidad los autos 'se estrellaron', los testigos calculan más velocidad que con 'chocaron'.",
    ],
    html: () => `
      <div class="mem-layout">
        <div class="polaroid" data-in="slowmo" data-d=".4">
          <div class="mem-grid a"></div>
          <div class="mem-grid b"></div>
          <div class="pol-cap">Summer 2015 ☀️</div>
        </div>
        <div class="mem-text">
          <div class="kicker" data-in="fade">Memories</div>
          <h2 class="h-m" data-in="letters" data-d=".2">Your memory <span class="accent">lies</span> too</h2>
          <div class="pt" data-in="up" data-d="1"><i>🎞️</i><span>Not a video → <b>rebuilt</b> every time</span></div>
          <div class="pt" data-step="1" data-in="up"><i>🔀</i><span>Every rebuild can <b>change</b> it</span></div>
          <div class="card loftus" data-step="2" data-in="up">
            <div class="big-num accent">1 in 4</div>
            <div>“remembered” getting <b>lost in a mall</b> as a kid<br><span class="foot left">Elizabeth Loftus · 1995 · it never happened</span></div>
          </div>
        </div>
      </div>`,
    enter(ctx) {
      const build = (el, changed) => {
        let h = "";
        for (let r = 0; r < 3; r++) for (let c = 0; c < 4; c++) {
          h += `<div class="tile" style="left:${c * 25}%;top:${r * 33.333}%"><div class="tile-in" style="left:${-c * 100}%;top:${-r * 100}%">${memorySVG(changed)}</div></div>`;
        }
        el.innerHTML = h;
      };
      build(ctx.$(".mem-grid.a"), false);
      build(ctx.$(".mem-grid.b"), true);
      gsap.set(ctx.$(".mem-grid.b"), { opacity: 0 });
      ctx.tween(ctx.$$(".mem-grid.a .tile"), { x: () => (Math.random() - 0.5) * 900, y: () => (Math.random() - 0.5) * 700, rotation: () => (Math.random() - 0.5) * 120, opacity: 0 },
        { x: 0, y: 0, rotation: 0, opacity: 1, duration: 2.4, stagger: 0.07, delay: 0.5, ease: "expo.out" });
    },
    step(ctx, n) {
      if (n === 1) {
        const a = ctx.$$(".mem-grid.a .tile"), b = ctx.$$(".mem-grid.b .tile");
        ctx.tween(a, { x: () => (Math.random() - 0.5) * 900, y: () => (Math.random() - 0.5) * 700, rotation: () => (Math.random() - 0.5) * 140, opacity: 0, duration: 1, stagger: 0.04, ease: "power3.in" });
        gsap.set(ctx.$(".mem-grid.b"), { opacity: 1 });
        ctx.tween(b, { x: () => (Math.random() - 0.5) * 900, y: () => (Math.random() - 0.5) * 700, rotation: () => (Math.random() - 0.5) * 120, opacity: 0 },
          { x: 0, y: 0, rotation: 0, opacity: 1, duration: 2, stagger: 0.06, delay: 1.1, ease: "expo.out" });
        ctx.sfx.whoosh(0.8);
        ctx.after(1200, () => ctx.sfx.shimmer());
      }
    },
  });

  // 13 ────────────────────────────────────────────── EFECTO MANDELA
  S.push({
    id: "mandela", title: "The Mandela effect (vote)", hue: 270, transition: "glitch",
    notes: [
      { en: "Three quick questions. Vote with your hands! First: does Pikachu have a black tip on its tail?",
        es: "Tres preguntas rápidas. ¡Voten con la mano! Primera: ¿Pikachu tiene la punta de la cola negra?" },
      { en: "NO! Its tail is yellow, with a brown part at the bottom. It was never black. Second: does the Monopoly man wear a monocle?",
        es: "¡NO! Su cola es amarilla, con una parte marrón abajo. Nunca fue negra. Segunda: ¿el señor del Monopoly usa monóculo?" },
      { en: "NO! He never had a monocle. Third: does Darth Vader say “Luke, I am your father”?",
        es: "¡NO! Nunca tuvo monóculo. Tercera: ¿Darth Vader dice “Luke, yo soy tu padre”?" },
      { en: "NO! He says: “No, I am your father.” He never says “Luke”.",
        es: "¡NO! Dice: “No, yo soy tu padre”. Nunca dice “Luke”." },
      { en: "When lots of people remember the same thing wrong, it's called the Mandela effect. Many people “remembered” that Nelson Mandela died in prison in the 1980s… but he was freed in 1990 and became president of South Africa.",
        es: "Cuando muchísima gente recuerda lo mismo de forma equivocada, se llama efecto Mandela. Mucha gente “recordaba” que Nelson Mandela murió en la cárcel en los 80… pero lo liberaron en 1990 y llegó a presidente de Sudáfrica." },
    ],
    hold: [5, 5, 5, 1, 0],
    facts: [
      "El nombre lo inventó Fiona Broome (≈2009): mucha gente 'recordaba' que Mandela murió preso en los 80.",
      "Realidad: Mandela salió libre en 1990, fue presidente de Sudáfrica (1994–1999) y murió en 2013.",
      "Pikachu: cola amarilla con base marrón (las orejas sí tienen puntas negras). Monopoly: sin monóculo. Vader: “No, I am your father”.",
    ],
    html: () => `
      <div class="col center wrap">
        <div class="live-tag" data-in="pop">⚡ VOTE</div>
        <h2 class="h-l" data-in="letters" data-d=".2">The <span class="accent">Mandela</span> effect</h2>
        <div class="row mandela">
          <div class="card mq" data-in="up" data-d=".7"><div class="mq-ico">⚡</div><p>Pikachu’s tail: <b>black tip?</b></p>
            <div class="mq-a" data-step="1" data-in="stamp"><b>NO</b> · yellow + brown base</div></div>
          <div class="card mq" data-in="up" data-d=".9"><div class="mq-ico">🎩</div><p>Monopoly man: <b>monocle?</b></p>
            <div class="mq-a" data-step="2" data-in="stamp"><b>NO</b> · never</div></div>
          <div class="card mq" data-in="up" data-d="1.1"><div class="mq-ico">🎬</div><p>“<b>Luke</b>, I am your father”?</p>
            <div class="mq-a" data-step="3" data-in="stamp"><b>NO</b> · “No, I am your father”</div></div>
        </div>
        <p class="punch small" data-step="4" data-in="up">Many people · same <span class="accent">wrong</span> memory</p>
      </div>`,
    step(ctx, n) { if (n <= 3) ctx.sfx.wrong(); },
  });

  // 14 ────────────────────────────────────────────── POR QUÉ PASA
  S.push({
    id: "prediccion", title: "Why does this happen?", hue: 250, transition: "warp",
    notes: [
      { en: "So, why does the brain do all this? Look at this circuit: your senses send only a little information, and with that, your brain makes a prediction about the world.",
        es: "Entonces, ¿por qué el cerebro hace todo esto? Miren este circuito: los sentidos mandan poca información, y con eso el cerebro arma una predicción del mundo." },
      { en: "Your brain is not a camera: it's a prediction machine. It guesses, to be fast and to save energy.",
        es: "Tu cerebro no es una cámara: es una máquina de predicciones. Adivina, para ser rápido y ahorrar energía." },
      { en: "Most of the time it's right… that's why we're alive! But when it makes a mistake… you get an illusion. And today you saw nine of them.",
        es: "Casi siempre acierta… ¡por eso estamos vivos! Pero cuando se equivoca… aparece una ilusión. Y hoy vieron nueve." },
    ],
    hold: [1, 1, 0],
    facts: [
      "Neurociencia actual: 'procesamiento predictivo'. El cerebro predice y compara con lo que llega; procesa a fondo solo las diferencias.",
      "Resumen: contexto (Ebbinghaus), bordes (Café wall), células cansadas (bandera, lilac, espiral), contraste (pasos), atención (puntos amarillos), adivinar la profundidad (giro).",
    ],
    html: () => `
      <div class="col center wrap">
        <div class="kicker" data-in="fade">The explanation</div>
        <h2 class="h-l" data-in="letters" data-d=".2">Why does this happen?</h2>
        <div class="flow">
          <div class="node" data-in="pop" data-d=".8"><div class="n-ico">👁️</div><b>Senses</b><span>a little info</span></div>
          <div class="link" data-in="fade" data-d="1.1"><i></i><i></i><i></i></div>
          <div class="node hot" data-in="pop" data-d="1.3"><div class="n-ico">🧠</div><b>Prediction</b><span>fills the gaps</span></div>
          <div class="link" data-in="fade" data-d="1.6"><i></i><i></i><i></i></div>
          <div class="node" data-in="pop" data-d="1.8"><div class="n-ico">✨</div><b>What you “see”</b><span>your reality</span></div>
        </div>
        <p class="punch" data-step="1" data-in="letters">Not a camera → a <span class="accent">prediction machine</span></p>
        <p class="lead small" data-step="2" data-in="up">Almost always right · wrong = <b class="accent2">illusion</b></p>
      </div>`,
    enter(ctx) {
      ctx.$$(".link i").forEach((dot, i) => {
        ctx.tween(dot, { left: "0%", opacity: 0 }, { left: "100%", opacity: 1, duration: 1.4, repeat: -1, delay: 2 + (i % 3) * 0.45, ease: "none" });
      });
    },
  });

  // 15 ────────────────────────────────────────────── CIERRE
  S.push({
    id: "cierre", title: "Ending → Game", hue: 265, transition: "burst",
    notes: [
      { en: "So, next time you are sure about something you saw… remember: your brain is lying to you. Don't believe everything you see!",
        es: "Así que la próxima vez que estés seguro de algo que viste… acordate: tu cerebro te miente. ¡No creas todo lo que ves!" },
      { en: "Were you paying attention? Let's find out! (Press NEXT to open the game room. Share the link with the SHARE button, or ask them to scan the QR code.)",
        es: "¿Prestaron atención? ¡Vamos a comprobarlo! (Tocá SIGUIENTE para abrir la sala del juego. Pasá el enlace con COMPARTIR o que escaneen el QR)." },
    ],
    hold: [1, 0],
    facts: ["Al tocar SIGUIENTE se abre la sala del juego. Compartí el enlace con el botón 📲 del celular."],
    html: () => `
      <canvas class="fill brain-cv" width="1600" height="900"></canvas>
      <div class="col center wrap cierre">
        <h1 class="h-xl huge" data-in="letters" data-d=".4">DON’T BELIEVE</h1>
        <h1 class="h-xl huge accent" data-in="letters" data-d=".9">EVERYTHING YOU SEE</h1>
        <div class="game-cta" data-step="1" data-in="zoom">
          <div class="kicker">Were you paying attention?</div>
          <div class="cta-big">🎮 Let’s find out…</div>
        </div>
      </div>`,
    enter(ctx) {
      const b = I.brainParticles(ctx.$(".brain-cv"), { cx: 800, cy: 450, w: 900, step: ctx.lite ? 14 : 11, duration: 3.5 });
      ctx.raf((t) => b.frame(t));
      ctx.$(".brain-cv").style.opacity = 0.25;
      ctx.after(900, () => ctx.sfx.boom(0.7));
    },
  });

  window.SLIDES = S;
})();
