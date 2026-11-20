"""Video "Para tus gallinas" — estilo carrusel soleado: tarjetas que se deslizan como en las historias,
fondo de sol con rayos y huevitos que rebotan.   python gallinas.py  |  python gallinas.py --cuadros 1 5"""
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from base import (BALOO, FREDOKA, W, H, Cierre, Guion, T, a_sprite, ajustar, blit, caja, centrar, clamp01,  # noqa: E402
                  cover, e_back, e_inout, e_out, ejecutar, foto, mascara_redonda, prog, realzar, sobre, sombra,
                  subtitulos, AQUI)

AMA1, AMA2 = (255, 218, 96), (255, 168, 56)
MARRON = (92, 48, 18)
NARANJA = (232, 108, 28)
BLANCO = (255, 255, 255)
CREMA = (255, 248, 232)

CARTAS = [  # (clave, foto, foco (cx, cy), nombre, detalle)
    ("intro", "assets/nuevas/n01.png", (0.52, 0.40), "¿TENÉS GALLINAS?", "Tenemos todo lo que necesitan"),
    ("ponedora", "fotos_presentacion/10_ponedora.jpg", (0.5, 0.5), "PONEDORA", "Por bolsa y suelto"),
    ("afrecho", "fotos_presentacion/09_afrecho_maiz.jpg", (0.5, 0.5), "AFRECHO DE MAÍZ", "Por bolsa y suelto"),
    ("iniciador", "fotos_presentacion/11_iniciador_parrillero.jpg", (0.5, 0.5), "INICIADOR PARRILLERO", ""),
    ("terminador", "fotos_presentacion/12_engorde_terminador.jpg", (0.5, 0.5), "ENGORDE TERMINADOR", ""),
]
GUION = [
    ("intro", "¿Tenés gallinas? Tenemos todo lo que necesitan.", "¿Tenés *gallinas?* | Tenemos todo | lo que necesitan."),
    ("ponedora", "Ponedora, por bolsa y suelto.", "*Ponedora,* | por bolsa y suelto."),
    ("afrecho", "Afrecho de maíz, por bolsa y suelto.", "*Afrecho* de *maíz,* | por bolsa y suelto."),
    ("iniciador", "Iniciador parrillero.", "*Iniciador* *parrillero.*"),
    ("terminador", "Y engorde terminador.", "Y *engorde* *terminador.*"),
    ("fin", "Todo para tus gallinas, en Forralitas. ¡Te esperamos!",
     "Todo para tus *gallinas,* | en *Forralitas.* | *¡Te* *esperamos!*"),
]
CW, CH, FOTO = 660, 930, 660          # tarjeta y foto (cuadrada) de la tarjeta
CY = 1010                             # centro vertical de las tarjetas
PASO = 650


