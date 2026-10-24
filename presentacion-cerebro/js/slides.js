// ============================================================
//  DIAPOSITIVAS — "TU CEREBRO TE MIENTE"
//
//  Cada diapositiva tiene:
//   id, title       -> nombre (se ve en el control remoto)
//   hue             -> color principal (0-360)
//   transition      -> dive | warp | sweep | glitch | burst | iris | rise
//   steps           -> cuántos toques de SIGUIENTE tiene antes de pasar
//   notes[]         -> lo que tenés que decir en cada paso (solo en tu celu)
//   html            -> contenido
//   enter / step / leave -> animaciones especiales
//
//  Atributos de animación en el HTML:
//   data-in="up|down|left|right|zoom|fade|letters|blur|pop|slowmo|stamp|flip|draw"
//   data-d="0.5"     -> retardo en segundos
//   data-step="1"    -> aparece recién en el paso 1, 2, ...
//   data-count="50"  -> número que cuenta hacia arriba
// ============================================================
(function () {
  const I = window.ILLUSIONS;

  const eyeSVG = `
<svg class="eye-svg" viewBox="0 0 1300 520">
  <defs>
    <radialGradient id="eyeG" cx="0.45" cy="0.45" r="0.6"><stop offset="0" stop-color="#1b1b2e"/><stop offset="1" stop-color="#0c0c16"/></radialGradient>
    <linearGradient id="ray" x1="0" x2="1"><stop offset="0" stop-color="#ffd84a"/><stop offset="1" stop-color="#22d3ee"/></linearGradient>
  </defs>
  <!-- árbol real -->
  <g data-in="pop" data-d=".5">
    <rect x="140" y="300" width="24" height="70" fill="#8b5a2b"/>
    <path d="M152 130 L232 300 L72 300 Z" fill="#34d27b"/>
    <text x="152" y="420" text-anchor="middle" class="svg-label">Lo que mirás</text>
  </g>
  <!-- ojo -->
  <g data-in="zoom" data-d=".8">
    <circle cx="760" cy="250" r="215" fill="url(#eyeG)" stroke="hsl(var(--h) 90% 66%)" stroke-width="5"/>
    <path d="M940 140 A 215 215 0 0 1 940 360" stroke="#ff5c8a" stroke-width="14" fill="none" stroke-linecap="round"/>
    <ellipse cx="575" cy="250" rx="26" ry="88" fill="#22d3ee" opacity=".55"/>
    <text x="960" y="470" text-anchor="middle" class="svg-label" fill="#ff5c8a">Retina</text>
    <text x="575" y="470" text-anchor="middle" class="svg-label">Cristalino</text>
  </g>
  <!-- rayos -->
  <g stroke="url(#ray)" stroke-width="4" fill="none">
    <path data-in="draw" data-d="1.4" d="M152 130 L575 250 L945 355"/>
    <path data-in="draw" data-d="1.7" d="M152 370 L575 250 L945 145"/>
  </g>
  <!-- imagen invertida en la retina -->
  <g data-in="fade" data-d="2.6" class="inverted">
    <rect x="918" y="166" width="16" height="48" fill="#8b5a2b"/>
    <path d="M926 345 L980 214 L872 214 Z" fill="#34d27b"/>
  </g>
</svg>`;

  const mullerSVG = `
<svg class="muller" viewBox="0 0 1200 520">
  <g class="ml-line" stroke-linecap="round">
    <line x1="300" y1="150" x2="900" y2="150" stroke="#fff" stroke-width="12"/>
    <g class="fins" stroke="#fff" stroke-width="12">
      <line x1="300" y1="150" x2="370" y2="80"/><line x1="300" y1="150" x2="370" y2="220"/>
      <line x1="900" y1="150" x2="830" y2="80"/><line x1="900" y1="150" x2="830" y2="220"/>
    </g>
    <text x="210" y="168" class="svg-big">A</text>
  </g>
  <g class="ml-line" stroke-linecap="round">
    <line x1="300" y1="380" x2="900" y2="380" stroke="#fff" stroke-width="12"/>
    <g class="fins" stroke="#fff" stroke-width="12">
      <line x1="300" y1="380" x2="230" y2="310"/><line x1="300" y1="380" x2="230" y2="450"/>
      <line x1="900" y1="380" x2="970" y2="310"/><line x1="900" y1="380" x2="970" y2="450"/>
    </g>
    <text x="130" y="398" class="svg-big">B</text>
  </g>
  <g class="guides" opacity="0">
    <line x1="300" y1="40" x2="300" y2="490" stroke="#22d3ee" stroke-width="4" stroke-dasharray="14 12"/>
    <line x1="900" y1="40" x2="900" y2="490" stroke="#22d3ee" stroke-width="4" stroke-dasharray="14 12"/>
    <line class="hl" x1="300" y1="150" x2="900" y2="150" stroke="#22d3ee" stroke-width="14" stroke-linecap="round"/>
    <line class="hl" x1="300" y1="380" x2="900" y2="380" stroke="#22d3ee" stroke-width="14" stroke-linecap="round"/>
  </g>
</svg>`;

  const dressSVG = (body, lace, cls = "") => `
<svg class="dress ${cls}" viewBox="0 0 300 520">
  <defs><clipPath id="dc-${cls}"><path d="M110 20 Q150 40 190 20 L205 120 Q210 150 196 175 L270 500 Q150 530 30 500 L104 175 Q90 150 95 120 Z"/></clipPath></defs>
  <g clip-path="url(#dc-${cls})">
    <rect width="300" height="520" fill="${body}"/>
    <rect y="0" width="300" height="34" fill="${lace}"/>
    <rect y="165" width="300" height="36" fill="${lace}"/>
    <rect y="290" width="300" height="34" fill="${lace}"/>
    <rect y="420" width="300" height="34" fill="${lace}"/>
  </g>
  <path d="M110 20 Q150 40 190 20 L205 120 Q210 150 196 175 L270 500 Q150 530 30 500 L104 175 Q90 150 95 120 Z" fill="none" stroke="rgba(255,255,255,.25)" stroke-width="3"/>
</svg>`;

  const outletSVG = `
<svg viewBox="0 0 260 260" class="obj">
  <rect x="20" y="20" width="220" height="220" rx="34" fill="#ecebe6"/>
  <circle cx="130" cy="130" r="82" fill="#d9d7cf"/>
  <rect x="78" y="88" width="16" height="44" rx="6" fill="#222" transform="rotate(-30 86 110)"/>
  <rect x="166" y="88" width="16" height="44" rx="6" fill="#222" transform="rotate(30 174 110)"/>
  <rect x="122" y="150" width="16" height="44" rx="6" fill="#222"/>
  <g class="face-hl" opacity="0" fill="none" stroke="#ffe14d" stroke-width="6">
    <circle cx="86" cy="110" r="34"/><circle cx="174" cy="110" r="34"/><ellipse cx="130" cy="172" rx="30" ry="36"/>
  </g>
</svg>`;
  const houseSVG = `
<svg viewBox="0 0 260 260" class="obj">
  <path d="M20 118 L130 34 L240 118 Z" fill="#c2453b"/>
  <rect x="44" y="112" width="172" height="128" fill="#f2d3a1"/>
  <rect x="66" y="132" width="44" height="44" fill="#2b2b33"/>
  <rect x="150" y="132" width="44" height="44" fill="#2b2b33"/>
  <rect x="108" y="190" width="44" height="50" rx="8" fill="#7b4a2b"/>
  <g class="face-hl" opacity="0" fill="none" stroke="#ffe14d" stroke-width="6">
    <circle cx="88" cy="154" r="32"/><circle cx="172" cy="154" r="32"/><ellipse cx="130" cy="214" rx="34" ry="30"/>
  </g>
</svg>`;
  const carSVG = `
<svg viewBox="0 0 260 260" class="obj">
  <path d="M40 120 Q50 70 90 64 L170 64 Q210 70 220 120 Z" fill="#3b82f6"/>
  <rect x="24" y="116" width="212" height="88" rx="26" fill="#2563eb"/>
  <path d="M70 76 L190 76 L206 116 L54 116 Z" fill="#bfe6ff"/>
  <circle cx="70" cy="150" r="22" fill="#fff8c4"/><circle cx="190" cy="150" r="22" fill="#fff8c4"/>
  <path d="M90 180 Q130 205 170 180" stroke="#111" stroke-width="10" fill="none" stroke-linecap="round"/>
  <rect x="36" y="200" width="36" height="30" rx="8" fill="#111"/><rect x="188" y="200" width="36" height="30" rx="8" fill="#111"/>
  <g class="face-hl" opacity="0" fill="none" stroke="#ffe14d" stroke-width="6">
    <circle cx="70" cy="150" r="34"/><circle cx="190" cy="150" r="34"/><ellipse cx="130" cy="188" rx="52" ry="22"/>
  </g>
</svg>`;

  const marsSVG = (face) => `
<svg viewBox="0 0 520 380" class="mars">
  <defs>
    <filter id="grain-${face}"><feTurbulence type="fractalNoise" baseFrequency="${face ? 0.9 : 1.6}" numOctaves="2" seed="4"/><feColorMatrix values="0 0 0 0 .55  0 0 0 0 .5  0 0 0 0 .45  0 0 0 ${face ? 0.55 : 0.35} 0"/></filter>
    <filter id="soft-${face}"><feGaussianBlur stdDeviation="${face ? 7 : 2.2}"/></filter>
    <radialGradient id="mesa-${face}" cx="0.35" cy="0.4" r="0.7"><stop offset="0" stop-color="#d9c7a8"/><stop offset="1" stop-color="#6b5a45"/></radialGradient>
  </defs>
  <rect width="520" height="380" fill="${face ? "#2b2622" : "#9a8466"}"/>
  <g filter="url(#soft-${face})">
    ${face ? `
      <ellipse cx="260" cy="190" rx="130" ry="160" fill="url(#mesa-${face})"/>
      <ellipse cx="208" cy="150" rx="34" ry="20" fill="#1d1915"/>
      <ellipse cx="312" cy="146" rx="34" ry="20" fill="#2a241e"/>
      <path d="M255 165 L245 235 L275 235 Z" fill="#40362c"/>
      <ellipse cx="262" cy="270" rx="52" ry="12" fill="#221d18"/>
      <ellipse cx="380" cy="190" rx="34" ry="150" fill="#1a1612" opacity=".7"/>
    ` : `
      <path d="M120 300 Q140 120 230 80 Q330 60 380 150 Q420 230 400 310 Q260 340 120 300 Z" fill="#b39c7c"/>
      <path d="M150 300 Q250 250 395 300" stroke="#7d684f" stroke-width="14" fill="none" opacity=".45"/>
      <ellipse cx="300" cy="190" rx="40" ry="26" fill="#a38c6c" opacity=".55"/>
      <ellipse cx="215" cy="230" rx="30" ry="16" fill="#a38c6c" opacity=".45"/>
    `}
  </g>
  <rect width="520" height="380" filter="url(#grain-${face})"/>
</svg>`;

  // escena de la foto que "se reconstruye" (memoria)
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

  const S = [];

  // 1 ─────────────────────────────────────────────── PORTADA
  S.push({
    id: "portada", title: "Portada", hue: 265, transition: "burst", steps: 0,
    notes: ["Saludá y presentate. Preguntá: «¿Quién cree que lo que ve es la realidad tal cual es? Levanten la mano». Después: «Hoy les voy a demostrar que su cerebro les miente… todo el tiempo»."],
    html: (cfg) => `
      <canvas class="fill brain-cv" width="1600" height="900"></canvas>
      <div class="portada">
        <div class="kicker" data-in="fade" data-d="1.4">${cfg.materia ? cfg.materia + " · " : ""}Exposición</div>
        <h1 class="h-xl" data-in="letters" data-d="1.8">TU CEREBRO</h1>
        <h1 class="h-xl accent glitch" data-text="TE MIENTE" data-in="letters" data-d="2.3">TE MIENTE</h1>
        <p class="lead" data-in="up" data-d="3.1">Ilusiones, trucos y por qué no podés confiar en tus propios ojos</p>
        <div class="presenter" data-in="fade" data-d="3.7">Presenta <b>${cfg.presentador}</b></div>
      </div>`,
    enter(ctx) {
      const cv = ctx.$(".brain-cv");
      const b = I.brainParticles(cv, { cx: 800, cy: 225, w: ctx.lite ? 380 : 430, step: ctx.lite ? 9 : 7 });
      ctx.raf((t) => b.frame(t));
      ctx.after(3300, () => ctx.$(".glitch").classList.add("on"));
      ctx.after(1500, () => ctx.sfx.boom(0.6));
    },
  });

  // 2 ─────────────────────────────────────────────── LO QUE VES NO ES LA REALIDAD
  S.push({
    id: "realidad", title: "Lo que ves no es la realidad", hue: 200, transition: "dive", steps: 1,
    notes: [
      "«Por segundo, tus ojos, oídos y piel le mandan al cerebro unos 11 millones de bits de información. ¿Saben cuánto procesa tu mente consciente? Unos 50». Dejá que miren los números.",
      "«¿Y el resto? Lo completa tu cerebro. Lo que ves es una mezcla de lo que llega… y de lo que tu cerebro inventa».",
    ],
    html: () => `
      <div class="col center wrap">
        <div class="kicker" data-in="fade">Dato 01</div>
        <h2 class="h-l" data-in="letters" data-d=".2">Lo que ves no es la realidad</h2>
        <div class="row stats">
          <div class="card stat" data-in="left" data-d=".9">
            <div class="stat-label">Tus sentidos envían</div>
            <div class="big-num" data-count="11000000">0</div>
            <div class="stat-unit">bits por segundo</div>
            <div class="dots-field"></div>
          </div>
          <div class="vs" data-in="zoom" data-d="1.3">VS</div>
          <div class="card stat" data-in="right" data-d="1.1">
            <div class="stat-label">Tu mente consciente procesa</div>
            <div class="big-num accent" data-count="50">0</div>
            <div class="stat-unit">bits por segundo</div>
            <div class="dots-one"><i></i></div>
          </div>
        </div>
        <p class="punch" data-step="1" data-in="letters">El resto… lo <span class="accent">inventa</span> tu cerebro.</p>
        <p class="foot" data-in="fade" data-d="2.4">Valores aproximados · estimación clásica de la teoría de la información</p>
      </div>`,
    enter(ctx) {
      const f = ctx.$(".dots-field");
      let h = "";
      for (let i = 0; i < 260; i++) h += `<i style="animation-delay:${(Math.random() * 2).toFixed(2)}s"></i>`;
      f.innerHTML = h;
    },
  });

  // 3 ─────────────────────────────────────────────── ENERGÍA
  S.push({
    id: "energia", title: "Tu cerebro es un glotón", hue: 320, transition: "warp", steps: 1,
    notes: [
      "«El cerebro pesa más o menos el 2% de tu cuerpo… pero se come cerca del 20% de toda tu energía». Preguntá: «¿Por qué creen que gasta tanto?».",
      "«Como gasta tanto, ahorra: en vez de analizar todo, toma atajos y PREDICE. Y esos atajos son los que vamos a hackear hoy».",
    ],
    html: () => `
      <div class="col center wrap">
        <div class="kicker" data-in="fade">Dato 02</div>
        <h2 class="h-l" data-in="letters" data-d=".2">Tu cerebro es un glotón</h2>
        <div class="row rings">
          <div class="ring-box" data-in="pop" data-d=".8">
            <svg viewBox="0 0 300 300" class="ring"><circle cx="150" cy="150" r="120" class="ring-bg"/><circle cx="150" cy="150" r="120" class="ring-fg" data-p="0.02"/></svg>
            <div class="ring-val"><span data-count="2">0</span>%</div>
            <div class="ring-label">de tu <b>peso</b></div>
          </div>
          <div class="ring-box" data-in="pop" data-d="1.1">
            <svg viewBox="0 0 300 300" class="ring"><circle cx="150" cy="150" r="120" class="ring-bg"/><circle cx="150" cy="150" r="120" class="ring-fg hot" data-p="0.2"/></svg>
            <div class="ring-val accent"><span data-count="20">0</span>%</div>
            <div class="ring-label">de tu <b>energía</b></div>
          </div>
        </div>
        <p class="punch" data-step="1" data-in="up">Por eso toma <span class="accent">atajos</span>: en vez de mirar todo… <b class="accent2">PREDICE</b>.</p>
      </div>`,
    enter(ctx) {
      ctx.$$(".ring-fg").forEach((c, i) => {
        const C = 2 * Math.PI * 120;
        gsap.set(c, { strokeDasharray: C, strokeDashoffset: C });
        ctx.tween(c, { strokeDashoffset: C * (1 - parseFloat(c.dataset.p)), duration: 2.2, delay: 1.1 + i * 0.3, ease: "expo.out" });
      });
    },
  });

  // 4 ─────────────────────────────────────────────── IMAGEN INVERTIDA
  S.push({
    id: "invertida", title: "La imagen llega al revés", hue: 190, transition: "sweep", steps: 1,
    notes: [
      "«La luz entra por el cristalino, los rayos se cruzan… y la imagen llega a la retina DADA VUELTA». Mostrá el árbol cabeza abajo.",
      "«Ustedes nunca ven nada al revés porque el cerebro la da vuelta automáticamente. Ya es la primera mentira: está editando la imagen»."
    ],
    html: () => `
      <div class="col wrap">
        <div class="kicker" data-in="fade">Cómo vemos</div>
        <h2 class="h-l" data-in="letters" data-d=".2">La imagen llega <span class="accent flip-word">al revés</span></h2>
        ${eyeSVG}
        <div class="flip-note" data-step="1" data-in="right">
          <span class="brain-ico">🧠</span>
          <div>…y tu cerebro <b class="accent">la da vuelta</b><br>sin que te des cuenta</div>
        </div>
      </div>`,
    step(ctx, n) {
      if (n === 1) {
        ctx.tween(ctx.$(".inverted"), { rotation: 180, svgOrigin: "926 255", duration: 1.6, ease: "expo.inOut", delay: 0.2 });
        ctx.sfx.shimmer();
      }
    },
  });

  // 5 ─────────────────────────────────────────────── PUNTO CIEGO
  S.push({
    id: "punto-ciego", title: "⚡ El punto ciego", hue: 0, transition: "iris", steps: 2,
    notes: [
      "«Todos tienen un agujero en la vista… y nunca se dieron cuenta. Hagamos la prueba todos juntos».",
      "Leé las instrucciones en voz alta: «Tápense el ojo IZQUIERDO. Con el derecho miren fijo la cruz. Ahora acérquense o aléjense de a poco, o muevan la cabeza… en algún momento el punto rojo DESAPARECE». Dales 30-40 segundos.",
      "«Ahí sale el nervio óptico del ojo: en ese lugar no hay células que detecten luz. Pero no ven un agujero negro: el cerebro lo rellena con lo que hay alrededor»."
    ],
    html: () => `
      <div class="col center wrap">
        <div class="live-tag" data-in="pop">⚡ PRUEBA EN VIVO</div>
        <h2 class="h-l" data-in="letters" data-d=".2">Tenés un <span class="accent">agujero</span> en la vista</h2>
        <p class="lead" data-in="up" data-d="1">Y nunca lo notaste. Hagamos la prueba.</p>
      </div>
      <div class="bs-panel">
        <div class="bs-instr">
          <span>1 · Tapate el ojo <b>IZQUIERDO</b></span>
          <span>2 · Mirá fijo la <b>✚</b> con el ojo derecho</span>
          <span>3 · Acercate o alejate <b>despacio</b></span>
        </div>
        <div class="bs-cross">✚</div>
        <div class="bs-dot"></div>
        <div class="bs-explain">
          <b>¡Desapareció!</b> Ahí sale el nervio óptico: no hay receptores de luz.<br>
          Tu cerebro <b>rellena el hueco</b> con lo que hay alrededor.
        </div>
      </div>`,
    step(ctx, n) {
      if (n === 1) {
        const p = ctx.$(".bs-panel");
        gsap.set(p, { display: "block" });
        ctx.bodyClass("no-vignette");
        ctx.tween(p, { clipPath: "circle(0% at 50% 50%)" }, { clipPath: "circle(120% at 50% 50%)", duration: 1.4, ease: "expo.inOut" });
        ctx.tween(ctx.$$(".bs-instr span"), { opacity: 0, y: -20 }, { opacity: 1, y: 0, stagger: 0.25, delay: 1, duration: 0.8 });
      }
      if (n === 2) {
        ctx.tween(ctx.$(".bs-explain"), { opacity: 0, y: 40 }, { opacity: 1, y: 0, duration: 1, ease: "expo.out" });
        ctx.sfx.shimmer();
      }
    },
  });

  // 6 ─────────────────────────────────────────────── MÜLLER-LYER
  S.push({
    id: "muller", title: "⚡ ¿Cuál línea es más larga?", hue: 285, transition: "glitch", steps: 2,
    notes: [
      "Preguntá: «¿Cuál es más larga, la A o la B?». Hacé votar a mano alzada: «Los que dicen A… los que dicen B…».",
      "«¿Seguros? Miren…». (Se borran las flechas y aparecen las guías).",
      "«¡Son EXACTAMENTE iguales! Las flechitas engañan al cerebro, que interpreta profundidad, como esquinas de una pared». Ilusión de Müller-Lyer (1889)."
    ],
    html: () => `
      <div class="col center wrap">
        <div class="live-tag" data-in="pop">⚡ VOTACIÓN</div>
        <h2 class="h-m" data-in="letters" data-d=".2">¿Cuál línea es más larga?</h2>
        <div data-in="zoom" data-d=".7" class="ml-wrap">${mullerSVG}</div>
        <div class="vote-row" data-in="up" data-d="1.2"><span class="chip">✋ A</span><span class="chip">✋ B</span><span class="chip">✋ Iguales</span></div>
        <div class="stamp" data-step="2" data-in="stamp">¡SON IGUALES!</div>
        <p class="foot" data-step="2" data-in="fade" data-d=".6">Ilusión de Müller-Lyer · 1889</p>
      </div>`,
    step(ctx, n) {
      if (n === 1) {
        ctx.tween(ctx.$$(".fins"), { opacity: 0.12, duration: 1.4, ease: "power2.inOut" });
        ctx.tween(ctx.$(".guides"), { opacity: 1, duration: 1, delay: 0.9 });
        ctx.tween(ctx.$$(".hl"), { strokeDasharray: 600, strokeDashoffset: 600 }, { strokeDashoffset: 0, duration: 1.3, delay: 1.1, ease: "expo.out" });
        ctx.tween(ctx.$(".vote-row"), { opacity: 0, y: 20, duration: 0.5 });
        ctx.sfx.whoosh(0.6);
      }
    },
  });

  // 7 ─────────────────────────────────────────────── ADELSON
  S.push({
    id: "adelson", title: "⚡ El tablero de Adelson", hue: 160, transition: "dive", steps: 2,
    notes: [
      "«¿Cuál casilla es más oscura, la A o la B?». Votación. Casi todos van a decir que la A es más oscura.",
      "«Voy a unir las dos casillas con una franja del mismo color…». ¡Son el mismo gris!",
      "«Ahora tapo todo lo demás… ¿Ven? Idénticas. Tu cerebro sabe que las sombras oscurecen, así que ACLARA lo que cree que está en sombra. No te muestra el color real: te muestra lo que cree que es». Creado por Edward Adelson, MIT, 1995."
    ],
    html: () => `
      <div class="adelson-layout">
        <div class="adelson-stage" data-in="slowmo" data-d=".3">
          <canvas class="adelson-cv" width="1000" height="820"></canvas>
          <canvas class="adelson-fx" width="1000" height="820"></canvas>
        </div>
        <div class="adelson-text">
          <div class="live-tag" data-in="pop" data-d=".4">⚡ VOTACIÓN</div>
          <h2 class="h-m" data-in="letters" data-d=".6">¿Cuál es más oscura?</h2>
          <div class="vote-row left" data-in="up" data-d="1.3"><span class="chip">✋ A</span><span class="chip">✋ B</span></div>
          <div class="reveal-box" data-step="1" data-in="up">Son <b class="accent">EXACTAMENTE</b><br>el mismo gris.</div>
          <p class="lead small" data-step="2" data-in="up">Tu cerebro <b>aclara</b> lo que cree que está en sombra.</p>
          <p class="foot left" data-step="2" data-in="fade" data-d=".5">Edward H. Adelson · MIT · 1995</p>
        </div>
      </div>`,
    enter(ctx) {
      ctx.data.info = I.adelson(ctx.$(".adelson-cv"));
    },
    step(ctx, n) {
      const fx = ctx.$(".adelson-fx");
      const g = fx.getContext("2d");
      const info = ctx.data.info;
      const gray = `rgb(${info.gray},${info.gray},${info.gray})`;
      if (n === 1) {
        // franja del mismo gris uniendo A y B (se dibuja animada)
        const st = { k: 0 };
        ctx.tween(st, { k: 1, duration: 1.4, ease: "expo.inOut", onUpdate() {
          g.clearRect(0, 0, fx.width, fx.height);
          g.strokeStyle = gray; g.lineWidth = 34; g.lineCap = "round";
          const [ax, ay] = info.A, [bx, by] = info.B;
          g.beginPath(); g.moveTo(ax, ay + 14); g.lineTo(ax + (bx - ax) * st.k, ay + 14 + (by - ay) * st.k); g.stroke();
        } });
        ctx.sfx.whoosh(0.5);
        ctx.after(1500, () => ctx.sfx.reveal());
      }
      if (n === 2) {
        // se apaga todo el tablero y quedan solo las casillas A y B
        g.clearRect(0, 0, fx.width, fx.height);
        g.fillStyle = gray;
        [info.squareA, info.squareB].forEach((sq) => {
          g.beginPath(); g.moveTo(...sq[0]); sq.slice(1).forEach((p) => g.lineTo(...p)); g.closePath(); g.fill();
        });
        g.font = "700 46px 'Space Grotesk', Arial";
        g.fillStyle = "#fff"; g.textAlign = "center";
        g.fillText("A", info.A[0], info.A[1] - 70);
        g.fillText("B", info.B[0], info.B[1] - 70);
        ctx.tween(ctx.$(".adelson-cv"), { opacity: 0, duration: 1.8, ease: "power2.inOut" });
        ctx.sfx.boom(0.4);
      }
    },
  });

  // 8 ─────────────────────────────────────────────── EL VESTIDO
  S.push({
    id: "vestido", title: "⚡ El vestido (2015)", hue: 220, transition: "warp", steps: 2,
    notes: [
      "«En 2015 una foto de un vestido dividió a todo internet». Votación: «¿Quiénes lo ven azul y negro? ¿Y blanco y dorado?». (El dibujo imita los colores de la foto original).",
      "«El vestido real era… AZUL Y NEGRO»",
      "«¿Por qué la gente veía colores distintos? La foto tenía una luz rara. Si tu cerebro supone que hay luz amarillenta, la “resta” y lo ves azul y negro. Si supone que está en sombra azulada, lo ves blanco y dorado. ¡El mismo píxel, dos cerebros, dos colores!»"
    ],
    html: () => `
      <div class="col center wrap">
        <div class="live-tag" data-in="pop">⚡ VOTACIÓN</div>
        <h2 class="h-m" data-in="letters" data-d=".2">El vestido que dividió internet</h2>
        <div class="row dresses">
          <div class="dress-box" data-in="slowmo" data-d=".6">
            ${dressSVG("#8f97c8", "#7a6540", "photo")}
            <div class="dress-cap">Colores de la foto · 2015</div>
          </div>
          <div class="dress-box real" data-step="1" data-in="flip">
            ${dressSVG("#1e3a9a", "#0b0b10", "real")}
            <div class="dress-cap big">Era <b class="accent">AZUL y NEGRO</b></div>
          </div>
        </div>
        <div class="vote-row" data-in="up" data-d="1.4"><span class="chip">💙🖤 Azul y negro</span><span class="chip">🤍💛 Blanco y dorado</span></div>
        <div class="row lights" data-step="2" data-in="up">
          <div class="light-card"><span class="sun">💡</span> ¿Tu cerebro supone <b>luz amarilla</b>? → lo ves <b>azul y negro</b></div>
          <div class="light-card"><span class="sun">🌥️</span> ¿Supone <b>sombra azulada</b>? → lo ves <b>blanco y dorado</b></div>
        </div>
      </div>`,
    step(ctx, n) {
      if (n === 1) { ctx.after(900, () => ctx.sfx.reveal()); ctx.tween(ctx.$(".vote-row"), { opacity: 0, duration: 0.4 }); }
    },
  });

  // 9 ─────────────────────────────────────────────── SERPIENTES
  S.push({
    id: "serpientes", title: "Imágenes que se mueven solas", hue: 60, transition: "burst", steps: 1,
    notes: [
      "No digas nada al principio. Dejá que la miren 5 segundos. Preguntá: «¿Qué ven?». Van a decir que gira.",
      "«Esta imagen está 100% quieta, es un dibujo. El movimiento lo crea tu cerebro por cómo procesa los contrastes de colores cuando movés los ojos. Si mirás fijo un solo círculo, ese se frena». Inspirada en las “Serpientes giratorias” de Akiyoshi Kitaoka."
    ],
    html: () => `
      <canvas class="fill snakes-cv" width="1600" height="900" data-in="slowmo"></canvas>
      <div class="snake-banner" data-in="up" data-d="1.4">Nada se mueve. <b>Lo juro.</b></div>
      <div class="snake-badge" data-step="1" data-in="pop">📷 Imagen 100% quieta · el movimiento lo crea tu cerebro<br><small>Inspirada en “Rotating Snakes” de Akiyoshi Kitaoka</small></div>`,
    enter(ctx) { I.snakes(ctx.$(".snakes-cv")); },
  });

  // 10 ────────────────────────────────────────────── POSTIMAGEN
  S.push({
    id: "postimagen", title: "⚡ Mirá el punto 20 segundos", hue: 30, transition: "iris", steps: 2,
    notes: [
      "«Ahora necesito que todos miren FIJO el punto negro del centro, sin mover los ojos, durante 20 segundos. Cuando la pantalla se ponga blanca, sigan mirando el punto». Tocá SIGUIENTE para arrancar la cuenta.",
      "Silencio durante la cuenta. Cuando se ponga blanca: «¿Qué vieron?». Van a ver la bandera argentina con sus colores reales.",
      "«Las células del ojo que detectan colores se CANSAN si miran mucho el mismo color. Cuando mirás blanco, muestran el color opuesto. Por eso apareció la bandera celeste y blanca, que nunca estuvo en la pantalla»."
    ],
    html: () => `
      <div class="col center wrap ai-intro">
        <div class="live-tag" data-in="pop">⚡ PRUEBA EN VIVO</div>
        <h2 class="h-m" data-in="letters" data-d=".2">Mirá fijo el punto <span class="accent">20 segundos</span></h2>
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
      <div class="white-screen"><div class="fix-dot"></div><div class="ws-q">¿La ves? 👀</div>
        <div class="ws-explain">Las células de tu ojo se <b>cansaron</b> de esos colores y ahora muestran los <b>opuestos</b>.<br>La bandera celeste y blanca <b>nunca estuvo</b> en la pantalla.</div>
      </div>`,
    step(ctx, n) {
      const ws = ctx.$(".white-screen");
      const goWhite = () => {
        if (ctx.data.white) return;
        ctx.data.white = true;
        gsap.set(ws, { display: "flex", opacity: 1 });
        ctx.bodyClass("no-vignette");
        ctx.sfx.boom(0.35);
        ctx.tween(ctx.$(".ws-q"), { opacity: 0 }, { opacity: 1, delay: 5, duration: 1 });
      };
      if (n === 1) {
        let s = 20;
        const span = ctx.$(".countdown span");
        ctx.tween(ctx.$(".countdown"), { opacity: 0, scale: 0.6 }, { opacity: 1, scale: 1, duration: 0.6, ease: "back.out(2)" });
        ctx.every(1000, () => {
          s--;
          if (s >= 0) {
            span.textContent = s;
            ctx.sfx.tick(s <= 3);
          }
          if (s === 0) ctx.after(400, goWhite);
        });
      }
      if (n === 2) {
        goWhite();
        ctx.tween(ctx.$(".ws-q"), { opacity: 0, duration: 0.3 });
        ctx.tween(ctx.$(".ws-explain"), { opacity: 0, y: 40 }, { opacity: 1, y: 0, duration: 1, ease: "expo.out" });
      }
    },
  });

  // 11 ────────────────────────────────────────────── STROOP
  const STROOP_COLS = { ROJO: "#ff3b3b", AZUL: "#3b82f6", VERDE: "#22c55e", AMARILLO: "#facc15", VIOLETA: "#a855f7", NARANJA: "#fb923c" };
  const stroopGrid = (mismatch) => {
    const names = Object.keys(STROOP_COLS);
    const r = I.rng(mismatch ? 5 : 3);
    let out = "";
    let prev = "";
    for (let i = 0; i < 12; i++) {
      let w = names[Math.floor(r() * names.length)];
      while (w === prev) w = names[Math.floor(r() * names.length)];
      prev = w;
      let c = w;
      if (mismatch) while (c === w) c = names[Math.floor(r() * names.length)];
      out += `<span style="color:${STROOP_COLS[c]}">${w}</span>`;
    }
    return out;
  };
  S.push({
    id: "stroop", title: "⚡ Decí el COLOR, no la palabra", hue: 0, transition: "sweep", steps: 3,
    notes: [
      "«Juego rápido: van a ver palabras de colores. Tienen que decir EN VOZ ALTA el COLOR de la letra, NO lo que dice la palabra. Todos juntos»",
      "Ronda 1 (fácil): coinciden palabra y color. Que lo digan rápido en grupo.",
      "Ronda 2 (difícil): ahora no coinciden. Van a trabarse y reírse. Animalos: «¡Más rápido!».",
      "«¿Por qué cuesta tanto? Porque leer es AUTOMÁTICO: tu cerebro no puede “no leer”. Las dos señales chocan. Se llama Efecto Stroop, descubierto en 1935»."
    ],
    html: () => `
      <div class="col center wrap">
        <div class="live-tag" data-in="pop">⚡ JUEGO EN VIVO</div>
        <h2 class="h-m" data-in="letters" data-d=".2">Decí el <span class="accent">COLOR</span>, no la palabra</h2>
        <div class="stroop-area">
          <div class="stroop r1"><div class="round-lbl">Ronda 1 · Fácil 😎</div><div class="sg">${stroopGrid(false)}</div></div>
          <div class="stroop r2"><div class="round-lbl">Ronda 2 · Difícil 😈</div><div class="sg">${stroopGrid(true)}</div></div>
          <div class="stroop r3">
            <div class="reveal-box">Leer es <b class="accent">automático</b>:<br>tu cerebro no puede “no leer”.</div>
            <p class="foot">Efecto Stroop · John Ridley Stroop · 1935</p>
          </div>
        </div>
      </div>`,
    step(ctx, n) {
      const show = (sel) => {
        const el = ctx.$(sel);
        gsap.set(el, { display: "flex" });
        const items = el.querySelectorAll(".sg span");
        ctx.tween(el, { opacity: 0 }, { opacity: 1, duration: 0.4 });
        if (items.length) ctx.tween(items, { opacity: 0, scale: 0.4, y: 30 }, { opacity: 1, scale: 1, y: 0, stagger: 0.06, duration: 0.6, ease: "back.out(2)" });
        ctx.sfx.pop();
      };
      const hide = (sel) => ctx.tween(ctx.$(sel), { opacity: 0, scale: 0.9, duration: 0.4, onComplete: () => gsap.set(ctx.$(sel), { display: "none" }) });
      if (n === 1) show(".r1");
      if (n === 2) { hide(".r1"); ctx.after(420, () => { show(".r2"); ctx.sfx.glitch(); }); }
      if (n === 3) { hide(".r2"); ctx.after(420, () => { show(".r3"); ctx.sfx.reveal(); }); }
    },
  });

  // 12 ────────────────────────────────────────────── PAREIDOLIA
  S.push({
    id: "pareidolia", title: "Pareidolia: caras en todos lados", hue: 45, transition: "dive", steps: 1,
    notes: [
      "«¿Qué ven acá? Un enchufe, una casa, un auto… ¿o caras?». Que digan qué emoción tiene cada una (el enchufe está sorprendido, el auto contento).",
      "«Esto se llama PAREIDOLIA: tu cerebro está programado para encontrar caras, porque reconocer rápido una cara era clave para sobrevivir. Prefiere equivocarse viendo una cara que no está… antes que no ver una que sí está»."
    ],
    html: () => `
      <div class="col center wrap">
        <div class="kicker" data-in="fade">Detector de caras</div>
        <h2 class="h-l" data-in="letters" data-d=".2">¿Ves caras?</h2>
        <div class="row objs">
          <div class="obj-card" data-in="up" data-d=".7">${outletSVG}<span>Un enchufe</span></div>
          <div class="obj-card" data-in="up" data-d=".9">${houseSVG}<span>Una casa</span></div>
          <div class="obj-card" data-in="up" data-d="1.1">${carSVG}<span>Un auto</span></div>
        </div>
        <p class="punch" data-step="1" data-in="up">Se llama <span class="accent">PAREIDOLIA</span>: tu cerebro busca caras en todo.</p>
      </div>`,
    step(ctx, n) {
      if (n === 1) {
        ctx.tween(ctx.$$(".face-hl"), { opacity: 0 }, { opacity: 1, duration: 0.6, stagger: 0.2 });
        ctx.tween(ctx.$$(".obj-card"), { y: -10, scale: 1.04, duration: 0.6, stagger: 0.2, ease: "back.out(2)" });
        ctx.sfx.shimmer();
      }
    },
  });

  // 13 ────────────────────────────────────────────── CARA DE MARTE
  S.push({
    id: "marte", title: "La Cara de Marte", hue: 15, transition: "warp", steps: 1,
    notes: [
      "«En 1976 la sonda Viking 1 de la NASA sacó esta foto de Marte. ¡Parecía una cara gigante! Se armaron teorías de extraterrestres, ruinas, de todo».",
      "«Años después, con cámaras mucho mejores, se fotografió el mismo lugar: era solo una montaña. La cara la había puesto tu cerebro»."
    ],
    html: () => `
      <div class="col center wrap">
        <div class="kicker" data-in="fade">Caso real · NASA</div>
        <h2 class="h-l" data-in="letters" data-d=".2">La “Cara de Marte”</h2>
        <div class="row mars-row">
          <figure class="mars-fig" data-in="slowmo" data-d=".7">${marsSVG(true)}<figcaption><b>1976</b> · Sonda Viking 1 <span class="tagx">baja resolución</span></figcaption></figure>
          <figure class="mars-fig" data-step="1" data-in="flip">${marsSVG(false)}<figcaption><b>Años después</b> · Mejores cámaras <span class="tagx ok">alta resolución</span></figcaption></figure>
        </div>
        <p class="punch small" data-step="1" data-in="up" data-d=".8">Era solo una <b>montaña</b>. La cara… la puso tu cerebro.</p>
      </div>`,
  });

  // 14 ────────────────────────────────────────────── GORILA
  S.push({
    id: "gorila", title: "⚡ Desafío de atención", hue: 140, transition: "glitch", steps: 4,
    notes: [
      "«Desafío: cuenten EN SILENCIO cuántas veces se pasa la pelota el equipo de remera BLANCA. Solo los blancos. Concéntrense». Tocá SIGUIENTE para arrancar.",
      "Dejá correr la animación (22 segundos). No digas nada. Cuando termine, preguntá: «¿Cuántos pases contaron?» y escuchá respuestas.",
      "«¡Fueron 12!». Felicitá a los que acertaron.",
      "«Ahora la pregunta importante… ¿alguien vio al GORILA?». Repetición rápida con el reflector. Muchos no lo van a haber visto.",
      "«En el experimento real, de Simons y Chabris en 1999, cerca de la MITAD de las personas no vio al gorila. Se llama ceguera por falta de atención: cuando tu cerebro se concentra en algo, borra lo demás»."
    ],
    html: () => `
      <div class="gor-head">
        <div class="live-tag" data-in="pop">⚡ DESAFÍO</div>
        <h2 class="h-m" data-in="letters" data-d=".2">Contá los pases del equipo <span class="white-pill">BLANCO</span></h2>
      </div>
      <div class="gor-stage" data-in="zoom" data-d=".6"><canvas class="gor-cv" width="1500" height="700"></canvas>
        <div class="gor-msg">Tocá SIGUIENTE para empezar</div>
        <div class="gor-replay">REPETICIÓN ×2.5</div>
      </div>
      <div class="gor-overlay">
        <div class="gor-q">¿Cuántos pases?</div>
        <div class="gor-a"><span data-count="12">0</span> pases</div>
        <div class="gor-gorilla">…¿y el <span class="accent">GORILA</span>? 🦍</div>
      </div>
      <div class="gor-fact">
        <div class="big-num accent">~50%</div>
        <div>de las personas <b>no vio al gorila</b> en el experimento original.<br><span class="foot">Simons y Chabris · 1999 · “ceguera por falta de atención”</span></div>
      </div>`,
    enter(ctx) {
      const sim = I.gorillaSim(ctx.$(".gor-cv"));
      ctx.data.sim = sim;
      sim.draw(0);
    },
    step(ctx, n) {
      const sim = ctx.data.sim;
      const ov = ctx.$(".gor-overlay");
      const run = (speed, onEnd) => {
        if (ctx.data.stop) ctx.data.stop();
        let start = null;
        ctx.data.stop = ctx.raf((t) => {
          if (start === null) start = t;
          const T = ((t - start) / 1000) * speed;
          sim.draw(Math.min(T, sim.DURATION));
          if (T >= sim.DURATION) { ctx.data.stop(); onEnd && onEnd(); }
        });
      };
      if (n === 1) {
        ctx.tween(ctx.$(".gor-msg"), { opacity: 0, duration: 0.4 });
        ctx.sfx.playMusic("ambient");
        run(1, () => {
          ctx.sfx.stopMusic();
          gsap.set(ov, { display: "flex" });
          ctx.tween(ov, { opacity: 0 }, { opacity: 1, duration: 0.6 });
          ctx.tween(ctx.$(".gor-q"), { opacity: 0, scale: 0.7 }, { opacity: 1, scale: 1, duration: 0.8, ease: "back.out(2)" });
          ctx.sfx.boom(0.4);
        });
      }
      if (n === 2) {
        // por si tocan SIGUIENTE antes de que termine
        gsap.set(ov, { display: "flex", opacity: 1 });
        ctx.tween(ctx.$(".gor-q"), { opacity: 0, y: -30, duration: 0.4 });
        ctx.reveal(ctx.$(".gor-a"), "stamp");
      }
      if (n === 3) {
        ctx.tween(ctx.$(".gor-a"), { opacity: 0, duration: 0.3 });
        ctx.reveal(ctx.$(".gor-gorilla"), "zoom");
        ctx.after(1800, () => {
          ctx.tween(ov, { opacity: 0, duration: 0.5, onComplete: () => gsap.set(ov, { display: "none" }) });
          sim.setSpotlight(true);
          gsap.set(ctx.$(".gor-replay"), { opacity: 1 });
          let start = null;
          if (ctx.data.stop) ctx.data.stop();
          ctx.data.stop = ctx.raf((t) => {
            if (start === null) start = t;
            const T = 6.5 + ((t - start) / 1000) * 1.4;
            sim.draw(Math.min(T, 16.5));
            if (T >= 16.5) { start = t; }
          });
        });
      }
      if (n === 4) {
        const f = ctx.$(".gor-fact");
        gsap.set(f, { display: "flex" });
        ctx.tween(f, { opacity: 0, y: 60 }, { opacity: 1, y: 0, duration: 1, ease: "expo.out" });
        ctx.sfx.reveal();
      }
    },
  });

  // 15 ────────────────────────────────────────────── CEGUERA AL CAMBIO
  S.push({
    id: "cambio", title: "⚡ Encontrá la diferencia", hue: 200, transition: "iris", steps: 2,
    notes: [
      "«Les voy a mostrar dos fotos que se alternan con un parpadeo. Hay UNA cosa que cambia, y es grande. El primero que la encuentre, que grite». Tocá SIGUIENTE para empezar.",
      "Dejá que busquen 20-40 segundos. Suele costar muchísimo.",
      "«¡El árbol de la derecha! Aparece y desaparece. Se llama CEGUERA AL CAMBIO: si algo cambia durante un parpadeo o un corte, tu cerebro no se entera. Por eso a veces no notás errores en las películas»."
    ],
    html: () => `
      <div class="col center wrap">
        <div class="live-tag" data-in="pop">⚡ DESAFÍO</div>
        <h2 class="h-m" data-in="letters" data-d=".2">Hay <span class="accent">una</span> cosa que cambia. ¿Cuál?</h2>
        <div class="scene" data-in="zoom" data-d=".6">
          <div class="scene-a">${I.sceneSVG(true)}</div>
          <div class="scene-b">${I.sceneSVG(false)}</div>
          <div class="scene-blank"></div>
          <div class="scene-hl"></div>
        </div>
        <p class="punch small" data-step="2" data-in="up">Se llama <span class="accent">ceguera al cambio</span>: lo que cambia durante un parpadeo, tu cerebro no lo registra.</p>
      </div>`,
    step(ctx, n) {
      const a = ctx.$(".scene-a"), b = ctx.$(".scene-b"), blank = ctx.$(".scene-blank");
      if (n === 1) {
        let showA = true;
        const cycle = () => {
          blank.style.opacity = 1;
          ctx.after(140, () => {
            showA = !showA;
            a.style.opacity = showA ? 1 : 0;
            b.style.opacity = showA ? 0 : 1;
            blank.style.opacity = 0;
          });
        };
        ctx.every(1000, cycle);
      }
      if (n === 2) {
        const hl = ctx.$(".scene-hl");
        ctx.tween(hl, { opacity: 0, scale: 2.5 }, { opacity: 1, scale: 1, duration: 0.8, ease: "expo.out" });
        ctx.sfx.reveal();
      }
    },
  });

  // 16 ────────────────────────────────────────────── OÍDOS
  S.push({
    id: "oidos", title: "También te engañan los oídos", hue: 185, transition: "sweep", steps: 1,
    notes: [
      "«No solo los ojos. En 2018 se viralizó un audio: la mitad del mundo escuchaba “Yanny” y la otra mitad “Laurel”. ¡Era el MISMO audio! Depende de qué frecuencias prioriza tu cerebro». Preguntá si alguno se acuerda.",
      "«Y el efecto McGurk: si ves a alguien mover la boca diciendo “GA” pero el audio dice “BA”, tu cerebro mezcla las dos cosas y escuchás “DA”. Lo que VES cambia lo que ESCUCHÁS»."
    ],
    html: () => `
      <canvas class="fill waves-cv" width="1600" height="900"></canvas>
      <div class="col center wrap">
        <div class="kicker" data-in="fade">No solo la vista</div>
        <h2 class="h-l" data-in="letters" data-d=".2">También te engañan los <span class="accent">oídos</span></h2>
        <div class="row ear-cards">
          <div class="card ear" data-in="left" data-d=".9">
            <div class="ear-ico">🎧</div>
            <h3>¿Yanny o Laurel?</h3>
            <p>2018 · El <b>mismo audio</b>: la mitad del mundo escuchó una palabra… y la otra mitad, otra.</p>
          </div>
          <div class="card ear" data-step="1" data-in="right">
            <div class="ear-ico">👄</div>
            <h3>Efecto McGurk</h3>
            <p>Ves una boca decir <b>“GA”</b>, escuchás <b>“BA”</b>… y tu cerebro entiende <b class="accent">“DA”</b>.</p>
          </div>
        </div>
      </div>`,
    enter(ctx) {
      const draw = I.waves(ctx.$(".waves-cv"));
      ctx.raf((t) => draw(t / 1000));
    },
  });

  // 17 ────────────────────────────────────────────── MEMORIA
  S.push({
    id: "memoria", title: "Tu memoria también miente", hue: 330, transition: "dive", steps: 2,
    notes: [
      "«¿Se acuerdan perfecto de su cumpleaños de 5 años? Spoiler: probablemente no. Los recuerdos no se guardan como un video: se REARMAN cada vez que los recordás».",
      "(La foto se rearma distinta). «Y cada vez que se rearma, puede cambiar un poquito… y vos ni te enterás».",
      "«La psicóloga Elizabeth Loftus hizo un experimento famoso: logró que alrededor de 1 de cada 4 personas “recordara” haberse perdido en un shopping de chicos… algo que NUNCA les pasó»."
    ],
    html: () => `
      <div class="mem-layout">
        <div class="polaroid" data-in="slowmo" data-d=".4">
          <div class="mem-grid a"></div>
          <div class="mem-grid b"></div>
          <div class="pol-cap">Verano 2015 ☀️</div>
        </div>
        <div class="mem-text">
          <div class="kicker" data-in="fade">Recuerdos</div>
          <h2 class="h-m" data-in="letters" data-d=".2">Tu memoria también <span class="accent">miente</span></h2>
          <p class="lead small" data-in="up" data-d="1">Los recuerdos no se guardan como un video: se <b>rearman</b> cada vez que los recordás.</p>
          <p class="lead small" data-step="1" data-in="up">…y cada vez pueden <b class="accent">cambiar</b> un poquito.</p>
          <div class="card loftus" data-step="2" data-in="up">
            <div class="big-num accent">1 de 4</div>
            <div>personas “recordó” haberse <b>perdido en un shopping</b> de chico… algo que nunca pasó.<br><span class="foot left">Elizabeth Loftus · 1995</span></div>
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

  // 18 ────────────────────────────────────────────── EFECTO MANDELA
  S.push({
    id: "mandela", title: "⚡ Efecto Mandela", hue: 270, transition: "glitch", steps: 4,
    notes: [
      "«Tres preguntas, voten a mano alzada. Primera: ¿Pikachu tiene la punta de la cola negra?». Esperá votos y tocá SIGUIENTE.",
      "«¡NO! Su cola es amarilla con la base marrón. Nunca fue negra». Segunda: «¿El señor del Monopoly usa monóculo?».",
      "«¡NO! Nunca tuvo monóculo». Tercera: «¿Darth Vader dice “Luke, yo soy tu padre”?».",
      "«¡NO! Dice: “No… yo soy tu padre”. Nunca dice “Luke”».",
      "«Cuando muchísima gente recuerda lo mismo de forma equivocada se llama EFECTO MANDELA: mucha gente “recordaba” que Nelson Mandela había muerto en la cárcel en los 80… y en realidad salió libre y llegó a presidente de Sudáfrica»."
    ],
    html: () => `
      <div class="col center wrap">
        <div class="live-tag" data-in="pop">⚡ VOTACIÓN</div>
        <h2 class="h-l" data-in="letters" data-d=".2">Efecto <span class="accent">Mandela</span></h2>
        <div class="row mandela">
          <div class="card mq" data-in="up" data-d=".7"><div class="mq-ico">⚡</div><p>¿Pikachu tiene la punta de la cola <b>negra</b>?</p>
            <div class="mq-a" data-step="1" data-in="stamp"><b>NO</b> · amarilla con base marrón</div></div>
          <div class="card mq" data-in="up" data-d=".9"><div class="mq-ico">🎩</div><p>¿El señor del Monopoly usa <b>monóculo</b>?</p>
            <div class="mq-a" data-step="2" data-in="stamp"><b>NO</b> · nunca lo tuvo</div></div>
          <div class="card mq" data-in="up" data-d="1.1"><div class="mq-ico">🎬</div><p>Darth Vader dice: <b>“Luke, yo soy tu padre”</b></p>
            <div class="mq-a" data-step="3" data-in="stamp"><b>NO</b> · dice “No… yo soy tu padre”</div></div>
        </div>
        <p class="punch small" data-step="4" data-in="up">Cuando <b>mucha gente</b> recuerda lo mismo <span class="accent">de forma equivocada</span>.</p>
      </div>`,
    step(ctx, n) { if (n <= 3) ctx.sfx.wrong(); },
  });

  // 19 ────────────────────────────────────────────── PREDICCIÓN
  S.push({
    id: "prediccion", title: "¿Por qué pasa todo esto?", hue: 250, transition: "warp", steps: 2,
    notes: [
      "«¿Por qué el cerebro hace todo esto? Miren el circuito: le llega POCA información de los sentidos, y con eso arma una PREDICCIÓN de lo que hay afuera».",
      "«Tu cerebro no es una cámara de fotos: es una MÁQUINA DE PREDICCIONES. Adivina para ser rápido y ahorrar energía».",
      "«Casi siempre acierta, por eso estamos vivos. Pero cuando se equivoca… aparece una ilusión. Y hoy vieron un montón»."
    ],
    html: () => `
      <div class="col center wrap">
        <div class="kicker" data-in="fade">La explicación</div>
        <h2 class="h-l" data-in="letters" data-d=".2">¿Por qué pasa todo esto?</h2>
        <div class="flow">
          <div class="node" data-in="pop" data-d=".8"><div class="n-ico">👁️</div><b>Sentidos</b><span>llega poca info</span></div>
          <div class="link" data-in="fade" data-d="1.1"><i></i><i></i><i></i></div>
          <div class="node hot" data-in="pop" data-d="1.3"><div class="n-ico">🧠</div><b>Predicción</b><span>completa lo que falta</span></div>
          <div class="link" data-in="fade" data-d="1.6"><i></i><i></i><i></i></div>
          <div class="node" data-in="pop" data-d="1.8"><div class="n-ico">✨</div><b>Lo que “ves”</b><span>tu realidad</span></div>
        </div>
        <p class="punch" data-step="1" data-in="letters">No es una cámara: es una <span class="accent">máquina de predicciones</span>.</p>
        <p class="lead small" data-step="2" data-in="up">Casi siempre acierta… y cuando se equivoca, <b class="accent2">aparece una ilusión</b>.</p>
      </div>`,
    enter(ctx) {
      ctx.$$(".link i").forEach((dot, i) => {
        ctx.tween(dot, { left: "0%", opacity: 0 }, { left: "100%", opacity: 1, duration: 1.4, repeat: -1, delay: 2 + (i % 3) * 0.45, ease: "none" });
      });
    },
  });

  // 20 ────────────────────────────────────────────── CIERRE
  S.push({
    id: "cierre", title: "Cierre → Juego", hue: 265, transition: "burst", steps: 1,
    notes: [
      "«Así que la próxima vez que estés seguro de algo que viste… acordate: tu cerebro te miente. No creas todo lo que ves».",
      "«¿Prestaron atención? Vamos a comprobarlo…». Al tocar SIGUIENTE se abre la sala del juego. Pasales el enlace por WhatsApp con el botón COMPARTIR del control o que escaneen el QR."
    ],
    html: () => `
      <canvas class="fill brain-cv" width="1600" height="900"></canvas>
      <div class="col center wrap cierre">
        <h1 class="h-xl huge" data-in="letters" data-d=".4">NO CREAS</h1>
        <h1 class="h-xl huge accent" data-in="letters" data-d=".9">TODO LO QUE VES</h1>
        <div class="game-cta" data-step="1" data-in="zoom">
          <div class="kicker">¿Prestaron atención?</div>
          <div class="cta-big">🎮 Vamos a comprobarlo…</div>
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
