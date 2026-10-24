// ============================================================
//  SFX — efectos de sonido y música generados con Web Audio
//  (no hace falta ningún archivo de audio)
// ============================================================
(function () {
  let ctx = null;
  let master = null;
  let musicBus = null;
  let noiseBuf = null;
  let muted = false;
  let music = null; // {stop}

  function init() {
    if (ctx) { if (ctx.state === "suspended") ctx.resume(); return; }
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return;
    ctx = new AC();
    master = ctx.createGain();
    master.gain.value = muted ? 0 : 0.8;
    // compresor suave para que nada sature en los parlantes de la netbook
    const comp = ctx.createDynamicsCompressor();
    comp.threshold.value = -14;
    comp.ratio.value = 4;
    master.connect(comp).connect(ctx.destination);
    musicBus = ctx.createGain();
    musicBus.gain.value = 0.35;
    musicBus.connect(master);
    noiseBuf = ctx.createBuffer(1, ctx.sampleRate * 2, ctx.sampleRate);
    const d = noiseBuf.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
  }

  const ok = () => ctx && ctx.state === "running";
  const now = () => ctx.currentTime;

  function env(g, t, a, peak, dcy, end = 0.0001) {
    g.gain.cancelScheduledValues(t);
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(peak, t + a);
    g.gain.exponentialRampToValueAtTime(end, t + a + dcy);
  }

  function tone(freq, { type = "sine", t = now(), a = 0.01, d = 0.3, vol = 0.3, to = null, dest = master, detune = 0 } = {}) {
    const o = ctx.createOscillator();
    const g = ctx.createGain();
    o.type = type;
    o.frequency.setValueAtTime(freq, t);
    o.detune.value = detune;
    if (to) o.frequency.exponentialRampToValueAtTime(to, t + a + d);
    env(g, t, a, vol, d);
    o.connect(g).connect(dest);
    o.start(t);
    o.stop(t + a + d + 0.05);
    return o;
  }

  function noise({ t = now(), a = 0.01, d = 0.3, vol = 0.3, type = "bandpass", f = 1000, f2 = null, q = 1, dest = master } = {}) {
    const s = ctx.createBufferSource();
    s.buffer = noiseBuf;
    const fl = ctx.createBiquadFilter();
    fl.type = type;
    fl.frequency.setValueAtTime(f, t);
    if (f2) fl.frequency.exponentialRampToValueAtTime(f2, t + a + d);
    fl.Q.value = q;
    const g = ctx.createGain();
    env(g, t, a, vol, d);
    s.connect(fl).connect(g).connect(dest);
    s.start(t, Math.random());
    s.stop(t + a + d + 0.05);
  }

  const S = {
    init,
    get muted() { return muted; },
    setMuted(m) {
      muted = m;
      if (master) master.gain.setTargetAtTime(m ? 0 : 0.8, now(), 0.05);
    },
    toggleMute() { S.setMuted(!muted); return muted; },

    // Barrido de aire para las transiciones
    whoosh(strength = 1) {
      if (!ok()) return;
      const t = now();
      noise({ t, a: 0.18, d: 0.55, vol: 0.22 * strength, f: 300, f2: 4000, q: 0.8 });
      noise({ t: t + 0.05, a: 0.2, d: 0.5, vol: 0.12 * strength, type: "lowpass", f: 2000, f2: 200 });
    },
    // Golpe grave cinematográfico
    boom(vol = 0.7) {
      if (!ok()) return;
      const t = now();
      tone(90, { t, a: 0.005, d: 1.4, vol, to: 28 });
      tone(45, { t, a: 0.01, d: 1.8, vol: vol * 0.6, type: "triangle", to: 25 });
      noise({ t, a: 0.002, d: 0.25, vol: 0.25, type: "lowpass", f: 900, f2: 100 });
    },
    // Brillo mágico (revelaciones)
    shimmer() {
      if (!ok()) return;
      const t = now();
      [1318.5, 1567.98, 2093, 2637].forEach((f, i) =>
        tone(f, { t: t + i * 0.06, a: 0.005, d: 0.9, vol: 0.07, type: "sine" }));
      noise({ t, a: 0.3, d: 0.8, vol: 0.05, type: "highpass", f: 6000, q: 0.5 });
    },
    // Aparición de un elemento
    pop() {
      if (!ok()) return;
      tone(520, { a: 0.003, d: 0.12, vol: 0.12, to: 980, type: "sine" });
    },
    // Impacto de revelación "¡SON IGUALES!"
    reveal() {
      if (!ok()) return;
      S.boom(0.5);
      S.shimmer();
    },
    glitch() {
      if (!ok()) return;
      const t = now();
      for (let i = 0; i < 6; i++) {
        tone(200 + Math.random() * 1800, { t: t + i * 0.035, a: 0.002, d: 0.03, vol: 0.06, type: "square" });
      }
      noise({ t, a: 0.002, d: 0.2, vol: 0.12, type: "highpass", f: 3000 });
    },
    tick(high = false) {
      if (!ok()) return;
      tone(high ? 1600 : 1100, { a: 0.001, d: 0.05, vol: high ? 0.18 : 0.1, type: "square" });
    },
    correct() {
      if (!ok()) return;
      const t = now();
      [523.25, 659.25, 783.99, 1046.5].forEach((f, i) =>
        tone(f, { t: t + i * 0.09, a: 0.005, d: 0.4, vol: 0.14, type: "triangle" }));
    },
    wrong() {
      if (!ok()) return;
      const t = now();
      tone(220, { t, a: 0.005, d: 0.35, vol: 0.12, type: "sawtooth", to: 140 });
      tone(160, { t: t + 0.18, a: 0.005, d: 0.45, vol: 0.12, type: "sawtooth", to: 90 });
    },
    // Golpe de tambor + platillo
    hit() {
      if (!ok()) return;
      const t = now();
      tone(150, { t, a: 0.002, d: 0.5, vol: 0.6, to: 50 });
      noise({ t, a: 0.002, d: 1.4, vol: 0.18, type: "highpass", f: 5000, q: 0.3 });
    },
    drumroll(seconds = 2.5) {
      if (!ok()) return;
      const t = now();
      const n = Math.floor(seconds * 22);
      for (let i = 0; i < n; i++) {
        const k = i / n;
        noise({ t: t + i * (seconds / n), a: 0.002, d: 0.06, vol: 0.05 + k * 0.2, type: "bandpass", f: 1800, q: 0.7 });
      }
    },
    fanfare() {
      if (!ok()) return;
      const t = now();
      const notes = [[523.25, 0], [659.25, 0.15], [783.99, 0.3], [1046.5, 0.45]];
      notes.forEach(([f, dt]) => {
        tone(f, { t: t + dt, a: 0.02, d: 0.35, vol: 0.12, type: "sawtooth" });
        tone(f / 2, { t: t + dt, a: 0.02, d: 0.35, vol: 0.08, type: "square" });
      });
      // acorde final largo
      [523.25, 659.25, 783.99, 1046.5, 261.63].forEach((f) =>
        tone(f, { t: t + 0.65, a: 0.03, d: 1.8, vol: 0.09, type: "sawtooth", detune: (Math.random() - 0.5) * 12 }));
      S.hit();
    },
    // Latido grave (suspenso)
    heartbeat() {
      if (!ok()) return;
      const t = now();
      tone(70, { t, a: 0.005, d: 0.18, vol: 0.5, to: 40 });
      tone(65, { t: t + 0.22, a: 0.005, d: 0.22, vol: 0.4, to: 38 });
    },

    // ---------------- MÚSICA ----------------
    stopMusic() {
      if (music) { music.stop(); music = null; }
    },
    // style: "lobby" (alegre), "question" (tensión), "ambient" (suave)
    playMusic(style) {
      if (!ok()) return;
      if (music && music.style === style) return;
      S.stopMusic();
      const bus = ctx.createGain();
      bus.gain.setValueAtTime(0.0001, now());
      bus.gain.exponentialRampToValueAtTime(1, now() + 1);
      bus.connect(musicBus);

      const bpm = style === "question" ? 128 : style === "lobby" ? 112 : 70;
      const step = 60 / bpm / 2; // corcheas
      // Am - F - C - G
      const prog = [
        [220, 261.63, 329.63], [174.61, 220, 261.63], [261.63, 329.63, 392], [196, 246.94, 293.66],
      ];
      const tense = [[220, 261.63, 329.63], [233.08, 277.18, 349.23]];
      let i = 0;
      let next = now() + 0.1;
      let speed = 1;
      const timer = setInterval(() => {
        while (next < now() + 0.25) {
          const chords = style === "question" ? tense : prog;
          const bar = Math.floor(i / 8) % chords.length;
          const ch = chords[bar];
          const pos = i % 8;
          if (style === "ambient") {
            if (pos === 0) ch.forEach((f) => tone(f / 2, { t: next, a: 1.2, d: 3.2, vol: 0.05, type: "sine", dest: bus }));
          } else if (style === "lobby") {
            if (pos % 2 === 0) tone(ch[0] / 2, { t: next, a: 0.01, d: 0.25, vol: 0.18, type: "triangle", dest: bus });
            const arp = [0, 1, 2, 1, 2, 0, 1, 2][pos];
            tone(ch[arp] * 2, { t: next, a: 0.005, d: 0.18, vol: 0.06, type: "square", dest: bus });
            if (pos === 4) { // caja
              const s = ctx.createBufferSource(); s.buffer = noiseBuf;
              const g = ctx.createGain(); env(g, next, 0.002, 0.08, 0.1);
              const f = ctx.createBiquadFilter(); f.type = "highpass"; f.frequency.value = 2500;
              s.connect(f).connect(g).connect(bus); s.start(next, Math.random()); s.stop(next + 0.15);
            }
            if (pos === 0) tone(60, { t: next, a: 0.003, d: 0.2, vol: 0.35, to: 40, dest: bus });
          } else {
            // tensión: bajo pulsante + tic
            tone(ch[0] / 4, { t: next, a: 0.005, d: 0.16, vol: 0.25, type: "sawtooth", dest: bus });
            if (pos % 2 === 1) tone(ch[(pos >> 1) % 3] * 2, { t: next, a: 0.003, d: 0.08, vol: 0.05, type: "square", dest: bus });
            if (pos === 0 || pos === 4) tone(55, { t: next, a: 0.003, d: 0.15, vol: 0.4, to: 35, dest: bus });
          }
          next += step / speed;
          i++;
        }
      }, 60);
      music = {
        style,
        setSpeed(s) { speed = s; },
        stop() {
          clearInterval(timer);
          const t = now();
          bus.gain.cancelScheduledValues(t);
          bus.gain.setValueAtTime(bus.gain.value, t);
          bus.gain.exponentialRampToValueAtTime(0.0001, t + 0.6);
          setTimeout(() => bus.disconnect(), 800);
        },
      };
    },
    musicSpeed(s) { if (music && music.setSpeed) music.setSpeed(s); },
  };

  window.SFX = S;
})();