class Video:
    musica = os.path.join(AQUI, "musica", "Hillbilly_Swing.mp3")
    musica_inicio = 30.0

    def __init__(self):
        g = self.guion = Guion(GUION)
        self.img = {k: realzar(foto(r), 1.08, 0.10) for k, r, *_ in CARTAS}
        self.foco = {k: c for k, _, c, *_ in CARTAS}
        self.orden = [k for k, *_ in CARTAS]
        # ---- tiempos
        g["intro"]["t0"] = 0.7
        t = max(4.2, g.fin("intro") + 0.7)
        self.cambios = [0.0]
        for k in self.orden[1:]:
            g[k]["t0"] = t + 0.45
            self.cambios.append(t)
            t += max(3.0, g[k]["dur"] + 1.0)
        self.t_cierre = t
        g["fin"]["t0"] = t + 0.5
        self.dur = round(max(t + 8.0, g.fin("fin") + 4.5), 2)
        # ---- piezas
        self.mask_foto = mascara_redonda(FOTO, FOTO + 60, 44)[:FOTO]
        self.cartas = {}
        for k, _, _, n, d in CARTAS:
            base = caja(CW, CH, 44, BLANCO)
            tam = ajustar(n, BALOO, 76, CW - 70)
            base = centrar(base, T(n, BALOO, tam, MARRON), CW / 2, FOTO + 95)
            if d:
                base = centrar(base, T(d, FREDOKA, ajustar(d, FREDOKA, 44, CW - 80), NARANJA), CW / 2, FOTO + 190)
            self.cartas[k] = base
        self.sh_carta = sombra(self.cartas["intro"], 20, 0.25)
        self.titulo = T("PARA TUS GALLINAS", BALOO, 74, MARRON)
        self.marca = T("FORRALITAS", FREDOKA, 36, BLANCO)
        marca_pill = caja(self.marca.shape[1] - 24 + 50, 64, 32, NARANJA)
        self.marca = centrar(marca_pill, self.marca, marca_pill.shape[1] / 2, 34)
        self.huevo = self._huevo(70)
        self.cierre = Cierre(dict(titulo_f=BALOO, texto_f=FREDOKA, num_f=BALOO, col_titulo=MARRON, col_texto=MARRON,
                                  col_sub=NARANJA, tarjeta=CREMA, tarjeta_alpha=0.96, ic_fondo=NARANJA, ic_tinta=BLANCO,
                                  espera="¡TE ESPERAMOS!", espera_f=BALOO, col_espera=MARRON))
        yy, xx = np.mgrid[0:H // 4, 0:W // 4].astype(np.float32) * 4
        self._ang = np.arctan2(yy - 300, xx - W / 2)
        self._r = np.hypot(xx - W / 2, yy - 300) / np.hypot(W, H)
        t1 = np.linspace(0, 1, H // 4, dtype=np.float32)[:, None, None]
        self._grad = np.array(AMA1, np.float32) * (1 - t1) + np.array(AMA2, np.float32) * t1
        self._subs = {}
        self.estilo_sub = dict(fuente=FREDOKA, tam=58, color=MARRON, resaltado=NARANJA, y=1660, caja=BLANCO, caja_alpha=0.97)

    @staticmethod
    def _huevo(h):
        w = int(h * 0.78)
        L = 3
        m = np.zeros((h * L, w * L), np.uint8)
        cv2.ellipse(m, (w * L // 2, int(h * L * 0.56)), (w * L // 2 - 2, int(h * L * 0.44)), 0, 0, 360, 255, -1, cv2.LINE_AA)
        cv2.ellipse(m, (w * L // 2, int(h * L * 0.42)), (int(w * L * 0.40), int(h * L * 0.40)), 0, 180, 360, 255, -1,
                    cv2.LINE_AA)
        a = cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
        col = np.full((h, w, 3), (255, 250, 238), np.float32)
        col[: h // 2, : w // 2] = (255, 255, 255)
        return a_sprite(col, a)

    def sfx(self):
        return [(c - 0.15, "whoosh") for c in self.cambios[1:]] + [(self.t_cierre - 0.25, "whoosh")] + \
               [(self.guion.palabra(k, 0) - 0.05, "pop") for k in self.orden[1:]]

    def fondo(self, t):
        rayos = (np.sin(14 * (self._ang + t * 0.12)) > 0).astype(np.float32)
        rayos = cv2.GaussianBlur(rayos, (0, 0), 1.0)[..., None]
        f = self._grad * (1 + 0.07 * rayos) + (1 - np.clip(self._r * 3, 0, 1))[..., None] * 40
        f = cv2.resize(np.clip(f, 0, 255).astype(np.uint8), (W, H), interpolation=cv2.INTER_LINEAR)
        cv2.circle(f, (W // 2, 300), 120, (255, 236, 150), -1, cv2.LINE_AA)
        return f

    def huevos(self, f, t):
        for i, x in enumerate((90, 250, 830, 990)):
            fase = i * 0.7
            salto = abs(np.sin(t * 2.6 + fase)) * 26
            blit(f, self.huevo, x, 1520 - salto, ang=8 * np.sin(t * 2.6 + fase), escala=0.9 + 0.15 * (i % 2))

    def posicion(self, t):
        """Índice (con decimales) de la tarjeta que está en el centro."""
        s = 0.0
        for i, c in enumerate(self.cambios[1:], start=1):
            s += e_inout(clamp01((t - (c - 0.1)) / 0.6))
        return s

    def carta(self, f, i, s, t, dy=0.0, amul=1.0):
        k = self.orden[i]
        d = i - s
        if abs(d) > 1.7:
            return
        x = W / 2 + d * PASO
        esc = 1 - 0.18 * min(abs(d), 1)
        ang = -d * 6
        alpha = clamp01(1.9 - abs(d)) * (1 - 0.3 * min(abs(d), 1)) * amul
        spr = self.cartas[k].copy()
        cx, cy = self.foco[k]
        z = 1.05 + (0.10 * clamp01((t - self.cambios[i]) / 3.5) if abs(d) < 0.5 else 0)
        img = cover(self.img[k], FOTO, FOTO, cx, cy, z)
        spr = sobre(spr, np.dstack([img.astype(np.float32) * self.mask_foto[..., None], self.mask_foto]), 0, 0)
        blit(f, self.sh_carta, x + 8, CY + 18 + dy, alpha=alpha * 0.9, escala=esc, ang=ang)
        blit(f, spr, x, CY + dy, alpha=alpha, escala=esc, ang=ang)

    def escena(self, t):
        f = self.fondo(t)
        q = prog(t, 0.1, 0.5)
        blit(f, self.titulo, W / 2, 245 - (1 - e_out(q)) * 60, alpha=clamp01(q * 3))
        blit(f, self.marca, W / 2, 335, alpha=clamp01(prog(t, 0.35, 0.4) * 3), escala=max(e_back(prog(t, 0.35, 0.4), 2), 0.01))
        s = self.posicion(t)
        qe = prog(t, 0.0, 0.7)
        for i in sorted(range(len(self.orden)), key=lambda j: -abs(j - s)):   # la del centro queda arriba
            self.carta(f, i, s, t, dy=(1 - e_out(qe)) * 600, amul=clamp01(qe * 3))
        # puntitos del carrusel
        n = len(self.orden)
        for i in range(n):
            x = W / 2 + (i - (n - 1) / 2) * 44
            act = clamp01(1 - abs(i - s))
            cv2.circle(f, (int(x), 1515), int(10 + 6 * act), BLANCO if act > 0.5 else (255, 238, 200), -1, cv2.LINE_AA)
        self.huevos(f, t)
        return f

    def esc_cierre(self, t):
        f = self.fondo(t)
        self.cierre.dibujar(f, t - self.t_cierre, y0=190, desde="alterno")
        return f

    def frame(self, t):
        t = min(t, self.dur - 1e-3)
        c = self.t_cierre
        if c - 0.3 <= t < c + 0.3:                       # círculo que se abre desde el centro
            p = e_inout((t - (c - 0.3)) / 0.6)
            a, b = self.escena(min(t, c - 1e-3)), self.esc_cierre(max(t, c))
            m = np.zeros((H, W), np.uint8)
            cv2.circle(m, (W // 2, H // 2), int(p * 1150), 255, -1, cv2.LINE_AA)
            m = (m.astype(np.float32) / 255)[..., None]
            f = (a * (1 - m) + b * m).astype(np.uint8)
            cv2.circle(f, (W // 2, H // 2), int(p * 1150), BLANCO, 10, cv2.LINE_AA)
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
    ejecutar(Video(), "forralitas_gallinas")
