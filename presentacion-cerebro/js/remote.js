// ============================================================
//  CONTROL REMOTO (tu celular)
// ============================================================
(function () {
  const $ = (s) => document.querySelector(s);
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const room = (NET.params.get("r") || "").toUpperCase();
  const TOKEN_KEY = "tcm.remote." + room;
  const getToken = () => { try { return localStorage.getItem(TOKEN_KEY); } catch (e) { return null; } };
  const setToken = (t) => { try { localStorage.setItem(TOKEN_KEY, t); } catch (e) {} };

  let authed = false;
  let state = null;
  let elapsedBase = 0, elapsedAt = 0;
  const views = ["v-connect", "v-pin", "v-slides", "v-game"];
  function show(id) { views.forEach((v) => $("#" + v).classList.toggle("hidden", v !== id)); }

  if (!room) {
    $("#connect-msg").textContent = "Falta el código de sala. Escaneá el QR de la pantalla grande.";
    $(".spinner").style.display = "none";
    return;
  }

  const buzz = (ms = 18) => { try { navigator.vibrate && navigator.vibrate(ms); } catch (e) {} };

  // Mantener la pantalla prendida mientras exponés
  let wake = null;
  async function keepAwake() { try { if ("wakeLock" in navigator && !wake) { wake = await navigator.wakeLock.request("screen"); wake.addEventListener("release", () => (wake = null)); } } catch (e) {} }
  document.addEventListener("click", keepAwake, { once: false });
  document.addEventListener("visibilitychange", () => { if (document.visibilityState === "visible") keepAwake(); });

  const link = NET.join({
    room, role: "remote",
    onStatus(s) {
      const dot = $("#dot");
      dot.className = "dot" + (s === "connected" ? " on" : s === "error" ? " off" : "");
      if (s === "nohost") $("#connect-msg").textContent = "No encuentro la presentación. ¿Está abierta en la netbook? Reintentando…";
      if (s === "reconnecting" && authed) $("#brand").textContent = "🔄 Reconectando…";
    },
    onOpen() {
      $("#brand").textContent = "🧠 Control remoto";
      link.send({ t: "hello", role: "remote", token: getToken() });
    },
    onClose() { if (!authed) show("v-connect"); },
    onMessage(m) {
      if (m.t === "auth") {
        if (m.ok) {
          authed = true;
          if (m.token) setToken(m.token);
          buzz(40);
        } else {
          authed = false;
          show("v-pin");
          $("#pin-err").textContent = m.bad ? (m.pairing ? "PIN incorrecto. Probá de nuevo." : "El control ya está emparejado. Apretá P en la netbook para conectar otro.") : (m.pairing ? "" : "Apretá P en la netbook para mostrar el PIN.");
          if (m.bad) { buzz(120); $("#pin").value = ""; }
          setTimeout(() => $("#pin").focus(), 100);
        }
      } else if (m.t === "state") {
        state = m;
        elapsedBase = m.elapsed; elapsedAt = Date.now();
        render();
      }
    },
  });

  // ---------- PIN ----------
  function sendPin() {
    const v = $("#pin").value.replace(/\D/g, "");
    if (v.length !== 4) { $("#pin-err").textContent = "Son 4 números"; return; }
    link.send({ t: "pin", pin: v });
  }
  $("#pin-btn").addEventListener("click", sendPin);
  $("#pin").addEventListener("input", () => { if ($("#pin").value.replace(/\D/g, "").length === 4) sendPin(); });

  const cmd = (c, extra) => { if (!authed) return; buzz(); link.send({ t: "cmd", c, ...(extra || {}) }); };

  // ---------- render ----------
  function render() {
    if (!state || !authed) return;
    $("#mute-btn").textContent = state.muted ? "🔇" : "🔊";
    if (state.mode === "game") { show("v-game"); renderGame(state.game); }
    else { show("v-slides"); renderSlides(); }
  }

  function renderSlides() {
    const s = state.slide;
    if (!state.started) {
      $("#s-num").textContent = "Listo para empezar";
      $("#s-title").textContent = "Tocá COMENZAR";
      $("#s-notes").innerHTML = "Lo ideal es tocar <b>COMENZAR</b> en la netbook (así se pone en pantalla completa). Si ya está todo listo, también podés empezar desde acá.";
      $("#s-steps").innerHTML = "";
      $("#s-next").textContent = state.list[0] || "";
      $("#next-sub").textContent = "COMENZAR";
      return;
    }
    $("#s-num").textContent = `Diapositiva ${s.i + 1} de ${s.n}`;
    $("#s-title").textContent = s.title;
    $("#s-notes").textContent = s.notes;
    let dots = "";
    for (let k = 1; k <= s.steps; k++) dots += `<i class="${k <= s.step ? "done" : ""}"></i>`;
    $("#s-steps").innerHTML = dots;
    const more = s.step < s.steps;
    $("#next-sub").textContent = more ? `PASO ${s.step + 1}/${s.steps}` : "SIGUIENTE";
    $("#s-next").textContent = more ? "(misma diapositiva, sigue la animación)" : s.next;
    $("#lite-btn").textContent = state.lite ? "✨ Efectos" : "🪶 Liviano";
  }

  const PHASES = { lobby: "Sala de espera", intro: "Mostrando pregunta", question: "⏱ Respondiendo", reveal: "Respuesta correcta", board: "Ranking", podium: "🏆 Podio final" };
  function renderGame(g) {
    $("#g-phase").textContent = PHASES[g.phase] || "Juego";
    $("#g-q").textContent = g.question || (g.phase === "lobby" ? "Pasales el enlace o que escaneen el QR" : "");
    $("#g-ok").textContent = g.correct ? "✓ " + g.correct : "";
    $("#g-players").textContent = g.players.length;
    $("#g-answered").textContent = g.phase === "question" || g.phase === "reveal" ? g.answered : "–";
    $("#g-qnum").textContent = g.qi >= 0 ? `${Math.min(g.qi + 1, g.total)}/${g.total}` : `0/${g.total}`;
    const main = $("#g-main");
    main.textContent = g.nextLabel;
    main.disabled = (g.phase === "lobby" && !g.players.length) || (g.phase === "podium" && g.nextLabel.includes("Terminado"));
    const pl = $("#plist");
    if (!g.players.length) { pl.innerHTML = '<div class="pl-empty">Todavía no entró nadie.<br>Tocá <b>📲 Compartir enlace</b> y mandalo al grupo.</div>'; return; }
    pl.innerHTML = g.players.map((p, i) => `
      <div class="pl-row ${p.on ? "" : "off"}">
        <span class="s">${i + 1}</span>
        <span class="n">${esc(p.name)} ${g.phase === "question" ? (p.ans ? "✅" : "⏳") : ""}</span>
        <span class="s">${p.score}</span>
        <button class="k" data-kick="${esc(p.pid)}" title="Sacar">✕</button>
      </div>`).join("");
  }

  $("#plist").addEventListener("click", (e) => {
    const b = e.target.closest("[data-kick]");
    if (!b) return;
    const name = b.parentElement.querySelector(".n").textContent.trim();
    if (confirm(`¿Sacar a "${name}" del juego?`)) cmd("kick", { pid: b.dataset.kick });
  });

  // ---------- botones ----------
  $("#next-btn").addEventListener("click", () => { if (state && !state.started) cmd("start"); else cmd("next"); });
  $("#prev-btn").addEventListener("click", () => cmd("prev"));
  $("#mute-btn").addEventListener("click", () => cmd("mute"));
  $("#lite-btn").addEventListener("click", () => cmd("lite"));
  $("#game-btn").addEventListener("click", () => { if (confirm("¿Abrir la sala del juego ahora?")) cmd("game-open"); });
  $("#g-main").addEventListener("click", () => cmd("next"));
  $("#back-btn").addEventListener("click", () => { if (confirm("¿Cerrar el juego y volver a la presentación?")) cmd("game-close"); });
  $("#reset-btn").addEventListener("click", () => { if (confirm("¿Reiniciar los puntajes y volver a la sala?")) cmd("game-reset"); });
  $("#share-btn").addEventListener("click", async () => {
    if (!state) return;
    const url = state.playUrl;
    const text = "🧠 ¡Entrá al juego de “Tu cerebro te miente”! Poné tu nombre y esperá:";
    try {
      if (navigator.share) await navigator.share({ title: "Tu cerebro te miente · Juego", text, url });
      else { await navigator.clipboard.writeText(url); alert("Enlace copiado:\n" + url); }
    } catch (e) {
      // si cancelan el menú de compartir no hacemos nada; si falla, ofrecemos WhatsApp
      if (e && e.name !== "AbortError") location.href = "https://wa.me/?text=" + encodeURIComponent(text + " " + url);
    }
  });

  // lista de diapositivas
  $("#list-btn").addEventListener("click", () => {
    if (!state) return;
    $("#sheet-list").innerHTML = state.list.map((t, i) => `<button class="sl-item ${i === state.slide.i ? "cur" : ""}" data-i="${i}"><b>${i + 1}</b>${esc(t)}</button>`).join("");
    $("#sheet").classList.remove("hidden");
  });
  $("#sheet").addEventListener("click", (e) => {
    const b = e.target.closest("[data-i]");
    if (b) cmd("goto", { i: parseInt(b.dataset.i, 10) });
    $("#sheet").classList.add("hidden");
  });

  // deslizar el dedo sobre las notas también cambia de diapositiva
  let tx = null, ty = null;
  const area = $("#v-slides");
  area.addEventListener("touchstart", (e) => { tx = e.touches[0].clientX; ty = e.touches[0].clientY; }, { passive: true });
  area.addEventListener("touchend", (e) => {
    if (tx === null) return;
    const dx = e.changedTouches[0].clientX - tx, dy = e.changedTouches[0].clientY - ty;
    if (Math.abs(dx) > 70 && Math.abs(dx) > Math.abs(dy) * 1.5 && !e.target.closest(".nav")) cmd(dx < 0 ? "next" : "prev");
    tx = ty = null;
  });

  // cronómetro
  setInterval(() => {
    if (!state || !state.started) return;
    const s = elapsedBase + Math.floor((Date.now() - elapsedAt) / 1000);
    const mm = String(Math.floor(s / 60)).padStart(2, "0"), ss = String(s % 60).padStart(2, "0");
    const t = $("#timer");
    t.textContent = `${mm}:${ss}`;
    t.classList.toggle("warn", s >= (CONFIG.minutosAviso || 25) * 60);
  }, 500);
})();
