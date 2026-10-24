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

  // 1 -> 1st, 2 -> 2nd, 3 -> 3rd, 4 -> 4th…
  const ordinal = (n) => { const t = n % 100; return n + (t >= 11 && t <= 13 ? "th" : ["th", "st", "nd", "rd"][n % 10] || "th"); };
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
    set("noroom", `<div class="big-emoji">🤔</div><div class="title" style="font-size:24px">The game code is missing</div><div class="muted">Scan the QR code on the big screen or ask for the link.</div>`);
    return;
  }

  const link = NET.join({
    room, role: "player",
    onStatus(s) {
      $("#dot").className = "dot" + (s === "connected" ? " on" : s === "error" ? " off" : "");
      if (s === "nohost" && !joined) set("nohost", `<div class="spinner"></div><div class="title" style="font-size:22px">Looking for the game…</div><div class="muted">The presentation may not be open yet. Trying again automatically.</div>`);
    },
    onOpen() { link.send({ t: "hello", role: "player", pid }); },
    onClose() {
      if (joined) $("#brand").textContent = "🔄 Reconnecting…";
    },
    onMessage(m) {
      $("#brand").textContent = "🧠 Your brain is lying to you";
      if (m.t === "p") handle(m);
      else if (m.t === "joined") { joined = true; myName = m.name; ls.set("tcm.name", m.name); }
      else if (m.t === "joinError") {
        const e = $("#join-err"); if (e) e.textContent = m.error;
        const b = $("#join-btn"); if (b) b.disabled = false;
        buzz(150);
      } else if (m.t === "kicked") {
        joined = false;
        set("kicked", `<div class="big-emoji">🚫</div><div class="title" style="font-size:24px">You were removed from the game</div><div class="muted">If it was a mistake, tell the presenter.</div>`);
        ls.set(PID_KEY, NET.uid());
      }
    },
  });

  function nameForm() {
    if (!set("name", `
      <div class="big-emoji">🧠</div>
      <div class="title" style="font-size:30px">Who has the fastest brain?</div>
      <div class="muted">Type your name to join</div>
      <div class="p-form">
        <input class="p-name" id="name" maxlength="15" placeholder="Your name" autocomplete="off" enterkeyhint="go" value="${esc(myName)}">
        <div class="err" id="join-err"></div>
        <button class="btn primary" id="join-btn">JOIN! 🚀</button>
      </div>`)) return;
    const go = () => {
      const v = $("#name").value.trim();
      if (!v) { $("#join-err").textContent = "Type a name"; return; }
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
      sc.textContent = `${m.score.toLocaleString("en-US")} pts`;
    }
    switch (m.phase) {
      case "closed":
        joined = false;
        set("closed", `<div class="big-emoji">⏳</div><div class="title" style="font-size:24px">The game hasn’t started yet</div><div class="muted">The game room opens when the presentation ends. Keep this page open: you’ll get in automatically.</div>`);
        // vuelve a preguntar cada tanto
        setTimeout(() => { if (view === "closed") link.send({ t: "hello", role: "player", pid }); }, 4000);
        break;
      case "name": nameForm(); break;
      case "lobby":
        joined = true;
        set("lobby", `
          <div class="big-emoji">✅</div>
          <div class="p-hello">You’re in!</div>
          <div class="p-chip">${esc(m.name)}</div>
          <div class="muted" style="margin-top:10px">Look at the big screen.<br>The game starts soon…</div>
          <div class="muted" style="font-size:13px;margin-top:18px">💡 The faster you answer, the more points you get</div>`);
        break;
      case "intro":
        if (set("intro" + m.qi, `
          <div class="p-qnum">Question ${m.qi + 1} of ${m.total}</div>
          <div class="title" style="font-size:44px">Get ready!</div>
          <div class="spinner"></div>`)) buzz(30);
        break;
      case "question":
        if (m.answered) {
          set("answered" + m.qi, `<div class="big-emoji">🚀</div><div class="title" style="font-size:28px">Answer sent!</div><div class="muted">Wait for the time to run out…</div>`);
        } else question(m);
        break;
      case "result": result(m); break;
      case "final": final(m); break;
    }
  }

  function question(m) {
    if (!set("q" + m.qi, `
      <div class="p-qnum">Question ${m.qi + 1} of ${m.total}</div>
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
    const title = !m.answered ? "⏰ Time’s up!" : m.correct ? "CORRECT! 🎉" : "Wrong 😬";
    if (!set(key, `
      <div class="result ${cls}">
        <div class="big-emoji">${!m.answered ? "⌛" : m.correct ? "✅" : "❌"}</div>
        <div class="r-title">${title}</div>
        <div class="r-pts">+${m.points} pts</div>
        ${m.streak >= 2 ? `<div class="r-streak">🔥 ${m.streak} in a row!</div>` : ""}
        <div class="r-rank">You are in <b>${ordinal(m.rank)}</b> place (of ${m.players})</div>
        ${!m.correct ? `<div class="r-correct">The correct answer was: <b>${esc(m.correctText)}</b></div>` : ""}
      </div>`)) return;
    app.className = "view";
    buzz(m.correct ? [40, 60, 40] : 250);
    last = m;
  }

  function final(m) {
    const key = "final" + (m.revealed ? "1" : "0");
    if (!m.revealed) {
      set(key, `<div class="big-emoji">🥁</div><div class="title" style="font-size:30px">Look at the screen!</div><div class="muted">Here comes the podium…</div>`);
      return;
    }
    const medal = ["🥇", "🥈", "🥉"][m.rank - 1];
    if (!set(key, `
      <div class="muted">Game over</div>
      <div class="big-emoji">${medal || "🧠"}</div>
      <div class="final-rank ${m.rank === 1 ? "gold" : ""}">${ordinal(m.rank)}</div>
      <div class="title" style="font-size:22px">${m.rank === 1 ? "YOU WON! Supreme brain 👑" : m.rank <= 3 ? "You made the podium!" : `out of ${m.players} players`}</div>
      <div class="p-chip">${m.score.toLocaleString("en-US")} pts</div>
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
