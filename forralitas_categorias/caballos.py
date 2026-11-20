"""Video "Para tus caballos" — estilo cine western: franjas negras, tonos dorados, números grandes y
carteles de cuero.   python caballos.py  |  python caballos.py --cuadros 1 5 9"""
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from base import (ANTON, MONT, RYE, SLAB, W, H, Cierre, Guion, T, a_sprite, ajustar, blit, caja, centrar,  # noqa: E402
                  clamp01, cover, e_back, e_inout, e_out, ejecutar, foto, mascara_redonda, prog, realzar,
                  sobre, sombra, subtitulos, AQUI)

NEGRO = (14, 10, 8)
ORO = (226, 178, 92)
CREMA = (246, 233, 206)
CUERO = (96, 58, 30)
CUERO_OSC = (58, 34, 18)
BARRA = 200

PRODUCTOS = [  # (clave, foto, cámara (cx, cy, zoom) inicio → fin, nombre en pantalla, detalle)
    ("alfa", "fotos_presentacion/01_alfa.jpg", ((0.50, 0.45, 1.25), (0.50, 0.55, 1.05)), "ALFA VERDE", "En fardos"),
    ("mezcla", "fotos_presentacion/03_mezcla_caballo.jpg", ((0.40, 0.50, 1.05), (0.60, 0.50, 1.25)),
     "MEZCLA PARA CABALLO", "Preparada · Bolsa de 35 kg y suelto"),
    ("alto", "assets/nuevas/alto_rendimiento.jpg", ((0.45, 0.50, 1.25), (0.58, 0.48, 1.05)), "ALTO RENDIMIENTO", ""),
    ("yegua", "assets/nuevas/yegua_con_cria.jpg", ((0.58, 0.45, 1.05), (0.45, 0.50, 1.25)), "YEGUA CON CRÍA", ""),
]
GUION = [
    ("intro", "¿Tenés caballos? Mirá todo lo que tenemos para ellos.",
     "¿Tenés *caballos?* | Mirá todo lo que | tenemos para ellos."),
    ("alfa", "Alfa verde, en fardos.", "*Alfa* *verde,* en fardos."),
    ("mezcla", "Mezcla para caballo preparada, en bolsa de treinta y cinco kilos y suelto.",
     "*Mezcla* *para* *caballo* | *preparada,* en bolsa | de *35* _ _ *kilos* y suelto."),
    ("alto", "Alto rendimiento.", "*Alto* *rendimiento.*"),
    ("yegua", "Y alimento para yegua con cría.", "Y *alimento* para | *yegua* *con* *cría.*"),
    ("fin", "Todo para tus caballos, en Forralitas. ¡Te esperamos!",
     "Todo para tus *caballos,* | en *Forralitas.* | *¡Te* *esperamos!*"),
]


