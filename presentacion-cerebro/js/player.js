// ============================================================
//  JUGADOR (celular de cada compañero)
// ============================================================
(function () {
  const $ = (s) => document.querySelector(s);
  const app = $("#app");
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const room = (NET.params.get("r") || "").toUpperCase();
  const SHAPES = [
    '<svg viewBox="0 0 40 40"><path d="M20 4 L37 34 L3 34 Z" fill="#fff"/></svg>',
    '<svg viewBox="0 0 40 40"><path d="M20 2 L38 20 L20 38 L2 20 Z" fill="#fff"/></svg>',
    '<svg viewBox="0 0 40 40"><circle cx="20" cy="20" r="17" fill="#fff"/></svg>',
    '<svg viewBox="0 0 40 40"><rect x="4" y="4" width="32" height="32" rx="3" fill="#fff"/></svg>',
  ];
  const ls = {
    get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} },
  };
  const PID_KEY = "tcm.pid." + room;
  // ?pid=... solo sirve para probar varios jugadores en la misma compu
  let pid = NET.params.get("pid") || ls.get(PID_KEY);
  if (!pid) { pid = NET.uid(); ls.set(PID_KEY, pid); }

  let joined = false;
  let myName = ls.get("tcm.name") || "";
  let view = ""; // clave de la pantalla actual, para no redibujar de más
  let qTimer = null;
  let last = null;

  const buzz = (p) => { try { navigator.vibrate && navigator.vibrate(p); } catch (e) {} };

  function set(key, html) {
    if (view === key) return false;
    view = key;
    clearInterval(qTimer);
    app.className = "view center-view";
    app.innerHTML = html;
    app.animate && app.firstElementChild && app.firstElementChild.animate(
      [{ opacity: 0, transform: "translateY(16px) scale(.98)" }, { opacity: 1, transform: "none" }],
      { duration: 380, easing: "cubic-bezier(.16,1,.3,1)" });
    return true;
  }

  if (!room) {
    set("noroom", `<div class="big-emoji">🤔</div><div class="title" style="font-size:24px">Falta el código del juego</div><div class="muted">Escaneá el QR de la pantalla grande o pedí el enlace.</div>`);
    return;
  }

  const link = NET.join({
    room, role: "player",
    onStatus(s) {
      $("#dot").className = "dot" + (s === "connected" ? " on" : s === "error" ? " off" : "");
      if (s === "nohost" && !joined) set("nohost", `<div class="spinner"></div><div class="title" style="font-size:22px">Buscando el juego…</div><div class="muted">Puede que la presentación todavía no esté abierta. Reintentando solo.</div>`);
    },
    onOpen() { link.send({ t: "hello", role: "player", pid }); },
    onClose() {
      if (joined) $("#brand").textContent = "🔄 Reconectando…";
    },
    onMessage(m) {
      $("#brand").textContent = "🧠 Tu cerebro te miente";
      if (m.t === "p") handle(m);
      else if (m.t === "joined") { joined = true; myName = m.name; ls.set("tcm.name", m.name); }
      else if (m.t === "joinError") {
        const e = $("#join-err"); if (e) e.textContent = m.error;
        const b = $("#join-btn"); if (b) b.disabled = false;
        buzz(150);
      } else if (m.t === "kicked") {
        joined = false;
        set("kicked", `<div class="big-emoji">🚫</div><div class="title" style="font-size:24px">Te sacaron del juego</div><div class="muted">Si fue un error, avisale a quien presenta.</div>`);
        ls.set(PID_KEY, NET.uid());
      }
    },
  });

  function nameForm() {
    if (!set("name", `
      <div class="big-emoji">🧠</div>
      <div class="title" style="font-size:30px">¿Quién tiene el cerebro más rápido?</div>
      <div class="muted">Escribí tu nombre para entrar</div>
      <div class="p-form">
        <input class="p-name" id="name" maxlength="15" placeholder="Tu nombre" autocomplete="off" enterkeyhint="go" value="${esc(myName)}">
        <div class="err" id="join-err"></div>
        <button class="btn primary" id="join-btn">¡ENTRAR! 🚀</button>
      </div>`)) return;
    const go = () => {
      const v = $("#name").value.trim();
      if (!v) { $("#join-err").textContent = "Escribí un nombre"; return; }
      $("#join-btn").disabled = true;
      link.send({ t: "join", pid, name: v });
    };
    $("#join-btn").addEventListener("click", go);
    $("#name").addEventListener("keydown", (e) => { if (e.key === "Enter") go(); });
  }

  function handle(m) {
    if (m.score !== undefined && m.name) {
      const sc = $("#score");
      sc.classList.remove("hidden");
      sc.textContent = `${m.score.toLocaleString("es-AR")} pts`;
    }
    switch (m.phase) {
      case "closed":
        joined = false;
        set("closed", `<div class="big-emoji">⏳</div><div class="title" style="font-size:24px">El juego todavía no empezó</div><div class="muted">Cuando termine la exposición se abre la sala. Dejá esta página abierta: entra sola.</div>`);
        // vuelve a preguntar cada tanto
        setTimeout(() => { if (view === "closed") link.send({ t: "hello", role: "player", pid }); }, 4000);
        break;
      case "name": nameForm(); break;
      case "lobby":
        joined = true;
        set("lobby", `
          <div class="big-emoji">✅</div>
          <div class="p-hello">¡Ya estás adentro!</div>
          <div class="p-chip">${esc(m.name)}</div>
          <div class="muted" style="margin-top:10px">Mirá la pantalla grande.<br>El juego empieza en un ratito…</div>
          <div class="muted" style="font-size:13px;margin-top:18px">💡 Más rápido respondés, más puntos ganás</div>`);
        break;
      case "intro":
        if (set("intro" + m.qi, `
          <div class="p-qnum">Pregunta ${m.qi + 1} de ${m.total}</div>
          <div class="title" style="font-size:44px">¡Preparate!</div>
          <div class="spinner"></div>`)) buzz(30);
        break;
      case "question":
        if (m.answered) {
          set("answered" + m.qi, `<div class="big-emoji">🚀</div><div class="title" style="font-size:28px">¡Respuesta enviada!</div><div class="muted">Esperá a que termine el tiempo…</div>`);
        } else question(m);
        break;
      case "result": result(m); break;
      case "final": final(m); break;
    }
  }

  function question(m) {
    if (!set("q" + m.qi, `
      <div class="p-qnum">Pregunta ${m.qi + 1} de ${m.total}</div>
      <div class="q-bar" id="qbar"><i></i></div>
      <div class="p-qtext">${esc(m.q)}</div>
      <div class="answers">
        ${m.options.map((t, i) => `<button class="ans a${i}" data-a="${i}">${SHAPES[i]}<span>${esc(t)}</span></button>`).join("")}
      </div>`)) return;
    app.className = "view";
    buzz(40);
    const end = Date.now() + m.endsIn;
    const total = (CONFIG.segundosPorPregunta || 40) * 1000;
    const bar = $("#qbar i");
    qTimer = setInterval(() => {
      const left = Math.max(0, end - Date.now());
      bar.style.transform = `scaleX(${left / total})`;
      $("#qbar").classList.toggle("danger", left < 10000);
    }, 100);
    app.querySelectorAll(".ans").forEach((b) => b.addEventListener("click", () => {
      buzz(25);
      link.send({ t: "answer", qi: m.qi, a: parseInt(b.dataset.a, 10) });
      app.querySelectorAll(".ans").forEach((x) => { x.disabled = true; if (x !== b) x.style.opacity = 0.3; });
      b.style.transform = "scale(1.04)";
    }));
  }

  function result(m) {
    const key = "r" + m.qi;
    const cls = !m.answered ? "none" : m.correct ? "ok" : "bad";
    const title = !m.answered ? "⏰ ¡Se acabó el tiempo!" : m.correct ? "¡CORRECTO! 🎉" : "Incorrecto 😬";
    if (!set(key, `
      <div class="result ${cls}">
        <div class="big-emoji">${!m.answered ? "⌛" : m.correct ? "✅" : "❌"}</div>
        <div class="r-title">${title}</div>
        <div class="r-pts">+${m.points} pts</div>
        ${m.streak >= 2 ? `<div class="r-streak">🔥 Racha de ${m.streak}</div>` : ""}
        <div class="r-rank">Estás en el puesto <b>${m.rank}</b> de ${m.players}</div>
        ${!m.correct ? `<div class="r-correct">La correcta era: <b>${esc(m.correctText)}</b></div>` : ""}
      </div>`)) return;
    app.className = "view";
    buzz(m.correct ? [40, 60, 40] : 250);
    last = m;
  }

  function final(m) {
    const key = "final" + (m.revealed ? "1" : "0");
    if (!m.revealed) {
      set(key, `<div class="big-emoji">🥁</div><div class="title" style="font-size:30px">¡Mirá la pantalla!</div><div class="muted">Se viene el podio…</div>`);
      return;
    }
    const medal = ["🥇", "🥈", "🥉"][m.rank - 1];
    if (!set(key, `
      <div class="muted">Terminó el juego</div>
      <div class="big-emoji">${medal || "🧠"}</div>
      <div class="final-rank ${m.rank === 1 ? "gold" : ""}">${m.rank}°</div>
      <div class="title" style="font-size:22px">${m.rank === 1 ? "¡GANASTE! Cerebro supremo 👑" : m.rank <= 3 ? "¡Llegaste al podio!" : `de ${m.players} jugadores`}</div>
      <div class="p-chip">${m.score.toLocaleString("es-AR")} pts</div>
      <div class="top3">${m.top.map((n, i) => `<div>${["🥇", "🥈", "🥉"][i]} ${esc(n)}</div>`).join("")}</div>`)) return;
    if (m.rank <= 3 && typeof confetti === "function") {
      buzz([60, 40, 60, 40, 200]);
      const end = Date.now() + 2500;
      (function f() {
        confetti({ particleCount: 6, spread: 70, origin: { y: 0.3 } });
        if (Date.now() < end) setTimeout(f, 80);
      })();
    }
  }

  // reconecta enseguida si vuelven de otra app
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible" && link.connected) link.send({ t: "hello", role: "player", pid });
  });
})();
