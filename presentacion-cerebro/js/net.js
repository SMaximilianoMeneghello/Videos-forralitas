// ============================================================
//  NET — conexión en tiempo real entre la netbook (host),
//  el control remoto y los celulares de los jugadores.
//
//  Usa PeerJS (WebRTC). Con ?local=1 en la URL usa
//  BroadcastChannel: sirve para probar todo en una misma
//  compu abriendo varias pestañas.
// ============================================================
(function () {
  const PREFIX = "tcm-cerebro-v1-";
  const ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
  const params = new URLSearchParams(location.search);
  const LOCAL = params.has("local");

  const PING_EVERY = 4000;
  const DEAD_AFTER = 14000;

  function randomCode(n) {
    let s = "";
    for (let i = 0; i < n; i++) s += ALPHABET[Math.floor(Math.random() * ALPHABET.length)];
    return s;
  }

  function uid() {
    return Math.random().toString(36).slice(2, 10) + Date.now().toString(36).slice(-4);
  }

  // Arma la URL a otra página manteniendo ?local si corresponde
  function pageUrl(page, room) {
    const u = new URL(page, location.href);
    u.search = "";
    u.hash = "";
    u.searchParams.set("r", room);
    if (LOCAL) u.searchParams.set("local", "1");
    return u.toString();
  }

  // ----------------------------------------------------------
  //  HOST (netbook)
  // ----------------------------------------------------------
  function host(opts) {
    const clients = new Map(); // cid -> {send, role, last, close}
    let room = opts.room || randomCode(4);
    let peer = null;
    let destroyed = false;
    let idRetries = 0;

    const status = (s, extra) => opts.onStatus && opts.onStatus(s, extra);

    function addClient(cid, sendFn, closeFn, meta) {
      clients.set(cid, { send: sendFn, close: closeFn, role: (meta && meta.role) || "?", last: Date.now() });
      opts.onConnect && opts.onConnect(cid, meta || {});
    }

    function dropClient(cid) {
      const c = clients.get(cid);
      if (!c) return;
      clients.delete(cid);
      try { c.close && c.close(); } catch (e) {}
      opts.onClose && opts.onClose(cid, c.role);
    }

    function handle(cid, msg) {
      const c = clients.get(cid);
      if (!c) return;
      c.last = Date.now();
      if (msg && msg.t === "__pong") return;
      if (msg && msg.t === "__ping") { c.send({ t: "__pong" }); return; }
      opts.onMessage && opts.onMessage(cid, msg);
    }

    // Latido: detecta celulares que se fueron sin avisar
    const beat = setInterval(() => {
      const now = Date.now();
      clients.forEach((c, cid) => {
        if (now - c.last > DEAD_AFTER) dropClient(cid);
        else { try { c.send({ t: "__ping" }); } catch (e) {} }
      });
    }, PING_EVERY);

    // ---------- modo local (BroadcastChannel) ----------
    if (LOCAL) {
      const ch = new BroadcastChannel("tcm-" + room);
      ch.onmessage = (ev) => {
        const m = ev.data;
        if (!m || m.to !== "host") return;
        if (m.k === "hello") {
          if (clients.has(m.from)) dropClient(m.from);
          addClient(m.from, (data) => ch.postMessage({ to: m.from, k: "msg", data }), null, m.meta);
          ch.postMessage({ to: m.from, k: "welcome" });
        } else if (m.k === "msg") handle(m.from, m.data);
        else if (m.k === "bye") dropClient(m.from);
      };
      setTimeout(() => { status("ready"); opts.onReady && opts.onReady(room); }, 50);
      return api();
    }

    // ---------- modo PeerJS ----------
    function start() {
      if (destroyed) return;
      status("connecting");
      peer = new Peer(PREFIX + room, { debug: 0 });

      peer.on("open", () => {
        idRetries = 0;
        status("ready");
        opts.onReady && opts.onReady(room);
      });

      peer.on("connection", (conn) => {
        const cid = conn.connectionId || uid();
        conn.on("open", () => {
          addClient(cid, (data) => { if (conn.open) conn.send(data); }, () => conn.close(), conn.metadata);
        });
        conn.on("data", (data) => handle(cid, data));
        conn.on("close", () => dropClient(cid));
        conn.on("error", () => dropClient(cid));
      });

      peer.on("disconnected", () => {
        // Se cortó el servidor de señalización: las conexiones abiertas siguen,
        // pero hay que reconectar para aceptar nuevos jugadores.
        if (destroyed) return;
        status("reconnecting");
        setTimeout(() => { try { if (!peer.destroyed) peer.reconnect(); } catch (e) {} }, 1500);
      });

      peer.on("error", (err) => {
        const type = err && err.type;
        if (type === "unavailable-id") {
          // El código quedó "tomado" (ej: recargaste la página). Reintenta un rato.
          try { peer.destroy(); } catch (e) {}
          idRetries++;
          if (idRetries > 6) { room = randomCode(4); idRetries = 0; }
          status("retrying", { room });
          setTimeout(start, 2500);
        } else if (type === "network" || type === "server-error" || type === "socket-error" || type === "socket-closed") {
          status("reconnecting");
          setTimeout(() => {
            try {
              if (peer.destroyed) start();
              else if (peer.disconnected) peer.reconnect();
            } catch (e) { start(); }
          }, 3000);
        } else if (type === "browser-incompatible") {
          status("error", { message: "Este navegador no soporta WebRTC. Usá Google Chrome." });
        } else {
          console.warn("PeerJS:", type, err);
        }
      });
    }

    if (typeof Peer === "undefined") {
      status("error", { message: "No se pudo cargar PeerJS." });
    } else {
      start();
    }

    function api() {
      return {
        get room() { return room; },
        send(cid, msg) { const c = clients.get(cid); if (c) { try { c.send(msg); } catch (e) {} } },
        broadcast(msg, role) {
          clients.forEach((c) => { if (!role || c.role === role) { try { c.send(msg); } catch (e) {} } });
        },
        kick(cid) { dropClient(cid); },
        clients,
        destroy() { destroyed = true; clearInterval(beat); try { peer && peer.destroy(); } catch (e) {} },
      };
    }
    return api();
  }

  // ----------------------------------------------------------
  //  CLIENTE (control remoto / jugador)
  // ----------------------------------------------------------
  function join(opts) {
    const room = (opts.room || "").toUpperCase();
    let connected = false;
    let lastSeen = 0;
    let conn = null;
    let peer = null;
    let sendRaw = () => {};
    let retryTimer = null;
    let openTimer = null;
    let attempt = 0;
    const status = (s) => opts.onStatus && opts.onStatus(s);

    function onOpen() {
      connected = true;
      attempt = 0;
      lastSeen = Date.now();
      clearTimeout(openTimer);
      status("connected");
      opts.onOpen && opts.onOpen();
    }

    function onData(msg) {
      lastSeen = Date.now();
      if (msg && msg.t === "__ping") { sendRaw({ t: "__pong" }); return; }
      if (msg && msg.t === "__pong") return;
      opts.onMessage && opts.onMessage(msg);
    }

    function lost() {
      if (connected) { connected = false; opts.onClose && opts.onClose(); }
      status("reconnecting");
      scheduleRetry();
    }

    function scheduleRetry() {
      clearTimeout(retryTimer);
      attempt++;
      const wait = Math.min(1000 * attempt, 5000);
      retryTimer = setTimeout(connect, wait);
    }

    // Si el host deja de responder, reconecta
    setInterval(() => {
      if (connected && Date.now() - lastSeen > DEAD_AFTER) {
        try { conn && conn.close && conn.close(); } catch (e) {}
        lost();
      } else if (connected) {
        sendRaw({ t: "__ping" });
      }
    }, PING_EVERY);

    // ---------- modo local ----------
    if (LOCAL) {
      const me = uid();
      const ch = new BroadcastChannel("tcm-" + room);
      sendRaw = (data) => ch.postMessage({ to: "host", from: me, k: "msg", data });
      ch.onmessage = (ev) => {
        const m = ev.data;
        if (!m || m.to !== me) return;
        if (m.k === "welcome") onOpen();
        else if (m.k === "msg") onData(m.data);
      };
      function connect() {
        status("connecting");
        ch.postMessage({ to: "host", from: me, k: "hello", meta: { role: opts.role } });
        clearTimeout(openTimer);
        openTimer = setTimeout(() => { if (!connected) scheduleRetry(); }, 3000);
      }
      window.addEventListener("beforeunload", () => ch.postMessage({ to: "host", from: me, k: "bye" }));
      connect();
      return { send: (m) => connected && sendRaw(m), get connected() { return connected; } };
    }

    // ---------- modo PeerJS ----------
    function connect() {
      if (typeof Peer === "undefined") { status("error"); return; }
      status("connecting");
      try { conn && conn.close(); } catch (e) {}
      if (!peer || peer.destroyed) {
        peer = new Peer({ debug: 0 });
        peer.on("open", () => { if (!(connected && conn && conn.open)) openConn(); });
        peer.on("error", (err) => {
          if (err && err.type === "peer-unavailable") status("nohost");
          if (!connected) scheduleRetry();
        });
        peer.on("disconnected", () => {
          setTimeout(() => { try { if (!peer.destroyed && peer.disconnected) peer.reconnect(); } catch (e) {} }, 1500);
        });
      } else if (peer.disconnected) {
        // al reconectar, el evento "open" vuelve a llamar a openConn
        try { peer.reconnect(); } catch (e) { peer.destroy(); peer = null; scheduleRetry(); }
      } else {
        openConn();
      }
    }

    function openConn() {
      const prev = conn;
      conn = peer.connect(PREFIX + room, { reliable: true, serialization: "json", metadata: { role: opts.role } });
      const thisConn = conn;
      if (prev) { try { prev.close(); } catch (e) {} }
      sendRaw = (data) => { if (thisConn.open) thisConn.send(data); };
      thisConn.on("open", onOpen);
      thisConn.on("data", onData);
      thisConn.on("close", () => { if (thisConn === conn) lost(); });
      thisConn.on("error", () => { if (thisConn === conn) lost(); });
      clearTimeout(openTimer);
      openTimer = setTimeout(() => { if (!connected && thisConn === conn) { try { thisConn.close(); } catch (e) {} scheduleRetry(); } }, 9000);
    }

    // Al volver a la app desde WhatsApp, etc., reconecta enseguida
    document.addEventListener("visibilitychange", () => {
      if (document.visibilityState === "visible" && !connected) { clearTimeout(retryTimer); connect(); }
    });

    connect();
    return { send: (m) => { if (connected) sendRaw(m); }, get connected() { return connected; } };
  }

  window.NET = { host, join, pageUrl, randomCode, uid, LOCAL, params };
})();
