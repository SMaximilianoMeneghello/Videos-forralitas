"""Video "Para tus cerdos" — estilo mosaico rosa: fotos en recuadros redondeados que se reacomodan;
el producto que se nombra pasa al recuadro grande.   python chanchos.py  |  python chanchos.py --cuadros 1 5"""
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from base import (FREDOKA, LILITA, W, H, Cierre, Guion, T, ajustar, blit, caja, centrar, clamp01,  # noqa: E402
                  cover, e_back, e_inout, e_out, ejecutar, foto, mascara_redonda, prog, realzar, sobre, sombra,
                  subtitulos, AQUI)

ROSA = (250, 216, 214)
ROSA2 = (244, 186, 186)
CIRUELA = (78, 28, 58)
CORAL = (236, 92, 104)
BLANCO = (255, 255, 255)

ITEMS = [  # (clave, foto, foco (cx, cy), nombre, detalle)
    ("intro", "assets/nuevas/n02.png", (0.52, 0.45), "¿TENÉS CERDOS?", ""),
    ("alimento", "fotos_presentacion/02_engorde_cerdo.jpg", (0.5, 0.5), "ALIMENTO DE CERDO",
     "Preparado · Bolsa de 30 kg y suelto"),
    ("engorde", "assets/nuevas/harina_carne.jpg", (0.5, 0.5), "ENGORDE DE CERDO", "Con harina de carne"),
]
GUION = [
    ("intro", "¿Tenés cerdos? Esto es lo que tenemos para ofrecerte.",
     "¿Tenés *cerdos?* | Esto es lo que | tenemos para *ofrecerte.*"),
    ("alimento", "Alimento de cerdo preparado, en bolsa de treinta kilos y suelto.",
     "*Alimento* de *cerdo* *preparado,* | en bolsa de *30* *kilos* | y suelto."),
    ("engorde", "Y engorde de cerdo con harina de carne.", "Y *engorde* de *cerdo* | con *harina* de *carne.*"),
    ("fin", "Todo para tus cerdos, en Forralitas. ¡Te esperamos!",
     "Todo para tus *cerdos,* | en *Forralitas.* | *¡Te* *esperamos!*"),
]
GRANDE = (60, 300, 960, 840)          # x, y, w, h
FILA_Y, FILA_H, FILA_W, GAP = 1300, 210, 290, 45


