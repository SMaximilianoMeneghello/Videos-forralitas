// ============================================================
//  JUEGO (pantalla grande) — tipo Kahoot
// ============================================================
(function () {
  const Q = window.QUESTIONS;
  const SECS = (window.CONFIG && window.CONFIG.segundosPorPregunta) || 40;
  const COLORS = ["#ff3355", "#2f7bff", "#ffb800", "#22c55e"];
  const SHAPES = [
    '<svg viewBox="0 0 40 40"><path d="M20 4 L37 34 L3 34 Z" fill="#fff"/></svg>',
    '<svg viewBox="0 0 40 40"><path d="M20 2 L38 20 L20 38 L2 20 Z" fill="#fff"/></svg>',
    '<svg viewBox="0 0 40 40"><circle cx="20" cy="20" r="17" fill="#fff"/></svg>',
    '<svg viewBox="0 0 40 40"><rect x="4" y="4" width="32" height="32" rx="3" fill="#fff"/></svg>',
  ];
  const $ = (s, r = document) => r.querySelector(s);
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  let P = null; // API del presentador
  let layer = null;
  let active = false;
  let phase = "off"; // lobby | intro | question | reveal | board | podium
  let qi = -1;
  let qStart = 0;
  let answers = new Map(); // pid -> {a, ms}
  let timers = [];
  let rafStop = null;
  let podiumDone = false;
  const players = new Map(); // pid -> {pid, name, score, streak, cid, connected, last}
  const cidToPid = new Map();

  const later = (ms, fn) => { const id = setTimeout(fn, ms); timers.push(id); return id; };
  function clearTimers() { timers.forEach(clearTimeout); timers = []; if (rafStop) { rafStop(); rafStop = null; } }

  // ---------------------------------------------------------- utilidades de jugadores
  function ranking() {
    return Array.from(players.values()).sort((a, b) => b.score - a.score || a.name.localeCompare(b.name));
  }
  function rankOf(pid) { return ranking().findIndex((p) => p.pid === pid) + 1; }

  function sendTo(p, msg) { if (p.cid && p.connected) P.net.send(p.cid, msg); }

  function playerView(p) {
    const base = { t: "p", phase, name: p.name, score: p.score, total: Q.length, qi };
    if (phase === "lobby") return { ...base, count: players.size };
    if (phase === "intro") return base;
    if (phase === "question") {
      const q = Q[qi];
      return { ...base, q: q.q, options: q.a, endsIn: Math.max(0, SECS * 1000 - (Date.now() - qStart)), answered: answers.has(p.pid) };
    }
    if (phase === "reveal" || phase === "board") {
      const l = p.last || { correct: false, points: 0, answered: false };
      return { ...base, phase: "result", correct: l.correct, answered: l.answered, points: l.points, streak: p.streak, rank: rankOf(p.pid), players: players.size, correctText: Q[qi].a[Q[qi].ok] };
    }
    if (phase === "podium") {
      return { ...base, phase: "final", rank: rankOf(p.pid), players: players.size, top: ranking().slice(0, 3).map((x) => x.name), revealed: podiumDone };
    }
    return base;
  }

  function syncPlayers() { players.forEach((p) => sendTo(p, playerView(p))); }

  // ---------------------------------------------------------- mensajes de jugadores
  function playerMessage(cid, m) {
    if (m.t === "hello" && m.role === "player") {
      const p = m.pid && players.get(m.pid);
      if (p) {
        p.cid = cid; p.connected = true; cidToPid.set(cid, p.pid);
        sendTo(p, playerView(p));
        P.sendState();
      } else {
        P.net.send(cid, { t: "p", phase: active ? "name" : "closed" });
      }
      return;
    }
    if (m.t === "join") {
      if (!active) { P.net.send(cid, { t: "p", phase: "closed" }); return; }
      let name = String(m.name || "").replace(/\s+/g, " ").trim().slice(0, 15);
      if (!name) { P.net.send(cid, { t: "joinError", error: "Escribí un nombre" }); return; }
      const taken = Array.from(players.values()).some((p) => p.pid !== m.pid && p.name.toLowerCase() === name.toLowerCase());
      if (taken) { P.net.send(cid, { t: "joinError", error: "Ese nombre ya está en uso" }); return; }
      let p = players.get(m.pid);
      if (!p) {
        p = { pid: m.pid, name, score: 0, streak: 0, cid, connected: true, last: null };
        players.set(m.pid, p);
        addLobbyName(p);
        SFX.pop();
      } else { p.cid = cid; p.connected = true; }
      cidToPid.set(cid, p.pid);
      P.net.send(cid, { t: "joined", name: p.name });
      updateCounts();
      syncPlayers();
      P.sendState();
      return;
    }
    if (m.t === "answer") {
      const pid = cidToPid.get(cid);
      const p = pid && players.get(pid);
      if (!p || phase !== "question" || m.qi !== qi || answers.has(pid)) return;
      const a = m.a | 0;
      if (a < 0 || a > 3) return;
      answers.set(pid, { a, ms: Date.now() - qStart });
      sendTo(p, playerView(p));
      updateCounts();
      P.sendState();
      const connected = Array.from(players.values()).filter((x) => x.connected).length;
      if (answers.size >= Math.max(1, connected)) later(600, endQuestion);
    }
  }

  function playerClosed(cid) {
    const pid = cidToPid.get(cid);
    cidToPid.delete(cid);
    const p = pid && players.get(pid);
    if (p && p.cid === cid) {
      p.connected = false;
      const chip = layer.querySelector(`.lobby-chip[data-pid="${CSS.escape(pid)}"]`);
      if (chip) chip.classList.add("off");
      P.sendState();
    }
  }

  // ---------------------------------------------------------- pantallas
  function screen(html, cls) {
    layer.innerHTML = `<div class="g-screen ${cls || ""}">${html}</div>`;
    return layer.firstElementChild;
  }

  function openLobby() {
    phase = "lobby";
    qi = -1;
    podiumDone = false;
    const el = screen(`
      <div class="lobby">
        <div class="lobby-left">
          <div class="kicker g-in">El juego final</div>
          <h1 class="g-title g-in" data-letters>¿QUIÉN TIENE EL<br><span class="accent">CEREBRO MÁS RÁPIDO?</span></h1>
          <ol class="lobby-steps g-in">
            <li><b>1</b> Escaneá el QR con el celu</li>
            <li><b>2</b> Escribí tu nombre</li>
            <li><b>3</b> Mirá la pantalla y respondé rápido</li>
          </ol>
          <div class="lobby-rules g-in">⏱ ${SECS} segundos por pregunta · ⚡ más rápido = más puntos · 🔥 rachas suman extra</div>
        </div>
        <div class="lobby-right g-in">
          <div class="qr-card"><div class="join-qr"></div></div>
          <div class="join-code">Código <b class="room-code"></b></div>
          <div class="join-url"></div>
        </div>
      </div>
      <div class="lobby-bottom">
        <div class="lobby-count"><span class="num">0</span> jugadores</div>
        <div class="lobby-names"></div>
      </div>`, "g-lobby");
    refreshJoin();
    P.splitLetters(el.querySelector("[data-letters]"));
    gsap.fromTo(el.querySelectorAll(".g-in"), { opacity: 0, y: 50 }, { opacity: 1, y: 0, stagger: 0.12, duration: 1.2, ease: "expo.out", delay: 0.2 });
    gsap.fromTo(el.querySelectorAll(".g-title .ch"), { opacity: 0, y: 60, rotationX: -90 }, { opacity: 1, y: 0, rotationX: 0, stagger: 0.03, duration: 1.3, ease: "expo.out", delay: 0.4, transformPerspective: 600 });
    players.forEach((p) => addLobbyName(p, true));
    updateCounts();
    SFX.playMusic("lobby");
    syncPlayers();
    P.sendState();
  }

  function refreshJoin() {
    if (!layer) return;
    const qr = layer.querySelector(".join-qr");
    if (qr) qr.innerHTML = P.qrSvg(P.playUrl());
    layer.querySelectorAll(".room-code").forEach((e) => (e.textContent = P.room));
    const u = layer.querySelector(".join-url");
    if (u) u.textContent = P.playUrl().replace(/^https?:\/\//, "");
  }

  function addLobbyName(p, instant) {
    const box = layer && layer.querySelector(".lobby-names");
    if (!box || box.querySelector(`[data-pid="${CSS.escape(p.pid)}"]`)) return;
    const chip = document.createElement("div");
    chip.className = "lobby-chip" + (p.connected ? "" : " off");
    chip.dataset.pid = p.pid;
    chip.style.setProperty("--c", COLORS[players.size % 4]);
    chip.textContent = p.name;
    box.appendChild(chip);
    if (!instant) {
      gsap.fromTo(chip, { scale: 0, rotation: (Math.random() - 0.5) * 40 }, { scale: 1, rotation: (Math.random() - 0.5) * 6, duration: 0.7, ease: "back.out(3)" });
      gsap.to(chip, { y: -6, duration: 1.4 + Math.random(), yoyo: true, repeat: -1, ease: "sine.inOut", delay: 0.7 });
    }
  }

  function removeLobbyName(pid) {
    const chip = layer && layer.querySelector(`.lobby-chip[data-pid="${CSS.escape(pid)}"]`);
    if (chip) gsap.to(chip, { scale: 0, opacity: 0, duration: 0.3, onComplete: () => chip.remove() });
  }

  function updateCounts() {
    if (!layer) return;
    const n = layer.querySelector(".lobby-count .num");
    if (n) n.textContent = players.size;
    const a = layer.querySelector(".q-answered .num");
    if (a) {
      a.textContent = answers.size;
      gsap.fromTo(a, { scale: 1.5 }, { scale: 1, duration: 0.4, ease: "back.out(3)" });
    }
  }

  function startGame() {
    if (!players.size) { P.toast("⏳ Todavía no entró ningún jugador"); return; }
    players.forEach((p) => { p.score = 0; p.streak = 0; p.last = null; });
    qi = -1;
    nextQuestion();
  }

  function nextQuestion() {
    clearTimers();
    qi++;
    if (qi >= Q.length) { podium(); return; }
    phase = "intro";
    answers = new Map();
    SFX.stopMusic();
    const el = screen(`
      <div class="q-intro">
        <div class="qi-ring"></div>
        <div class="qi-label">Pregunta</div>
        <div class="qi-num"><span>${qi + 1}</span><small>/${Q.length}</small></div>
        <div class="qi-q">${esc(Q[qi].q)}</div>
      </div>`, "g-intro");
    gsap.fromTo(el.querySelector(".qi-ring"), { scale: 0, opacity: 1 }, { scale: 3, opacity: 0, duration: 1.6, ease: "expo.out" });
    gsap.fromTo(el.querySelector(".qi-num"), { scale: 3, opacity: 0, ...(P.lite ? {} : { filter: "blur(20px)" }) }, { scale: 1, opacity: 1, ...(P.lite ? {} : { filter: "blur(0px)" }), duration: 0.9, ease: "expo.out" });
    gsap.fromTo(el.querySelector(".qi-label"), { opacity: 0, y: -30 }, { opacity: 1, y: 0, duration: 0.8, delay: 0.2 });
    gsap.fromTo(el.querySelector(".qi-q"), { opacity: 0, y: 40 }, { opacity: 1, y: 0, duration: 1, delay: 0.7, ease: "expo.out" });
    SFX.boom(0.5); SFX.whoosh(1);
    syncPlayers();
    P.sendState();
    later(3600, showQuestion);
  }

  function showQuestion() {
    clearTimers();
    phase = "question";
    const q = Q[qi];
    const el = screen(`
      <div class="q-top"><div class="q-num">${qi + 1} / ${Q.length}</div><div class="q-text">${esc(q.q)}</div></div>
      <div class="q-mid">
        <div class="q-timer">
          <svg viewBox="0 0 240 240"><circle cx="120" cy="120" r="104" class="t-bg"/><circle cx="120" cy="120" r="104" class="t-fg"/></svg>
          <div class="t-num">${SECS}</div>
        </div>
        <div class="q-brain">🧠</div>
        <div class="q-answered"><span class="num">0</span><small>respuestas</small></div>
      </div>
      <div class="q-grid">
        ${q.a.map((t, i) => `<div class="q-opt" style="--c:${COLORS[i]}"><span class="shape">${SHAPES[i]}</span><span class="txt">${esc(t)}</span></div>`).join("")}
      </div>`, "g-question");
    gsap.fromTo(el.querySelector(".q-top"), { y: -80, opacity: 0 }, { y: 0, opacity: 1, duration: 0.9, ease: "expo.out" });
    gsap.fromTo(el.querySelectorAll(".q-opt"), { scale: 0.6, opacity: 0, y: 60 }, { scale: 1, opacity: 1, y: 0, stagger: 0.08, duration: 0.8, ease: "back.out(1.8)", delay: 0.2 });
    gsap.fromTo(el.querySelector(".q-timer"), { scale: 0, rotation: -90 }, { scale: 1, rotation: 0, duration: 0.9, ease: "back.out(2)", delay: 0.1 });
    gsap.to(el.querySelector(".q-brain"), { scale: 1.12, duration: 0.6, yoyo: true, repeat: -1, ease: "sine.inOut" });
    qStart = Date.now();
    SFX.playMusic("question");
    syncPlayers();
    P.sendState();

    const C = 2 * Math.PI * 104;
    const fg = el.querySelector(".t-fg");
    const num = el.querySelector(".t-num");
    const timerBox = el.querySelector(".q-timer");
    fg.style.strokeDasharray = C;
    let lastSec = SECS;
    let on = true;
    const loop = () => {
      if (!on) return;
      const left = Math.max(0, SECS * 1000 - (Date.now() - qStart));
      fg.style.strokeDashoffset = C * (1 - left / (SECS * 1000));
      const sec = Math.ceil(left / 1000);
      if (sec !== lastSec) {
        lastSec = sec;
        num.textContent = sec;
        if (sec <= 10 && sec > 0) {
          timerBox.classList.add("danger");
          SFX.tick(sec <= 5);
          gsap.fromTo(num, { scale: 1.45 }, { scale: 1, duration: 0.5, ease: "back.out(3)" });
          if (sec === 10) SFX.musicSpeed(1.35);
        }
      }
      if (left <= 0) { endQuestion(); return; }
      requestAnimationFrame(loop);
    };
    requestAnimationFrame(loop);
    rafStop = () => { on = false; };
  }

  function score(ms) {
    // 1000 puntos si responde al instante, 500 si responde en el último segundo
    const k = Math.min(1, ms / (SECS * 1000));
    return Math.round(1000 - 500 * k);
  }

  function endQuestion() {
    if (phase !== "question") return;
    clearTimers();
    phase = "reveal";
    SFX.stopMusic();
    SFX.musicSpeed(1);
    const q = Q[qi];
    const counts = [0, 0, 0, 0];
    players.forEach((p) => {
      const ans = answers.get(p.pid);
      if (ans) counts[ans.a]++;
      const correct = !!ans && ans.a === q.ok;
      let pts = 0;
      if (correct) {
        p.streak++;
        pts = score(ans.ms) + (p.streak >= 2 ? 100 * (p.streak - 1) : 0);
      } else p.streak = 0;
      p.score += pts;
      p.last = { correct, points: pts, answered: !!ans };
    });

    const el = layer.querySelector(".g-question");
    el.classList.add("revealing");
    const timer = el.querySelector(".q-timer");
    const mid = el.querySelector(".q-mid");
    const max = Math.max(1, ...counts);
    const bars = document.createElement("div");
    bars.className = "q-bars";
    bars.innerHTML = counts.map((c, i) => `
      <div class="bar ${i === q.ok ? "ok" : ""}" style="--c:${COLORS[i]}">
        <div class="bar-n">${c}</div>
        <div class="bar-fill" style="--k:${c / max}"></div>
        <div class="bar-ico">${SHAPES[i]}${i === q.ok ? '<b class="tick">✓</b>' : ""}</div>
      </div>`).join("");
    gsap.to([timer, mid.querySelector(".q-brain"), mid.querySelector(".q-answered")], { opacity: 0, scale: 0.6, duration: 0.4 });
    mid.appendChild(bars);
    gsap.fromTo(bars.querySelectorAll(".bar-fill"), { scaleY: 0 }, { scaleY: 1, duration: 1.2, stagger: 0.1, ease: "expo.out", delay: 0.3 });
    gsap.fromTo(bars.querySelectorAll(".bar-n"), { opacity: 0, y: 20 }, { opacity: 1, y: 0, stagger: 0.1, delay: 0.8 });
    el.querySelectorAll(".q-opt").forEach((o, i) => {
      if (i === q.ok) {
        o.classList.add("correct");
        o.insertAdjacentHTML("beforeend", '<span class="ok-badge">✓</span>');
        gsap.fromTo(o, { scale: 1 }, { scale: 1.06, duration: 0.5, ease: "back.out(3)", yoyo: true, repeat: 1 });
      } else gsap.to(o, { opacity: 0.25, scale: 0.94, ...(P.lite ? {} : { filter: "grayscale(0.8)" }), duration: 0.6 });
    });
    SFX.correct();
    P.flash(0.25, 0.6);
    syncPlayers();
    P.sendState();
  }

  function board() {
    clearTimers();
    phase = "board";
    const r = ranking();
    const top = r.slice(0, 5);
    const last = qi >= Q.length - 1;
    const el = screen(`
      <div class="board">
        <div class="kicker">Después de la pregunta ${qi + 1} de ${Q.length}</div>
        <h1 class="g-title small">🏆 Ranking</h1>
        <div class="b-list">
          ${top.map((p, i) => `
            <div class="b-row ${i === 0 ? "first" : ""}">
              <div class="b-pos">${i + 1}</div>
              <div class="b-name">${esc(p.name)}${p.streak >= 2 ? ` <span class="streak">🔥${p.streak}</span>` : ""}</div>
              <div class="b-delta">${p.last && p.last.points ? "+" + p.last.points : ""}</div>
              <div class="b-score" data-to="${p.score}">${p.score - ((p.last && p.last.points) || 0)}</div>
            </div>`).join("")}
        </div>
        <div class="b-hint">${last ? "Se viene el PODIO…" : "Prepárense para la siguiente…"}</div>
      </div>`, "g-board");
    gsap.fromTo(el.querySelectorAll(".b-row"), { x: -200, opacity: 0 }, { x: 0, opacity: 1, stagger: 0.12, duration: 0.9, ease: "expo.out", delay: 0.2 });
    el.querySelectorAll(".b-score").forEach((s) => {
      const o = { v: parseInt(s.textContent, 10) };
      gsap.to(o, { v: parseInt(s.dataset.to, 10), duration: 1.6, delay: 0.8, ease: "power2.out", onUpdate: () => (s.textContent = Math.round(o.v).toLocaleString("es-AR")) });
    });
    gsap.fromTo(el.querySelector(".g-title"), { scale: 0.6, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.8, ease: "back.out(2)" });
    SFX.whoosh(0.8);
    SFX.playMusic("lobby");
    syncPlayers();
    P.sendState();
  }

  function podium() {
    clearTimers();
    phase = "podium";
    podiumDone = false;
    SFX.stopMusic();
    const r = ranking();
    const p1 = r[0], p2 = r[1], p3 = r[2];
    const col = (p, place) => p ? `
      <div class="pod p${place}">
        <div class="pod-who"><div class="pod-medal">${["🥇", "🥈", "🥉"][place - 1]}</div><div class="pod-name">${esc(p.name)}</div><div class="pod-score">${p.score.toLocaleString("es-AR")} pts</div></div>
        <div class="pod-block"><span>${place}</span></div>
      </div>` : `<div class="pod p${place} empty"><div class="pod-block"><span>${place}</span></div></div>`;
    const el = screen(`
      <div class="spot s1"></div><div class="spot s2"></div><div class="spot s3"></div>
      <div class="pod-title">Y los cerebros más rápidos son…</div>
      <div class="podium">${col(p2, 2)}${col(p1, 1)}${col(p3, 3)}</div>
      <div class="rest">${r.slice(3, 12).map((p, i) => `<div class="rest-row"><b>${i + 4}</b><span>${esc(p.name)}</span><i>${p.score.toLocaleString("es-AR")}</i></div>`).join("")}</div>`, "g-podium");
    gsap.set(el.querySelectorAll(".pod"), { opacity: 0 });
    gsap.fromTo(el.querySelector(".pod-title"), { opacity: 0, scale: 0.8 }, { opacity: 1, scale: 1, duration: 1.2, ease: "expo.out" });
    gsap.fromTo(el.querySelectorAll(".spot"), { opacity: 0 }, { opacity: 0.6, duration: 2, stagger: 0.3 });
    gsap.to(el.querySelectorAll(".spot"), { rotation: "+=18", duration: 2.2, yoyo: true, repeat: -1, ease: "sine.inOut", stagger: 0.4 });
    syncPlayers();
    P.sendState();

    const rise = (place) => {
      const p = el.querySelector(".pod.p" + place);
      gsap.set(p, { opacity: 1 });
      gsap.fromTo(p.querySelector(".pod-block"), { scaleY: 0 }, { scaleY: 1, duration: 1, ease: "expo.out", transformOrigin: "50% 100%" });
      const who = p.querySelector(".pod-who");
      if (who) gsap.fromTo(who, { opacity: 0, y: 80, scale: 0.5 }, { opacity: 1, y: 0, scale: 1, duration: 1, delay: 0.35, ease: "back.out(2)" });
      SFX.hit();
      P.shake(place === 1 ? 18 : 8);
    };
    SFX.drumroll(2.4);
    later(2500, () => rise(3));
    later(4300, () => { SFX.drumroll(2.6); });
    later(4400, () => rise(2));
    later(7300, () => { SFX.drumroll(3); SFX.heartbeat(); });
    later(10400, () => {
      rise(1);
      SFX.fanfare();
      P.flash(0.9, 1.4);
      confettiShow();
      podiumDone = true;
      syncPlayers();
      P.sendState();
      later(2500, () => {
        gsap.fromTo(el.querySelectorAll(".rest-row"), { opacity: 0, x: 80 }, { opacity: 1, x: 0, stagger: 0.08, duration: 0.7, ease: "expo.out" });
        SFX.playMusic("lobby");
      });
    });
  }

  function confettiShow() {
    if (typeof confetti !== "function") return;
    const colors = ["#8b5cf6", "#22d3ee", "#ec4899", "#ffd84a", "#ffffff"];
    const end = Date.now() + (P.lite ? 1500 : 4500);
    confetti({ particleCount: P.lite ? 80 : 220, spread: 110, startVelocity: 60, origin: { y: 0.65 }, colors, zIndex: 50 });
    (function frame() {
      confetti({ particleCount: 4, angle: 60, spread: 60, origin: { x: 0, y: 0.7 }, colors, zIndex: 50 });
      confetti({ particleCount: 4, angle: 120, spread: 60, origin: { x: 1, y: 0.7 }, colors, zIndex: 50 });
      if (Date.now() < end) timers.push(setTimeout(frame, 60));
    })();
  }

  // ---------------------------------------------------------- control
  function open() {
    if (active) return;
    active = true;
    layer.classList.add("on");
    P.hideSlides();
    gsap.fromTo(layer, { opacity: 0, scale: 1.1 }, { opacity: 1, scale: 1, duration: 1, ease: "expo.out" });
    window.BG && BG.burst(1);
    SFX.boom(0.6);
    openLobby();
    P.updateHud();
  }

  function close() {
    if (!active) return;
    clearTimers();
    SFX.stopMusic();
    active = false;
    phase = "off";
    gsap.to(layer, { opacity: 0, duration: 0.5, onComplete: () => { layer.classList.remove("on"); layer.innerHTML = ""; } });
    syncPlayers();
    P.backToSlides();
  }

  function next() {
    if (phase === "lobby") startGame();
    else if (phase === "intro") showQuestion();
    else if (phase === "question") endQuestion();
    else if (phase === "reveal") board();
    else if (phase === "board") nextQuestion();
    else if (phase === "podium" && !podiumDone) {
      // saltear el suspenso
      clearTimers();
      const el = layer.querySelector(".g-podium");
      el.querySelectorAll(".pod").forEach((p) => gsap.set(p, { opacity: 1 }));
      el.querySelectorAll(".pod-who, .pod-block").forEach((p) => gsap.set(p, { opacity: 1, y: 0, scale: 1, scaleY: 1 }));
      gsap.set(el.querySelectorAll(".rest-row"), { opacity: 1, x: 0 });
      SFX.fanfare(); confettiShow();
      podiumDone = true;
      syncPlayers(); P.sendState();
    }
  }

  function prev() { if (phase === "lobby") close(); }

  function command(m) {
    switch (m.c) {
      case "game-open": if (P.started) open(); break;
      case "game-close": close(); break;
      case "game-start": if (phase === "lobby") startGame(); break;
      case "game-skip": if (phase === "question") endQuestion(); else if (phase === "intro") showQuestion(); break;
      case "game-reset":
        players.forEach((p) => { p.score = 0; p.streak = 0; p.last = null; });
        clearTimers(); SFX.stopMusic();
        openLobby();
        break;
      case "kick": {
        const p = players.get(m.pid);
        if (p) {
          if (p.cid) { P.net.send(p.cid, { t: "kicked" }); cidToPid.delete(p.cid); }
          players.delete(m.pid);
          removeLobbyName(m.pid);
          updateCounts();
          syncPlayers();
          P.sendState();
        }
        break;
      }
    }
  }

  function nextLabel() {
    switch (phase) {
      case "lobby": return players.size ? `▶ COMENZAR (${players.size})` : "Esperando jugadores…";
      case "intro": return "▶ MOSTRAR OPCIONES";
      case "question": return "⏭ TERMINAR TIEMPO";
      case "reveal": return "🏆 VER RANKING";
      case "board": return qi >= Q.length - 1 ? "🥇 ¡PODIO!" : "▶ SIGUIENTE PREGUNTA";
      case "podium": return podiumDone ? "🎉 ¡Terminado!" : "⏭ SALTEAR SUSPENSO";
      default: return "";
    }
  }

  function remoteState() {
    const q = qi >= 0 && qi < Q.length ? Q[qi] : null;
    return {
      active, phase, qi, total: Q.length,
      answered: answers.size,
      question: q ? q.q : "",
      correct: q && (phase === "reveal" || phase === "board") ? q.a[q.ok] : "",
      nextLabel: nextLabel(),
      players: ranking().map((p) => ({ pid: p.pid, name: p.name, score: p.score, on: p.connected, ans: answers.has(p.pid) })),
    };
  }

  window.GAME = {
    init(api) {
      P = api;
      layer = document.getElementById("game");
      P.hideSlides = P.hideSlides || (() => {});
    },
    open, close, next, prev, command, playerMessage, playerClosed, remoteState, refreshJoin,
    get active() { return active; },
  };
})();
