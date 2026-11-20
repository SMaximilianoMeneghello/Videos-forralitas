"""Video "Aves y semillas" — estilo sobre de semillas antiguo: papel madera, cada producto en un sobre con
ventanita, cinta roja con el nombre, semillitas que caen y pajaritos que cruzan.
python aves.py  |  python aves.py --cuadros 1 5"""
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from base import (FREDOKA, SLAB, W, H, Cierre, Guion, T, a_sprite, ajustar, blit, caja, centrar, clamp01,  # noqa: E402
                  cover, e_back, e_inout, e_out, ejecutar, foto, prog, realzar, sobre, sombra, subtitulos, AQUI)

KRAFT = (212, 184, 138)
PAPEL = (247, 238, 216)
VERDE = (34, 70, 40)
ROJO = (186, 58, 40)
SEMILLA = (150, 112, 60)

SOBRES = [  # (clave, foto, foco (cx, cy, zoom), nombre, detalle)
    ("intro", "fotos/04_semillas.jpg", (0.55, 0.55, 1.05), "AVES Y SEMILLAS", "Granos y semillas para tus aves"),
    ("semillas", "fotos/04_semillas.jpg", (0.60, 0.62, 1.35), "SEMILLAS PARA AVES", ""),
    ("entero", "fotos_presentacion/05_maiz_entero.jpg", (0.5, 0.5, 1.15), "MAÍZ ENTERO", "Bolsas de 40 kg y 50 kg"),
    ("quebrado", "fotos_presentacion/06_maiz_quebrado.jpg", (0.5, 0.5, 1.15), "MAÍZ QUEBRADO", "Bolsa de 40 kg y suelto"),
    ("avena", "assets/flyer/avena.jpg", (0.5, 0.5, 1.1), "AVENA", "Bolsa de 30 kg"),
]
GUION = [
    ("intro", "¿Buscás semillas y granos para tus aves? Mirá lo que tenemos.",
     "¿Buscás *semillas* y *granos* | para tus *aves?* | Mirá lo que tenemos."),
    ("semillas", "Semillas para aves.", "*Semillas* para *aves.*"),
    ("entero", "Maíz entero, en bolsas de cuarenta y cincuenta kilos.",
     "*Maíz* *entero,* | en bolsas de *40* y *50* *kilos.*"),
    ("quebrado", "Maíz quebrado, en bolsa de cuarenta kilos y suelto.",
     "*Maíz* *quebrado,* | en bolsa de *40* *kilos* | y suelto."),
    ("avena", "Y avena, en bolsa de treinta kilos.", "Y *avena,* | en bolsa de *30* *kilos.*"),
    ("fin", "Todo para tus aves, en Forralitas. ¡Te esperamos!",
     "Todo para tus *aves,* | en *Forralitas.* | *¡Te* *esperamos!*"),
]
SW, SH = 780, 1040            # sobre
SY = 900                      # centro vertical del sobre
VW, VH = 600, 560             # ventana (óvalo)