class Video:
    musica = os.path.join(AQUI, "musica", "Groundwork.mp3")
    musica_inicio = 20.0

    def __init__(self):
        g = self.guion = Guion(GUION)
        self.img = {k: realzar(foto(r), 1.08, 0.10) for k, r, *_ in ITEMS}
        self.foco = {k: c for k, _, c, *_ in ITEMS}
        self.orden = [k for k, *_ in ITEMS]
        # ---- tiempos
        g["intro"]["t0"] = 0.7
        t = max(4.4, g.fin("intro") + 0.7)
        self.cambios = [("intro", 0.0)]
        for k in self.orden[1:]:
            g[k]["t0"] = t + 0.55
            self.cambios.append((k, t))
            t += max(3.4, g[k]["dur"] + 1.1)
        self.t_cierre = t
        g["fin"]["t0"] = t + 0.5
        self.dur = round(max(t + 8.0, g.fin("fin") + 4.5), 2)
        # ---- piezas
        self.titulo = T("PARA TUS CERDOS", LILITA, 76, CIRUELA)
        self.marca = T("FORRALITAS", FREDOKA, 34, CORAL)
        self.nombres, self.detalles = {}, {}
        for k, _, _, n, d in ITEMS:
            s = T(n, LILITA, ajustar(n, LILITA, 76, 820), BLANCO)
            pad = int(76 * 0.35)
            w, h = s.shape[1] - 2 * pad + 90, 120
            self.nombres[k] = centrar(caja(w, h, 60, CORAL), s, w / 2, h / 2 + 4)
            self.detalles[k] = T(d, FREDOKA, ajustar(d, FREDOKA, 50, 960), CIRUELA) if d else None
        self.sh_nombre = {k: sombra(v, 12, 0.3) for k, v in self.nombres.items()}
        self.badges = {}
        for i, k in enumerate(self.orden):
            b = caja(64, 64, 32, CIRUELA)
            self.badges[k] = centrar(b, T(str(i), LILITA, 40, BLANCO), 32, 34)
        self.cierre = Cierre(dict(titulo_f=LILITA, texto_f=FREDOKA, num_f=LILITA, col_titulo=CIRUELA, col_texto=CIRUELA,
                                  col_sub=CORAL, tarjeta=BLANCO, tarjeta_alpha=0.95, ic_fondo=CORAL, ic_tinta=BLANCO,
                                  espera="¡TE ESPERAMOS!", espera_f=LILITA, col_espera=CORAL))
        self.fondo = self._fondo()
        self._subs = {}
        self.estilo_sub = dict(fuente=FREDOKA, tam=58, color=CIRUELA, resaltado=CORAL, y=1660, caja=BLANCO, caja_alpha=0.97)

    def _fondo(self):
        f = np.zeros((H, W, 3), np.uint8)
        f[:] = ROSA
        for y in range(0, H + 120, 120):
            for x in range(0 if (y // 120) % 2 else 60, W + 120, 120):
                cv2.circle(f, (x, y), 14, ROSA2, -1, cv2.LINE_AA)
        return f

    def sfx(self):
        return [(t - 0.2, "whoosh") for _, t in self.cambios[1:]] + [(self.t_cierre - 0.25, "whoosh")] + \
               [(self.guion.palabra(k, 0) - 0.1, "pop") for k in self.orden[1:]]

    # ---- disposición del mosaico
    def disposicion(self, destacado):
        rects = {destacado: GRANDE}
        resto = [k for k in self.orden if k != destacado]
        x0 = (W - (len(resto) * FILA_W + (len(resto) - 1) * GAP)) / 2
        for i, k in enumerate(resto):
            rects[k] = (x0 + i * (FILA_W + GAP), FILA_Y, FILA_W, FILA_H)
        return rects

    def rects(self, t):
        idx = max(i for i, (_, c) in enumerate(self.cambios) if t >= c - 0.1)
        actual = self.disposicion(self.cambios[idx][0])
        if idx == 0:
            return actual, self.cambios[0][0], 1.0
        previo = self.disposicion(self.cambios[idx - 1][0])
        p = e_inout(clamp01((t - (self.cambios[idx][1] - 0.1)) / 0.65))
        mezcla = {k: tuple(a + (b - a) * p for a, b in zip(previo[k], actual[k])) for k in actual}
        return mezcla, self.cambios[idx][0], p

    def tile(self, f, k, r, t, zoom):
        x, y, w, h = [int(round(v)) for v in r]
        if w < 4 or h < 4:
            return
        cx, cy = self.foco[k]
        img = cover(self.img[k], w, h, cx, cy, zoom)
        rad = int(min(w, h) * 0.08) + 6
        m = mascara_redonda(w, h, rad)
        borde = caja(w + 16, h + 16, rad + 8, BLANCO)
        sh = caja(w + 16, h + 16, rad + 8, CIRUELA, 0.18)
        blit(f, sh, x + w / 2 + 8, y + h / 2 + 12)
        blit(f, borde, x + w / 2, y + h / 2)
        blit(f, np.dstack([img.astype(np.float32) * m[..., None], m]), x + w / 2, y + h / 2)

    def escena(self, t):
        f = self.fondo.copy()
        off = int((t * 18) % 120)
        f = np.roll(f, off, axis=0)
        q = prog(t, 0.1, 0.5)
        blit(f, self.titulo, W / 2, 175 - (1 - e_out(q)) * 60, alpha=clamp01(q * 3))
        blit(f, self.marca, W / 2, 245, alpha=clamp01(prog(t, 0.35, 0.4) * 3))
        rects, dest, p = self.rects(t)
        entra = prog(t, 0.0, 0.7)
        # pequeños primero, después el grande (queda arriba)
        for i, k in enumerate(self.orden):
            if k == dest:
                continue
            qi = prog(t, 0.9 + 0.15 * i, 0.5)
            if qi <= 0:
                continue
            x, y, w, h = rects[k]
            esc = max(e_back(qi, 1.8), 0.01)
            r = (x + w / 2 - w * esc / 2, y + h / 2 - h * esc / 2, w * esc, h * esc)
            self.tile(f, k, r, t, 1.08)
            if k != "intro":
                blit(f, self.badges[k], r[0] + 18, r[1] + 18, alpha=clamp01(qi * 3))
        x, y, w, h = rects[dest]
        esc = max(e_back(entra, 1.4), 0.01)
        cambio = next(c for kk, c in self.cambios if kk == dest)
        zoom = 1.04 + 0.12 * clamp01((t - cambio) / 3.5)
        self.tile(f, dest, (x + w / 2 - w * esc / 2, y + h / 2 - h * esc / 2, w * esc, h * esc), t, zoom)
        # nombre y detalle del destacado
        qn = prog(t, cambio + 0.45, 0.4) if dest != "intro" else prog(t, 0.5, 0.45)
        blit(f, self.sh_nombre[dest], W / 2 + 4, GRANDE[1] + GRANDE[3] + 12, alpha=clamp01(qn * 3) * p)
        blit(f, self.nombres[dest], W / 2, GRANDE[1] + GRANDE[3], alpha=clamp01(qn * 3) * p,
             escala=max(e_back(qn, 2.0), 0.01))
        if self.detalles[dest] is not None:
            qd = prog(t, cambio + 0.65, 0.4)
            blit(f, self.detalles[dest], W / 2, GRANDE[1] + GRANDE[3] + 105 + (1 - e_out(qd)) * 20, alpha=e_out(qd))
        return f

    def esc_cierre(self, t):
        f = np.roll(self.fondo.copy(), int((t * 18) % 120), axis=0)
        self.cierre.dibujar(f, t - self.t_cierre, y0=190, desde="alterno")
        return f

    def frame(self, t):
        t = min(t, self.dur - 1e-3)
        c = self.t_cierre
        if c - 0.3 <= t < c + 0.3:                      # el mosaico se va hacia arriba y entra el cierre
            p = e_inout((t - (c - 0.3)) / 0.6)
            a, b = self.escena(min(t, c - 1e-3)), self.esc_cierre(max(t, c))
            off = int(p * H)
            f = np.empty_like(a)
            f[:H - off] = a[off:]
            f[H - off:] = b[:off]
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
    ejecutar(Video(), "forralitas_cerdos")
