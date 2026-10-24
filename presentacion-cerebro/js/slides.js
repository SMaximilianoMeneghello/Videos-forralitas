// ============================================================
//  DIAPOSITIVAS — "YOUR BRAIN IS LYING TO YOU" (en inglés)
//
//  Cada diapositiva tiene:
//   id, title       -> nombre (se ve en el control remoto)
//   hue             -> color principal (0-360)
//   transition      -> dive | warp | sweep | glitch | burst | iris | rise
//   steps           -> cuántos toques de SIGUIENTE tiene antes de pasar
//   notes[]         -> qué decir en cada paso: en (inglés) + es (traducción). Solo en tu celu
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
    <text x="152" y="420" text-anchor="middle" class="svg-label">What you look at</text>
  </g>
  <!-- ojo -->
  <g data-in="zoom" data-d=".8">
    <circle cx="760" cy="250" r="215" fill="url(#eyeG)" stroke="hsl(var(--h) 90% 66%)" stroke-width="5"/>
    <path d="M940 140 A 215 215 0 0 1 940 360" stroke="#ff5c8a" stroke-width="14" fill="none" stroke-linecap="round"/>
    <ellipse cx="575" cy="250" rx="26" ry="88" fill="#22d3ee" opacity=".55"/>
    <text x="960" y="470" text-anchor="middle" class="svg-label" fill="#ff5c8a">Retina</text>
    <text x="575" y="470" text-anchor="middle" class="svg-label">Lens</text>
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
    id: "portada", title: "Cover", hue: 265, transition: "burst", steps: 0,
    notes: [
      { en: "Hello everyone! My name is ___, and today I'm going to talk about something you use every second: your brain. Quick question: who thinks that what you see is reality, exactly as it is? Raise your hand! … Well, today I'm going to show you that your brain is lying to you… all the time.", es: "¡Hola a todos! Me llamo ___ y hoy voy a hablar de algo que usan cada segundo: su cerebro. Pregunta rápida: ¿quién cree que lo que ve es la realidad, tal cual es? ¡Levanten la mano! … Bueno, hoy les voy a demostrar que su cerebro les miente… todo el tiempo." },
    ],
    html: (cfg) => `
      <canvas class="fill brain-cv" width="1600" height="900"></canvas>
      <div class="portada">
        <div class="kicker" data-in="fade" data-d="1.4">${cfg.materia ? cfg.materia + " · " : ""}Presentation</div>
        <h1 class="h-xl" data-in="letters" data-d="1.8">YOUR BRAIN</h1>
        <h1 class="h-xl accent glitch" data-text="IS LYING TO YOU" data-in="letters" data-d="2.3">IS LYING TO YOU</h1>
        <p class="lead" data-in="up" data-d="3.1">Illusions, tricks and why you can’t trust your own eyes</p>
        <div class="presenter" data-in="fade" data-d="3.7">Presented by <b>${cfg.presentador}</b></div>
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
    id: "realidad", title: "What you see is not reality", hue: 200, transition: "dive", steps: 1,
    notes: [
      { en: "Every second, your eyes, ears and skin send your brain about eleven million bits of information. And do you know how much your conscious mind can process? Only about fifty!", es: "Cada segundo, tus ojos, oídos y piel le mandan al cerebro unos once millones de bits de información. ¿Y saben cuánto puede procesar tu mente consciente? ¡Solo unos cincuenta!" },
      { en: "So what happens with the rest? Your brain fills in the gaps. What you see is a mix of real information… and things your brain makes up.", es: "¿Y qué pasa con el resto? Tu cerebro completa los huecos. Lo que ves es una mezcla de información real… y cosas que tu cerebro inventa." }
    ],
    html: () => `
      <div class="col center wrap">
        <div class="kicker" data-in="fade">Fact 01</div>
        <h2 class="h-l" data-in="letters" data-d=".2">What you see is not reality</h2>
        <div class="row stats">
          <div class="card stat" data-in="left" data-d=".9">
            <div class="stat-label">Your senses send</div>
            <div class="big-num" data-count="11000000">0</div>
            <div class="stat-unit">bits per second</div>
            <div class="dots-field"></div>
          </div>
          <div class="vs" data-in="zoom" data-d="1.3">VS</div>
          <div class="card stat" data-in="right" data-d="1.1">
            <div class="stat-label">Your conscious mind processes</div>
            <div class="big-num accent" data-count="50">0</div>
            <div class="stat-unit">bits per second</div>
            <div class="dots-one"><i></i></div>
          </div>
        </div>
        <p class="punch" data-step="1" data-in="letters">Your brain <span class="accent">makes up</span> the rest.</p>
        <p class="foot" data-in="fade" data-d="2.4">Approximate values · classic estimate from information theory</p>
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
    id: "energia", title: "Your brain is always hungry", hue: 320, transition: "warp", steps: 1,
    notes: [
      { en: "Your brain is only about two percent of your body weight… but it uses about twenty percent of your energy. Why do you think it uses so much?", es: "Tu cerebro es solo un 2% de tu peso… pero usa cerca del 20% de tu energía. ¿Por qué creen que gasta tanto?" },
      { en: "Because it uses so much energy, it needs to save energy. It doesn't analyze everything: it takes shortcuts, and it predicts. Today we are going to hack those shortcuts.", es: "Como gasta tanta energía, necesita ahorrar. No analiza todo: toma atajos y predice. Hoy vamos a hackear esos atajos." }
    ],
    html: () => `
      <div class="col center wrap">
        <div class="kicker" data-in="fade">Fact 02</div>
        <h2 class="h-l" data-in="letters" data-d=".2">Your brain is always hungry</h2>
        <div class="row rings">
          <div class="ring-box" data-in="pop" data-d=".8">
            <svg viewBox="0 0 300 300" class="ring"><circle cx="150" cy="150" r="120" class="ring-bg"/><circle cx="150" cy="150" r="120" class="ring-fg" data-p="0.02"/></svg>
            <div class="ring-val"><span data-count="2">0</span>%</div>
            <div class="ring-label">of your <b>body weight</b></div>
          </div>
          <div class="ring-box" data-in="pop" data-d="1.1">
            <svg viewBox="0 0 300 300" class="ring"><circle cx="150" cy="150" r="120" class="ring-bg"/><circle cx="150" cy="150" r="120" class="ring-fg hot" data-p="0.2"/></svg>
            <div class="ring-val accent"><span data-count="20">0</span>%</div>
            <div class="ring-label">of your <b>energy</b></div>
          </div>
        </div>
        <p class="punch" data-step="1" data-in="up">So it takes <span class="accent">shortcuts</span>: instead of checking everything… it <b class="accent2">PREDICTS</b>.</p>
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
    id: "invertida", title: "The image arrives upside down", hue: 190, transition: "sweep", steps: 1,
    notes: [
      { en: "Light goes into your eye through the lens. The light rays cross… and the image arrives at the retina upside down! Look at the tree.", es: "La luz entra al ojo por el cristalino. Los rayos se cruzan… ¡y la imagen llega a la retina dada vuelta! Miren el árbol." },
      { en: "But you never see the world upside down, because your brain flips the image automatically. That's the first lie: your brain edits the image.", es: "Pero nunca ven el mundo al revés, porque el cerebro da vuelta la imagen automáticamente. Esa es la primera mentira: tu cerebro edita la imagen." }
    ],
    html: () => `
      <div class="col wrap">
        <div class="kicker" data-in="fade">How we see</div>
        <h2 class="h-l" data-in="letters" data-d=".2">The image arrives <span class="accent flip-word">upside down</span></h2>
        ${eyeSVG}
        <div class="flip-note" data-step="1" data-in="right">
          <span class="brain-ico">🧠</span>
          <div>…and your brain <b class="accent">flips it</b><br>without you noticing</div>
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
    id: "punto-ciego", title: "⚡ The blind spot", hue: 0, transition: "iris", steps: 2,
    notes: [
      { en: "Everybody here has a hole in their vision… and you never noticed it. Let's test it together!", es: "Todos acá tienen un agujero en la vista… y nunca se dieron cuenta. ¡Probémoslo juntos!" },
      { en: "Cover your LEFT eye. With your right eye, look at the cross. Don't look at the red dot! Now move a little closer or a little farther away, slowly… At some point, the red dot disappears! (Give them 30–40 seconds.)", es: "Tápense el ojo IZQUIERDO. Con el derecho miren la cruz. ¡No miren el punto rojo! Ahora acérquense o aléjense despacio… ¡En algún momento el punto rojo desaparece! (Dales 30–40 segundos)." },
      { en: "Did it disappear? That's your blind spot. It's where the optic nerve leaves the eye, and there are no light receptors there. But you don't see a black hole, because your brain fills it in with what is around it.", es: "¿Desapareció? Ese es tu punto ciego. Es donde el nervio óptico sale del ojo, y ahí no hay receptores de luz. Pero no ven un agujero negro, porque tu cerebro lo rellena con lo que hay alrededor." }
    ],
    html: () => `
      <div class="col center wrap">
        <div class="live-tag" data-in="pop">⚡ LIVE TEST</div>
        <h2 class="h-l" data-in="letters" data-d=".2">You have a <span class="accent">hole</span> in your vision</h2>
        <p class="lead" data-in="up" data-d="1">And you never noticed. Let’s test it.</p>
      </div>
      <div class="bs-panel">
        <div class="bs-instr">
          <span>1 · Cover your <b>LEFT</b> eye</span>
          <span>2 · Stare at the <b>✚</b> with your right eye</span>
          <span>3 · Move closer or farther <b>slowly</b></span>
        </div>
        <div class="bs-cross">✚</div>
        <div class="bs-dot"></div>
        <div class="bs-explain">
          <b>It disappeared!</b> That’s where the optic nerve leaves the eye: there are no light receptors.<br>
          Your brain <b>fills in the gap</b> with what’s around it.
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
    id: "muller", title: "⚡ Which line is longer?", hue: 285, transition: "glitch", steps: 2,
    notes: [
      { en: "Which line is longer, A or B? Raise your hand if you think A… now B… and who thinks they are the same?", es: "¿Qué línea es más larga, la A o la B? Levanten la mano los que piensan A… ahora B… ¿y quién piensa que son iguales?" },
      { en: "Are you sure? Look…", es: "¿Están seguros? Miren…" },
      { en: "They are exactly the same length! The arrow ends trick your brain, because it thinks about depth, like the corners of a room. This is the Müller-Lyer illusion, from 1889.", es: "¡Miden exactamente lo mismo! Las puntas de flecha engañan al cerebro, porque piensa en profundidad, como las esquinas de una habitación. Es la ilusión de Müller-Lyer, de 1889." }
    ],
    html: () => `
      <div class="col center wrap">
        <div class="live-tag" data-in="pop">⚡ VOTE</div>
        <h2 class="h-m" data-in="letters" data-d=".2">Which line is longer?</h2>
        <div data-in="zoom" data-d=".7" class="ml-wrap">${mullerSVG}</div>
        <div class="vote-row" data-in="up" data-d="1.2"><span class="chip">✋ A</span><span class="chip">✋ B</span><span class="chip">✋ Same</span></div>
        <div class="stamp" data-step="2" data-in="stamp">THEY’RE EQUAL!</div>
        <p class="foot" data-step="2" data-in="fade" data-d=".6">Müller-Lyer illusion · 1889</p>
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
    id: "adelson", title: "⚡ Adelson’s checkerboard", hue: 160, transition: "dive", steps: 2,
    notes: [
      { en: "Which square is darker, A or B? Vote! … Most people say A is darker.", es: "¿Qué casilla es más oscura, la A o la B? ¡Voten! … Casi todos dicen que la A es más oscura." },
      { en: "I'm going to connect the two squares with a stripe of the same color… They are the same gray!", es: "Voy a unir las dos casillas con una franja del mismo color… ¡Son el mismo gris!" },
      { en: "Now I hide everything else… See? Identical. Your brain knows that shadows make things darker, so it makes things in the shadow look lighter. It doesn't show you the real color: it shows you what it thinks the color is. Edward Adelson created this at MIT in 1995.", es: "Ahora tapo todo lo demás… ¿Ven? Idénticas. Tu cerebro sabe que las sombras oscurecen, así que hace que lo que está en sombra se vea más claro. No te muestra el color real: te muestra lo que cree que es. Lo creó Edward Adelson en el MIT en 1995." }
    ],
    html: () => `
      <div class="adelson-layout">
        <div class="adelson-stage" data-in="slowmo" data-d=".3">
          <canvas class="adelson-cv" width="1000" height="820"></canvas>
          <canvas class="adelson-fx" width="1000" height="820"></canvas>
        </div>
        <div class="adelson-text">
          <div class="live-tag" data-in="pop" data-d=".4">⚡ VOTE</div>
          <h2 class="h-m" data-in="letters" data-d=".6">Which one is darker?</h2>
          <div class="vote-row left" data-in="up" data-d="1.3"><span class="chip">✋ A</span><span class="chip">✋ B</span></div>
          <div class="reveal-box" data-step="1" data-in="up">They are <b class="accent">EXACTLY</b><br>the same gray.</div>
          <p class="lead small" data-step="2" data-in="up">Your brain <b>lightens</b> what it thinks is in shadow.</p>
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
    id: "vestido", title: "⚡ The dress (2015)", hue: 220, transition: "warp", steps: 2,
    notes: [
      { en: "In 2015, a photo of a dress divided the whole internet. What colors do you see? Raise your hand for blue and black… and now for white and gold.", es: "En 2015, la foto de un vestido dividió a todo internet. ¿Qué colores ven? Levanten la mano los que ven azul y negro… y ahora blanco y dorado." },
      { en: "The real dress was… blue and black!", es: "El vestido real era… ¡azul y negro!" },
      { en: "Why did people see different colors? The light in the photo was strange. If your brain thinks there is yellow light, it removes it, and you see blue and black. If your brain thinks the dress is in a blue shadow, you see white and gold. Same photo, different brains, different colors!", es: "¿Por qué la gente veía colores distintos? La luz de la foto era rara. Si tu cerebro cree que hay luz amarilla, la quita, y ves azul y negro. Si cree que el vestido está en una sombra azulada, ves blanco y dorado. ¡Misma foto, distintos cerebros, distintos colores!" }
    ],
    html: () => `
      <div class="col center wrap">
        <div class="live-tag" data-in="pop">⚡ VOTE</div>
        <h2 class="h-m" data-in="letters" data-d=".2">The dress that broke the internet</h2>
        <div class="row dresses">
          <div class="dress-box" data-in="slowmo" data-d=".6">
            ${dressSVG("#8f97c8", "#7a6540", "photo")}
            <div class="dress-cap">Colors in the photo · 2015</div>
          </div>
          <div class="dress-box real" data-step="1" data-in="flip">
            ${dressSVG("#1e3a9a", "#0b0b10", "real")}
            <div class="dress-cap big">It was <b class="accent">BLUE and BLACK</b></div>
          </div>
        </div>
        <div class="vote-row" data-in="up" data-d="1.4"><span class="chip">💙🖤 Blue and black</span><span class="chip">🤍💛 White and gold</span></div>
        <div class="row lights" data-step="2" data-in="up">
          <div class="light-card"><span class="sun">💡</span> Your brain assumes <b>yellow light</b>? → you see <b>blue and black</b></div>
          <div class="light-card"><span class="sun">🌥️</span> It assumes <b>blue shadow</b>? → you see <b>white and gold</b></div>
        </div>
      </div>`,
    step(ctx, n) {
      if (n === 1) { ctx.after(900, () => ctx.sfx.reveal()); ctx.tween(ctx.$(".vote-row"), { opacity: 0, duration: 0.4 }); }
    },
  });

  // 9 ─────────────────────────────────────────────── SERPIENTES
  S.push({
    id: "serpientes", title: "Pictures that move by themselves", hue: 60, transition: "burst", steps: 1,
    notes: [
      { en: "(Don't say anything at first. Let them look for five seconds.) What do you see? (They will say it's moving.)", es: "(No digas nada al principio. Dejá que miren cinco segundos.) ¿Qué ven? (Van a decir que se mueve)." },
      { en: "This image is one hundred percent still. It's just a drawing! The movement is created by your brain, because of the way it processes contrast when your eyes move. If you stare at one circle, it stops. It's inspired by the Rotating Snakes, by Akiyoshi Kitaoka.", es: "Esta imagen está 100% quieta. ¡Es solo un dibujo! El movimiento lo crea tu cerebro, por cómo procesa el contraste cuando movés los ojos. Si mirás fijo un círculo, se frena. Está inspirada en las Serpientes Giratorias de Akiyoshi Kitaoka." }
    ],
    html: () => `
      <canvas class="fill snakes-cv" width="1600" height="900" data-in="slowmo"></canvas>
      <div class="snake-banner" data-in="up" data-d="1.4">Nothing is moving. <b>I promise.</b></div>
      <div class="snake-badge" data-step="1" data-in="pop">📷 100% still image · your brain creates the movement<br><small>Inspired by “Rotating Snakes” by Akiyoshi Kitaoka</small></div>`,
    enter(ctx) { I.snakes(ctx.$(".snakes-cv")); },
  });

  // 10 ────────────────────────────────────────────── POSTIMAGEN
  S.push({
    id: "postimagen", title: "⚡ Stare at the dot for 20 seconds", hue: 30, transition: "iris", steps: 2,
    notes: [
      { en: "Now I need everybody to look at the black dot in the middle, without moving your eyes, for twenty seconds. When the screen turns white, keep looking at the dot! (Press NEXT to start the countdown.)", es: "Ahora necesito que todos miren el punto negro del centro, sin mover los ojos, durante veinte segundos. ¡Cuando la pantalla se ponga blanca, sigan mirando el punto! (Tocá SIGUIENTE para arrancar la cuenta)." },
      { en: "(Stay quiet during the countdown.) When it turns white, ask: What did you see? (They should see the Argentine flag with its real colors.)", es: "(Silencio durante la cuenta.) Cuando se ponga blanca, preguntá: ¿Qué vieron? (Deberían ver la bandera argentina con sus colores reales)." },
      { en: "The cells in your eyes that detect color get tired if they look at the same color for a long time. When you look at white, they show the opposite color. That's why you saw the light blue and white flag… and it was never on the screen!", es: "Las células del ojo que detectan los colores se cansan si miran mucho tiempo el mismo color. Cuando mirás blanco, muestran el color opuesto. Por eso vieron la bandera celeste y blanca… ¡y nunca estuvo en la pantalla!" }
    ],
    html: () => `
      <div class="col center wrap ai-intro">
        <div class="live-tag" data-in="pop">⚡ LIVE TEST</div>
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
        <div class="ws-explain">The cells in your eyes got <b>tired</b> of those colors, so now they show the <b>opposite</b> ones.<br>The light blue and white flag was <b>never</b> on the screen.</div>
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
  const STROOP_COLS = { RED: "#ff3b3b", BLUE: "#3b82f6", GREEN: "#22c55e", YELLOW: "#facc15", PURPLE: "#a855f7", ORANGE: "#fb923c" };
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
    id: "stroop", title: "⚡ Say the COLOR, not the word", hue: 0, transition: "sweep", steps: 3,
    notes: [
      { en: "Quick game! You will see color words. You have to say out loud the COLOR of the letters, NOT the word. All together!", es: "¡Juego rápido! Van a ver palabras de colores. Tienen que decir en voz alta el COLOR de las letras, NO la palabra. ¡Todos juntos!" },
      { en: "Round one is easy: the word and the color are the same. Let's go, fast!", es: "La ronda uno es fácil: la palabra y el color coinciden. ¡Vamos, rápido!" },
      { en: "Round two is hard: now they are different. Come on… faster!", es: "La ronda dos es difícil: ahora no coinciden. Dale… ¡más rápido!" },
      { en: "Why is it so hard? Because reading is automatic. Your brain can't “not read”. The two signals crash. This is called the Stroop effect, and it was discovered in 1935.", es: "¿Por qué cuesta tanto? Porque leer es automático. Tu cerebro no puede “no leer”. Las dos señales chocan. Se llama efecto Stroop, y se descubrió en 1935." }
    ],
    html: () => `
      <div class="col center wrap">
        <div class="live-tag" data-in="pop">⚡ LIVE GAME</div>
        <h2 class="h-m" data-in="letters" data-d=".2">Say the <span class="accent">COLOR</span>, not the word</h2>
        <div class="stroop-area">
          <div class="stroop r1"><div class="round-lbl">Round 1 · Easy 😎</div><div class="sg">${stroopGrid(false)}</div></div>
          <div class="stroop r2"><div class="round-lbl">Round 2 · Hard 😈</div><div class="sg">${stroopGrid(true)}</div></div>
          <div class="stroop r3">
            <div class="reveal-box">Reading is <b class="accent">automatic</b>:<br>your brain can’t “not read”.</div>
            <p class="foot">The Stroop effect · John Ridley Stroop · 1935</p>
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
    id: "pareidolia", title: "Pareidolia: faces everywhere", hue: 45, transition: "dive", steps: 1,
    notes: [
      { en: "What do you see here? An outlet, a house, a car… or faces? What emotion does each one have? (The outlet looks surprised, the car looks happy.)", es: "¿Qué ven acá? Un enchufe, una casa, un auto… ¿o caras? ¿Qué emoción tiene cada una? (El enchufe parece sorprendido, el auto contento)." },
      { en: "This is called pareidolia. Your brain is programmed to find faces, because recognizing faces quickly was important to survive. Your brain prefers to see a face that isn't there… than to miss one that is there.", es: "Esto se llama pareidolia. Tu cerebro está programado para encontrar caras, porque reconocerlas rápido era importante para sobrevivir. Tu cerebro prefiere ver una cara que no está… antes que no ver una que sí está." }
    ],
    html: () => `
      <div class="col center wrap">
        <div class="kicker" data-in="fade">Face detector</div>
        <h2 class="h-l" data-in="letters" data-d=".2">Do you see faces?</h2>
        <div class="row objs">
          <div class="obj-card" data-in="up" data-d=".7">${outletSVG}<span>An outlet</span></div>
          <div class="obj-card" data-in="up" data-d=".9">${houseSVG}<span>A house</span></div>
          <div class="obj-card" data-in="up" data-d="1.1">${carSVG}<span>A car</span></div>
        </div>
        <p class="punch" data-step="1" data-in="up">It’s called <span class="accent">PAREIDOLIA</span>: your brain looks for faces everywhere.</p>
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
    id: "marte", title: "The Face on Mars", hue: 15, transition: "warp", steps: 1,
    notes: [
      { en: "In 1976, NASA's Viking 1 probe took this photo of Mars. It looked like a giant face! People invented theories about aliens and ancient ruins.", es: "En 1976, la sonda Viking 1 de la NASA sacó esta foto de Marte. ¡Parecía una cara gigante! La gente inventó teorías de extraterrestres y ruinas antiguas." },
      { en: "Years later, with much better cameras, they photographed the same place. It was just a mountain! The face was created by our brains.", es: "Años después, con cámaras mucho mejores, fotografiaron el mismo lugar. ¡Era solo una montaña! La cara la crearon nuestros cerebros." }
    ],
    html: () => `
      <div class="col center wrap">
        <div class="kicker" data-in="fade">True story · NASA</div>
        <h2 class="h-l" data-in="letters" data-d=".2">The “Face on Mars”</h2>
        <div class="row mars-row">
          <figure class="mars-fig" data-in="slowmo" data-d=".7">${marsSVG(true)}<figcaption><b>1976</b> · Viking 1 probe <span class="tagx">low resolution</span></figcaption></figure>
          <figure class="mars-fig" data-step="1" data-in="flip">${marsSVG(false)}<figcaption><b>Years later</b> · Better cameras <span class="tagx ok">high resolution</span></figcaption></figure>
        </div>
        <p class="punch small" data-step="1" data-in="up" data-d=".8">It was just a <b>mountain</b>. The face… was made by your brain.</p>
      </div>`,
  });

  // 14 ────────────────────────────────────────────── GORILA
  S.push({
    id: "gorila", title: "⚡ Attention challenge", hue: 140, transition: "glitch", steps: 4,
    notes: [
      { en: "Challenge! Count in silence how many times the team in WHITE passes the ball. Only the white team. Concentrate! (Press NEXT to start.)", es: "¡Desafío! Cuenten en silencio cuántas veces se pasa la pelota el equipo de BLANCO. Solo el equipo blanco. ¡Concéntrense! (Tocá SIGUIENTE para empezar)." },
      { en: "(Let the animation run for 22 seconds. Don't say anything.) When it ends, ask: How many passes did you count?", es: "(Dejá correr la animación 22 segundos. No digas nada.) Cuando termine, preguntá: ¿Cuántos pases contaron?" },
      { en: "It was twelve passes! Well done if you got it right.", es: "¡Fueron doce pases! Muy bien los que acertaron." },
      { en: "Now the important question… did anyone see the GORILLA? (Fast replay with the spotlight.)", es: "Ahora la pregunta importante… ¿alguien vio al GORILA? (Repetición rápida con el reflector)." },
      { en: "In the real experiment, by Simons and Chabris in 1999, about HALF of the people did not see the gorilla. This is called inattentional blindness: when your brain focuses on one thing, it deletes the rest.", es: "En el experimento real, de Simons y Chabris en 1999, cerca de la MITAD de las personas no vio al gorila. Se llama ceguera por falta de atención: cuando tu cerebro se concentra en una cosa, borra el resto." }
    ],
    html: () => `
      <div class="gor-head">
        <div class="live-tag" data-in="pop">⚡ CHALLENGE</div>
        <h2 class="h-m" data-in="letters" data-d=".2">Count the passes of the <span class="white-pill">WHITE</span> team</h2>
      </div>
      <div class="gor-stage" data-in="zoom" data-d=".6"><canvas class="gor-cv" width="1500" height="700"></canvas>
        <div class="gor-msg">Ready? Let’s start!</div>
        <div class="gor-replay">REPLAY</div>
      </div>
      <div class="gor-overlay">
        <div class="gor-q">How many passes?</div>
        <div class="gor-a"><span data-count="12">0</span> passes</div>
        <div class="gor-gorilla">…and the <span class="accent">GORILLA</span>? 🦍</div>
      </div>
      <div class="gor-fact">
        <div class="big-num accent">~50%</div>
        <div>of people <b>didn’t see the gorilla</b> in the original experiment.<br><span class="foot">Simons &amp; Chabris · 1999 · “inattentional blindness”</span></div>
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
    id: "cambio", title: "⚡ Spot the difference", hue: 200, transition: "iris", steps: 2,
    notes: [
      { en: "I'm going to show you two pictures that switch with a blink. ONE thing changes, and it's big. The first person who finds it, shout! (Press NEXT.)", es: "Les voy a mostrar dos imágenes que se alternan con un parpadeo. Cambia UNA cosa, y es grande. ¡El primero que la encuentre, que grite! (Tocá SIGUIENTE)." },
      { en: "(Let them search for 20 to 40 seconds.) Can you see it? Keep looking…", es: "(Dejá que busquen entre 20 y 40 segundos.) ¿La ven? Sigan buscando…" },
      { en: "The tree on the right! It appears and disappears. This is called change blindness: if something changes during a blink or a cut, your brain doesn't notice. That's why we don't see mistakes in movies.", es: "¡El árbol de la derecha! Aparece y desaparece. Se llama ceguera al cambio: si algo cambia durante un parpadeo o un corte, tu cerebro no se da cuenta. Por eso no vemos los errores en las películas." }
    ],
    html: () => `
      <div class="col center wrap">
        <div class="live-tag" data-in="pop">⚡ CHALLENGE</div>
        <h2 class="h-m" data-in="letters" data-d=".2"><span class="accent">One</span> thing changes. What is it?</h2>
        <div class="scene" data-in="zoom" data-d=".6">
          <div class="scene-a">${I.sceneSVG(true)}</div>
          <div class="scene-b">${I.sceneSVG(false)}</div>
          <div class="scene-blank"></div>
          <div class="scene-hl"></div>
        </div>
        <p class="punch small" data-step="2" data-in="up">It’s called <span class="accent">change blindness</span>: if something changes during a blink, your brain doesn’t notice.</p>
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
    id: "oidos", title: "Your ears lie too", hue: 185, transition: "sweep", steps: 1,
    notes: [
      { en: "It's not only your eyes. In 2018, an audio went viral: half of the world heard “Yanny” and the other half heard “Laurel”. It was the SAME audio! It depends on which sounds your brain pays attention to. Does anyone remember it?", es: "No son solo los ojos. En 2018 se viralizó un audio: la mitad del mundo escuchaba “Yanny” y la otra mitad “Laurel”. ¡Era el MISMO audio! Depende de a qué sonidos les presta atención tu cerebro. ¿Alguien se acuerda?" },
      { en: "And this is the McGurk effect: if you see a person saying “ga”, but the audio says “ba”, your brain mixes them and you hear “da”. What you SEE changes what you HEAR.", es: "Y este es el efecto McGurk: si ves a una persona decir “ga” pero el audio dice “ba”, tu cerebro los mezcla y escuchás “da”. Lo que VES cambia lo que ESCUCHÁS." }
    ],
    html: () => `
      <canvas class="fill waves-cv" width="1600" height="900"></canvas>
      <div class="col center wrap">
        <div class="kicker" data-in="fade">Not only your eyes</div>
        <h2 class="h-l" data-in="letters" data-d=".2">Your <span class="accent">ears</span> lie too</h2>
        <div class="row ear-cards">
          <div class="card ear" data-in="left" data-d=".9">
            <div class="ear-ico">🎧</div>
            <h3>Yanny or Laurel?</h3>
            <p>2018 · The <b>same audio</b>: half of the world heard one word… and the other half heard a different one.</p>
          </div>
          <div class="card ear" data-step="1" data-in="right">
            <div class="ear-ico">👄</div>
            <h3>The McGurk effect</h3>
            <p>You see a mouth say <b>“GA”</b>, you hear <b>“BA”</b>… and your brain understands <b class="accent">“DA”</b>.</p>
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
    id: "memoria", title: "Your memory lies too", hue: 330, transition: "dive", steps: 2,
    notes: [
      { en: "Do you remember your fifth birthday perfectly? Spoiler: probably not. Memories are not saved like a video: your brain rebuilds them every time you remember them.", es: "¿Se acuerdan perfecto de su cumpleaños de cinco años? Spoiler: probablemente no. Los recuerdos no se guardan como un video: tu cerebro los rearma cada vez que los recordás." },
      { en: "And every time it rebuilds them, they can change a little… and you don't even notice.", es: "Y cada vez que los rearma, pueden cambiar un poquito… y ni te das cuenta." },
      { en: "The psychologist Elizabeth Loftus did a famous experiment: about one in four people “remembered” getting lost in a shopping mall as a child… something that NEVER happened.", es: "La psicóloga Elizabeth Loftus hizo un experimento famoso: alrededor de una de cada cuatro personas “recordó” haberse perdido en un shopping de chico… algo que NUNCA pasó." }
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
          <p class="lead small" data-in="up" data-d="1">Memories aren’t saved like a video: they are <b>rebuilt</b> every time you remember them.</p>
          <p class="lead small" data-step="1" data-in="up">…and every time, they can <b class="accent">change</b> a little.</p>
          <div class="card loftus" data-step="2" data-in="up">
            <div class="big-num accent">1 in 4</div>
            <div>people “remembered” getting <b>lost in a shopping mall</b> as a kid… something that never happened.<br><span class="foot left">Elizabeth Loftus · 1995</span></div>
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
    id: "mandela", title: "⚡ The Mandela effect", hue: 270, transition: "glitch", steps: 4,
    notes: [
      { en: "Three questions. Vote with your hands! First: does Pikachu have a black tip on its tail?", es: "Tres preguntas. ¡Voten con la mano! Primera: ¿Pikachu tiene la punta de la cola negra?" },
      { en: "NO! Its tail is yellow, with a brown part at the bottom. It was never black. Second: does the Monopoly man wear a monocle?", es: "¡NO! Su cola es amarilla, con una parte marrón abajo. Nunca fue negra. Segunda: ¿el señor del Monopoly usa monóculo?" },
      { en: "NO! He never had a monocle. Third: does Darth Vader say “Luke, I am your father”?", es: "¡NO! Nunca tuvo monóculo. Tercera: ¿Darth Vader dice “Luke, yo soy tu padre”?" },
      { en: "NO! He says: “No, I am your father.” He never says “Luke”.", es: "¡NO! Dice: “No, yo soy tu padre”. Nunca dice “Luke”." },
      { en: "When lots of people remember the same thing wrong, it's called the Mandela effect. Many people “remembered” that Nelson Mandela died in prison in the 1980s… but actually he was freed in 1990 and became president of South Africa.", es: "Cuando muchísima gente recuerda lo mismo de forma equivocada, se llama efecto Mandela. Mucha gente “recordaba” que Nelson Mandela murió en la cárcel en los años 80… pero en realidad lo liberaron en 1990 y llegó a presidente de Sudáfrica." }
    ],
    html: () => `
      <div class="col center wrap">
        <div class="live-tag" data-in="pop">⚡ VOTE</div>
        <h2 class="h-l" data-in="letters" data-d=".2">The <span class="accent">Mandela</span> effect</h2>
        <div class="row mandela">
          <div class="card mq" data-in="up" data-d=".7"><div class="mq-ico">⚡</div><p>Does Pikachu have a <b>black</b> tip on its tail?</p>
            <div class="mq-a" data-step="1" data-in="stamp"><b>NO</b> · yellow with a brown base</div></div>
          <div class="card mq" data-in="up" data-d=".9"><div class="mq-ico">🎩</div><p>Does the Monopoly man wear a <b>monocle</b>?</p>
            <div class="mq-a" data-step="2" data-in="stamp"><b>NO</b> · he never did</div></div>
          <div class="card mq" data-in="up" data-d="1.1"><div class="mq-ico">🎬</div><p>Darth Vader says: <b>“Luke, I am your father”</b></p>
            <div class="mq-a" data-step="3" data-in="stamp"><b>NO</b> · he says “No, I am your father”</div></div>
        </div>
        <p class="punch small" data-step="4" data-in="up">When <b>lots of people</b> remember the same thing <span class="accent">wrong</span>.</p>
      </div>`,
    step(ctx, n) { if (n <= 3) ctx.sfx.wrong(); },
  });

  // 19 ────────────────────────────────────────────── PREDICCIÓN
  S.push({
    id: "prediccion", title: "Why does this happen?", hue: 250, transition: "warp", steps: 2,
    notes: [
      { en: "Why does the brain do all this? Look at this circuit: your senses send only a little information, and with that, your brain makes a prediction about the world outside.", es: "¿Por qué el cerebro hace todo esto? Miren este circuito: los sentidos mandan poca información, y con eso el cerebro arma una predicción del mundo de afuera." },
      { en: "Your brain is not a camera: it's a prediction machine. It guesses, to be fast and to save energy.", es: "Tu cerebro no es una cámara: es una máquina de predicciones. Adivina, para ser rápido y ahorrar energía." },
      { en: "Most of the time it's right… that's why we're alive! But when it makes a mistake… you get an illusion. And today you saw a lot of them.", es: "Casi siempre acierta… ¡por eso estamos vivos! Pero cuando se equivoca… aparece una ilusión. Y hoy vieron un montón." }
    ],
    html: () => `
      <div class="col center wrap">
        <div class="kicker" data-in="fade">The explanation</div>
        <h2 class="h-l" data-in="letters" data-d=".2">Why does this happen?</h2>
        <div class="flow">
          <div class="node" data-in="pop" data-d=".8"><div class="n-ico">👁️</div><b>Senses</b><span>a little info arrives</span></div>
          <div class="link" data-in="fade" data-d="1.1"><i></i><i></i><i></i></div>
          <div class="node hot" data-in="pop" data-d="1.3"><div class="n-ico">🧠</div><b>Prediction</b><span>fills in the gaps</span></div>
          <div class="link" data-in="fade" data-d="1.6"><i></i><i></i><i></i></div>
          <div class="node" data-in="pop" data-d="1.8"><div class="n-ico">✨</div><b>What you “see”</b><span>your reality</span></div>
        </div>
        <p class="punch" data-step="1" data-in="letters">It’s not a camera: it’s a <span class="accent">prediction machine</span>.</p>
        <p class="lead small" data-step="2" data-in="up">It’s almost always right… and when it’s wrong, <b class="accent2">you get an illusion</b>.</p>
      </div>`,
    enter(ctx) {
      ctx.$$(".link i").forEach((dot, i) => {
        ctx.tween(dot, { left: "0%", opacity: 0 }, { left: "100%", opacity: 1, duration: 1.4, repeat: -1, delay: 2 + (i % 3) * 0.45, ease: "none" });
      });
    },
  });

  // 20 ────────────────────────────────────────────── CIERRE
  S.push({
    id: "cierre", title: "Ending → Game", hue: 265, transition: "burst", steps: 1,
    notes: [
      { en: "So, next time you are sure about something you saw… remember: your brain is lying to you. Don't believe everything you see!", es: "Así que la próxima vez que estés seguro de algo que viste… acordate: tu cerebro te miente. ¡No creas todo lo que ves!" },
      { en: "Were you paying attention? Let's find out! (Press NEXT to open the game room. Share the link with the SHARE button, or ask them to scan the QR code.)", es: "¿Prestaron atención? ¡Vamos a comprobarlo! (Tocá SIGUIENTE para abrir la sala del juego. Pasá el enlace con COMPARTIR o que escaneen el QR)." }
    ],
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