def herradura(d, color):
    """Herradura dibujada (sprite)."""
    L = d * 3
    m = np.zeros((L, L), np.uint8)
    cv2.ellipse(m, (L // 2, int(L * 0.46)), (int(L * 0.36), int(L * 0.38)), 0, 150, 390, 255, int(L * 0.13), cv2.LINE_AA)
    for a in (165, 200, 235, 305, 340, 375):
        x = L / 2 + L * 0.36 * np.cos(np.radians(a))
        y = L * 0.46 + L * 0.38 * np.sin(np.radians(a))
        cv2.circle(m, (int(x), int(y)), int(L * 0.022), 0, -1, cv2.LINE_AA)
    a = cv2.resize(m, (d, d), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    return a_sprite(np.full((d, d, 3), color, np.float32), a)


def cartel(nombre, detalle):
    w = 960
    tam = ajustar(nombre, RYE, 84, w - 90)
    h = 230
    base = caja(w, h, 26, CUERO_OSC)
    base = sobre(base, caja(w - 16, h - 16, 20, CUERO), 8, 8)
    costura = np.zeros((h, w), np.uint8)               # costura punteada
    for x in range(30, w - 30, 26):
        cv2.line(costura, (x, 22), (x + 13, 22), 255, 3, cv2.LINE_AA)
        cv2.line(costura, (x, h - 22), (x + 13, h - 22), 255, 3, cv2.LINE_AA)
    a = costura.astype(np.float32) / 255 * 0.7
    base = sobre(base, a_sprite(np.full((h, w, 3), ORO, np.float32), a), 0, 0)
    if detalle:
        base = centrar(base, T(nombre, RYE, tam, CREMA, sombra=0.35), w / 2, 92)
        base = centrar(base, T(detalle, MONT, ajustar(detalle, MONT, 44, w - 90), ORO), w / 2, 165)
    else:
        base = centrar(base, T(nombre, RYE, tam, CREMA, sombra=0.35), w / 2, h / 2 + 4)
    return base


class Video:
    musica = os.path.join(AQUI, "musica", "Galway.mp3")
    musica_inicio = 10.0

    def __init__(self):
        g = self.guion = Guion(GUION)
        self.fotos = {k: realzar(foto(r), 1.06, 0.10) for k, r, *_ in PRODUCTOS}
        self.caballo = realzar(foto("assets/nuevas/n03.png"), 1.04, 0.10)
        # ---- tiempos
        g["intro"]["t0"] = 0.6
        t = max(4.4, g.fin("intro") + 0.7)
        self.escenas = [("intro", 0.0, t)]
        for k, *_ in PRODUCTOS:
            g[k]["t0"] = t + 0.45
            d = max(3.4, g[k]["dur"] + 1.0)
            self.escenas.append((k, t, t + d))
            t += d
        self.t_cierre = t
        g["fin"]["t0"] = t + 0.5
        self.dur = round(max(t + 8.0, g.fin("fin") + 4.5), 2)
        # ---- piezas
        self.titulo1 = T("¿TENÉS", RYE, 120, CREMA, sombra=0.5)
        self.titulo2 = T("CABALLOS?", RYE, ajustar("CABALLOS?", RYE, 170, 980), ORO, sombra=0.5)
        self.herr = herradura(120, ORO)
        self.herr_chica = herradura(56, ORO)
        self.carteles = {k: cartel(n, d) for k, _, _, n, d in PRODUCTOS}
        self.sombras = {k: sombra(c, 16, 0.5) for k, c in self.carteles.items()}
        self.numeros = {k: T(f"{i + 1:02d}", SLAB, 150, ORO, sombra=0.5) for i, (k, *_) in enumerate(PRODUCTOS)}
        self.de = {k: T(f"/ {len(PRODUCTOS):02d}", SLAB, 52, CREMA, sombra=0.4) for k, *_ in PRODUCTOS}
        self.cabecera = T("FORRALITAS  ·  PARA TU CABALLO", MONT, 34, ORO)
        self.cierre = Cierre(dict(titulo_f=RYE, texto_f=MONT, num_f=SLAB, col_titulo=CREMA, col_texto=CREMA,
                                  col_sub=ORO, tarjeta=CUERO_OSC, tarjeta_alpha=0.92, ic_fondo=ORO, ic_tinta=CUERO_OSC,
                                  espera="¡TE ESPERAMOS!", espera_f=RYE, col_espera=ORO, sombra=0.4))
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.hypot(xx - W / 2, yy - H / 2) / np.hypot(W / 2, H / 2)
        self.vig = (1 - 0.35 * r ** 2.2)[..., None]
        rng = np.random.default_rng(3)
        self.grano = [rng.normal(0, 7, (H // 2, W // 2)).astype(np.float32) for _ in range(4)]
        t1 = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
        self.fondo_cierre = np.clip(np.array((52, 32, 18), np.float32) * (1 - t1) + np.array((16, 10, 6), np.float32) * t1,
                                    0, 255) * np.ones((1, W, 1), np.float32)
        yv = (np.arange(H, dtype=np.float32) / H)[:, None, None]
        self.oscuro_abajo = 1 - 0.6 * np.clip((yv - 0.5) / 0.3, 0, 1)
        self._subs = {}
        self.estilo_sub = dict(fuente=MONT, tam=56, color=CREMA, resaltado=ORO, y=H - BARRA // 2 - 6, caja=None)

    def sfx(self):
        s = [(e[1] - 0.25, "whoosh") for e in self.escenas[1:]] + [(self.t_cierre - 0.25, "whoosh")]
        return s + [(0.8, "golpe")]

    # ---- escenas
    def esc_intro(self, t):
        e = e_inout(clamp01(t / 4.4))
        f = cover(self.caballo, W, H, 0.62, 0.40, 1.10 - 0.10 * e)
        f = (f.astype(np.float32) * self.oscuro_abajo).astype(np.uint8)
        y1, y2, y3 = 1180, 1350, 1495
        q = prog(t, 0.5, 0.6)
        blit(f, self.titulo1, W / 2, y1 + (1 - e_out(q)) * 40, alpha=clamp01(q * 2.5))
        q = prog(t, 0.85, 0.6)
        blit(f, self.titulo2, W / 2, y2, alpha=clamp01(q * 2.5), escala=1.12 - 0.12 * e_out(q))
        q = e_out(prog(t, 1.3, 0.6))
        if q > 0:
            cv2.line(f, (int(W / 2 - 110 - 220 * q), y3), (int(W / 2 - 110), y3), ORO, 4, cv2.LINE_AA)
            cv2.line(f, (int(W / 2 + 110), y3), (int(W / 2 + 110 + 220 * q), y3), ORO, 4, cv2.LINE_AA)
            blit(f, self.herr_chica, W / 2, y3 + 2, alpha=q, escala=0.6 + 0.4 * q)
        return f

    def esc_producto(self, k, a, b, t):
        cam = next(p[2] for p in PRODUCTOS if p[0] == k)
        p = e_inout(clamp01((t - a) / (b - a)))
        (x0, y0, z0), (x1, y1, z1) = cam
        f = cover(self.fotos[k], W, H, x0 + (x1 - x0) * p, y0 + (y1 - y0) * p, z0 + (z1 - z0) * p)
        tl = t - a
        q = prog(tl, 0.3, 0.5)
        blit(f, self.numeros[k], 150 - (1 - e_out(q)) * 200, 360, alpha=clamp01(q * 3))
        blit(f, self.de[k], 300 - (1 - e_out(q)) * 200, 390, alpha=clamp01(q * 3))
        q = prog(tl, 0.45, 0.55)
        y = 1380 + (1 - e_out(q)) * 120
        blit(f, self.sombras[k], W / 2 + 6, y + 16, alpha=clamp01(q * 3))
        blit(f, self.carteles[k], W / 2, y, alpha=clamp01(q * 3), escala=0.92 + 0.08 * e_back(q, 1.6))
        return f

    def esc_cierre(self, t):
        f = self.fondo_cierre.astype(np.uint8)
        f = np.ascontiguousarray(f)
        tl = t - self.t_cierre
        q = prog(tl, 0.0, 0.6)
        blit(f, self.herr, W / 2, H - BARRA - 150, alpha=0.25 * clamp01(q * 2))
        self.cierre.dibujar(f, tl, y0=BARRA + 130, desde="alterno")
        return f

    def escena(self, t):
        if t >= self.t_cierre:
            return self.esc_cierre(t)
        for k, a, b in self.escenas:
            if a <= t < b:
                return self.esc_intro(t) if k == "intro" else self.esc_producto(k, a, b, t)
        return self.esc_cierre(t)

    # ---- transición "quemado de película"
    def frame(self, t):
        t = min(t, self.dur - 1e-3)
        cortes = [e[1] for e in self.escenas[1:]] + [self.t_cierre]
        f = None
        for c in cortes:
            if c - 0.28 <= t < c + 0.28:
                p = (t - (c - 0.28)) / 0.56
                a, b = self.escena(min(t, c - 1e-3)), self.escena(max(t, c))
                base = a if p < 0.5 else b
                fl = np.exp(-((p - 0.5) / 0.2) ** 2)
                luz = np.array((255, 196, 120), np.float32)
                f = np.clip(base.astype(np.float32) * (1 + 0.5 * fl) + luz * 0.35 * fl, 0, 255).astype(np.uint8)
                break
        if f is None:
            f = self.escena(t)
        f = np.ascontiguousarray(f)
        # tono cálido suave + viñeta + grano
        x = f.astype(np.float32) * np.array([1.03, 1.0, 0.93], np.float32) * self.vig
        x += cv2.resize(self.grano[int(t * 24) % 4], (W, H))[..., None]
        f = np.clip(x, 0, 255).astype(np.uint8)
        # franjas de cine
        f[:BARRA] = NEGRO
        f[H - BARRA:] = NEGRO
        q = clamp01(t / 0.6)
        blit(f, self.cabecera, W / 2, BARRA / 2 + 10, alpha=q * (1 - prog(t, self.t_cierre - 0.3, 0.3)))
        subtitulos(f, self.guion, t, self.estilo_sub, self._subs)
        if t < 0.35:
            f = (f.astype(np.float32) * (t / 0.35)).astype(np.uint8)
        if t > self.dur - 0.5:
            f = (f.astype(np.float32) * ((self.dur - t) / 0.5)).astype(np.uint8)
        return f


if __name__ == "__main__":
    ejecutar(Video(), "forralitas_caballos")