def sobre_vacio():
    """Sobre de papel con borde doble, solapa dentada y ventana ovalada (sin foto)."""
    L = 2
    w, h = SW * L, SH * L
    m = np.zeros((h, w), np.uint8)
    dientes = [(0, 60 * L)]
    for i in range(0, w + 1, 40 * L):
        dientes += [(i, 60 * L), (i + 20 * L, 30 * L)]
    dientes += [(w, 60 * L), (w, h), (0, h)]
    cv2.fillPoly(m, [np.array(dientes, np.int32)], 255, cv2.LINE_AA)
    m = cv2.resize(m, (SW, SH), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    base = a_sprite(np.full((SH, SW, 3), PAPEL, np.float32), m)
    tinta = np.zeros((SH, SW), np.uint8)
    cv2.rectangle(tinta, (26, 76), (SW - 26, SH - 26), 255, 5, cv2.LINE_AA)
    cv2.rectangle(tinta, (40, 90), (SW - 40, SH - 40), 255, 2, cv2.LINE_AA)
    cv2.ellipse(tinta, (SW // 2, 140 + VH // 2), (VW // 2 + 12, VH // 2 + 12), 0, 0, 360, 255, 4, cv2.LINE_AA)
    a = tinta.astype(np.float32) / 255
    return sobre(base, a_sprite(np.full((SH, SW, 3), VERDE, np.float32), a), 0, 0)


def mascara_ovalo():
    m = np.zeros((VH * 3, VW * 3), np.uint8)
    cv2.ellipse(m, (VW * 3 // 2, VH * 3 // 2), (VW * 3 // 2 - 3, VH * 3 // 2 - 3), 0, 0, 360, 255, -1, cv2.LINE_AA)
    return cv2.resize(m, (VW, VH), interpolation=cv2.INTER_AREA).astype(np.float32) / 255


def cinta(txt):
    tam = ajustar(txt, SLAB, 62, 640)
    s = T(txt, SLAB, tam, PAPEL)
    pad = int(tam * 0.35)
    w, h = max(s.shape[1] - 2 * pad + 90, 420), 110
    m = np.zeros((h, w + 80), np.uint8)
    cv2.fillPoly(m, [np.array([[0, 0], [w + 79, 0], [w + 50, h // 2], [w + 79, h - 1], [0, h - 1], [30, h // 2]])], 255,
                 cv2.LINE_AA)
    base = a_sprite(np.full((h, w + 80, 3), ROJO, np.float32), m.astype(np.float32) / 255)
    return centrar(base, s, (w + 80) / 2, h / 2 + 4)


def pajaro(f, x, y, esc, fase):
    ala = np.sin(fase) * 0.9
    p = lambda dx, dy: (int(x + dx * esc), int(y + dy * esc))
    cv2.polylines(f, [np.array([p(-34, ala * 16 - 6), p(-15, ala * 7 - 15), p(0, 0), p(15, ala * 7 - 15),
                                p(34, ala * 16 - 6)])], False, VERDE, max(3, int(4 * esc)), cv2.LINE_AA)


class Video:
    musica = os.path.join(AQUI, "musica", "Fretless.mp3")
    musica_inicio = 15.0

    def __init__(self):
        g = self.guion = Guion(GUION)
        self.img = {k: realzar(foto(r), 1.06, 0.10) for k, r, *_ in SOBRES}
        self.cam = {k: c for k, _, c, *_ in SOBRES}
        self.orden = [k for k, *_ in SOBRES]
        g["intro"]["t0"] = 0.7
        t = max(4.6, g.fin("intro") + 0.7)
        self.cambios = [("intro", 0.0)]
        for k in self.orden[1:]:
            g[k]["t0"] = t + 0.55
            self.cambios.append((k, t))
            t += max(3.2, g[k]["dur"] + 1.1)
        self.t_cierre = t
        g["fin"]["t0"] = t + 0.5
        self.dur = round(max(t + 8.0, g.fin("fin") + 4.5), 2)
        # ---- piezas
        self.vacio = sobre_vacio()
        self.sh_sobre = sombra(self.vacio, 18, 0.35)
        self.ovalo = mascara_ovalo()
        self.cintas = {k: cinta(n) for k, _, _, n, _ in SOBRES}
        self.detalles = {k: (T(d, FREDOKA, ajustar(d, FREDOKA, 46, SW - 100), VERDE) if d else None)
                         for k, _, _, _, d in SOBRES}
        self.numeros = {k: T(f"Nº {i}", SLAB, 40, ROJO) for i, k in enumerate(self.orden)}
        self.titulo = T("AVES Y SEMILLAS", SLAB, 78, VERDE)
        sello = T("FORRALITAS", SLAB, 40, ROJO)
        borde = np.zeros((sello.shape[0] - 10, sello.shape[1] - 10), np.uint8)
        cv2.rectangle(borde, (4, 4), (borde.shape[1] - 5, borde.shape[0] - 5), 255, 4, cv2.LINE_AA)
        self.sello = centrar(a_sprite(np.full(borde.shape + (3,), ROJO, np.float32), borde.astype(np.float32) / 255),
                             sello, borde.shape[1] / 2, borde.shape[0] / 2 + 3)
        self.cierre = Cierre(dict(titulo_f=SLAB, texto_f=FREDOKA, num_f=SLAB, col_titulo=VERDE, col_texto=VERDE,
                                  col_sub=ROJO, tarjeta=PAPEL, tarjeta_alpha=0.96, ic_fondo=ROJO, ic_tinta=PAPEL,
                                  espera="¡TE ESPERAMOS!", espera_f=SLAB, col_espera=ROJO))
        rng = np.random.default_rng(12)
        ruido = rng.normal(0, 9, (H // 2, W // 2)).astype(np.float32)
        ruido = cv2.resize(cv2.GaussianBlur(ruido, (0, 0), 0.8), (W, H))[..., None]
        base = np.array(KRAFT, np.float32) + ruido
        fibras = np.zeros((H, W), np.uint8)
        for _ in range(500):
            x, y = rng.integers(0, W), rng.integers(0, H)
            a = rng.uniform(0, np.pi)
            l = rng.integers(8, 30)
            cv2.line(fibras, (int(x), int(y)), (int(x + l * np.cos(a)), int(y + l * np.sin(a))), 255, 1, cv2.LINE_AA)
        base -= (fibras.astype(np.float32) / 255 * 22)[..., None]
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.hypot(xx - W / 2, yy - H / 2) / np.hypot(W / 2, H / 2)
        self.fondo0 = np.clip(base * (1 - 0.18 * r ** 2)[..., None], 0, 255).astype(np.uint8)
        self.semillas = rng.uniform(0, 1, (40, 4))
        self._subs = {}
        self.estilo_sub = dict(fuente=FREDOKA, tam=58, color=VERDE, resaltado=ROJO, y=1665, caja=PAPEL, caja_alpha=0.97)

    def sfx(self):
        return [(c - 0.2, "whoosh") for _, c in self.cambios[1:]] + [(self.t_cierre - 0.25, "whoosh")] + \
               [(c + 0.45, "pop") for _, c in self.cambios[1:]]

    def fondo(self, t):
        f = self.fondo0.copy()
        for x, y, v, ph in self.semillas:                     # semillitas que caen
            cx = x * W + 20 * np.sin(t * 1.4 + ph * 6)
            cy = (y * (H + 60) + t * (60 + 90 * v)) % (H + 60) - 30
            cv2.ellipse(f, (int(cx), int(cy)), (int(6 + 4 * v), int(3 + 2 * v)), (t * 80 + ph * 360) % 180, 0, 360,
                        SEMILLA, -1, cv2.LINE_AA)
        for i in range(3):                                    # pajaritos
            per = 9.0
            tt = (t + i * 2.2) % per
            if tt < 4.5:
                x = -80 + tt / 4.5 * (W + 160)
                pajaro(f, x, 330 + i * 46 + 18 * np.sin(t * 2 + i), 0.8 + 0.15 * i, t * 10 + i)
        return f

    def sobre_lleno(self, k, t, t0):
        cx, cy, z = self.cam[k]
        img = cover(self.img[k], VW, VH, cx, cy, z * (1 + 0.07 * clamp01((t - t0) / 3.5)))
        s = sobre(self.vacio, np.dstack([img.astype(np.float32) * self.ovalo[..., None], self.ovalo]), (SW - VW) // 2, 140)
        cy_c = 140 + VH + 85
        s = centrar(s, self.cintas[k], SW / 2, cy_c)
        if self.detalles[k] is not None:
            s = centrar(s, self.detalles[k], SW / 2, cy_c + 115)
        return s if k == "intro" else centrar(s, self.numeros[k], 92, 115)

    def escena(self, t):
        f = self.fondo(t)
        q = prog(t, 0.1, 0.5)
        blit(f, self.titulo, W / 2, 170 - (1 - e_out(q)) * 60, alpha=clamp01(q * 3))
        qs = prog(t, 0.45, 0.35)
        blit(f, self.sello, W / 2, 255, alpha=clamp01(qs * 3), escala=max(2.0 - 1.0 * e_out(qs), 0.01), ang=-4)
        idx = max(i for i, (_, c) in enumerate(self.cambios) if t >= c - 0.05)
        k, c = self.cambios[idx]
        if idx > 0 and t < c + 0.5:                          # el sobre anterior sale hacia la izquierda girando
            kp, cp = self.cambios[idx - 1]
            p = e_inout(clamp01((t - c + 0.05) / 0.5))
            blit(f, self.sobre_lleno(kp, t, cp), W / 2 - p * 1150, SY + p * 120, ang=8 * p)
        q = prog(t, c + (0.15 if idx else 0.05), 0.6)
        if q > 0:
            y = SY - (1 - e_out(q)) * 1300
            ang = (-12 + 10 * e_back(q, 1.6)) if idx % 2 else (12 - 14 * e_back(q, 1.6))
            blit(f, self.sh_sobre, W / 2 + 10, y + 20, alpha=clamp01(q * 3), ang=ang)
            blit(f, self.sobre_lleno(k, t, c), W / 2, y, ang=ang)
        return f

    def esc_cierre(self, t):
        f = self.fondo(t)
        self.cierre.dibujar(f, t - self.t_cierre, y0=190, desde="alterno")
        return f

    def frame(self, t):
        t = min(t, self.dur - 1e-3)
        c = self.t_cierre
        if c - 0.3 <= t < c + 0.3:                       # persiana de papel que baja
            p = e_inout((t - (c - 0.3)) / 0.6)
            a, b = self.escena(min(t, c - 1e-3)), self.esc_cierre(max(t, c))
            y = int(p * H)
            f = a.copy()
            f[:y] = b[:y]
            cv2.line(f, (0, y), (W, y), ROJO, 10, cv2.LINE_AA)
        elif t < c:
            f = self.escena(t)
        else:
            f = self.esc_cierre(t)
        f = np.ascontiguousarray(f)
        subtitulos(f, self.guion, t, self.estilo_sub, self._subs)
        if t < 0.25:
            f = (f.astype(np.float32) * (t / 0.25)).astype(np.uint8)
        if t > self.dur - 0.5:
            f = (f.astype(np.float32) * ((self.dur - t) / 0.5)).astype(np.uint8)
        return f


if __name__ == "__main__":
    ejecutar(Video(), "forralitas_aves_semillas")
