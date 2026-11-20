"""Video "Para tus mascotas" — estilo pastel con huellitas: cada producto en un círculo con anillo que gira,
el nombre en un globito de diálogo y huellitas que caminan.   python mascotas.py  |  python mascotas.py --cuadros 1 5"""
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from base import (BALOO, FREDOKA, LILITA, W, H, Cierre, Guion, T, a_sprite, ajustar, blit, caja, centrar,  # noqa: E402
                  clamp01, cover, e_back, e_inout, e_out, ejecutar, foto, mascara_circulo, prog, realzar,
                  recorte_png, sobre, sombra, subtitulos, AQUI)

CELESTE, CELESTE2 = (196, 228, 250), (172, 212, 244)
AZUL = (26, 48, 96)
NARANJA = (255, 138, 52)
ROSA = (255, 122, 160)
BLANCO = (255, 255, 255)
D = 780                     # diámetro del círculo
CX, CY = W / 2, 860

ITEMS = [  # (clave, tipo, fuente(s), foco/zoom, nombre, detalle)
    ("intro", "foto", "fotos/02_perros_gatos.jpg", (0.50, 0.50, 1.15), "¡PARA TUS MASCOTAS!", "Lo mejor para ellos"),
    ("sabrositos", "foto", "fotos/01_perros_sabrositos.jpg", (0.42, 0.52, 1.25), "SABROSITOS", "Para perros"),
    ("wenuy", "foto", "fotos/02_perros_gatos.jpg", (0.41, 0.42, 2.6), "WENUY", "Cachorros y adultos"),
    ("gatos", "png", ["assets/oferta/sabrositos_mix_bolsa.png", "assets/oferta/sabrositos_pescado_bolsa.png"], None,
     "SABROSITOS GATO", "Sabor mix y pescado"),
    ("piedras", "png", ["assets/oferta/piedras_rec.png"], None, "PIEDRAS SANITARIAS", "Bolsa de 1 kg"),
]
GUION = [
    ("intro", "¡Para tus mascotas, lo mejor!", "¡Para tus *mascotas,* | lo *mejor!*"),
    ("sabrositos", "Sabrositos, para perros.", "*Sabrositos,* para *perros.*"),
    ("wenuy", "Güenuy, para cachorros y adultos.", "*Wenuy,* | para *cachorros* y *adultos.*"),
    ("gatos", "Sabrositos para gatos, sabor mix y pescado.", "*Sabrositos* para *gatos,* | sabor *mix* y *pescado.*"),
    ("piedras", "Y piedras sanitarias, en bolsa de un kilo.", "Y *piedras* *sanitarias,* | en bolsa de *1* *kilo.*"),
    ("fin", "Todo para tus mascotas, en Forralitas. ¡Te esperamos!",
     "Todo para tus *mascotas,* | en *Forralitas.* | *¡Te* *esperamos!*"),
]


def huella(l, color, alpha=1.0):
    L = l * 3
    m = np.zeros((L, L), np.uint8)
    cv2.ellipse(m, (L // 2, int(L * 0.66)), (int(L * 0.26), int(L * 0.21)), 0, 0, 360, 255, -1, cv2.LINE_AA)
    for dx, dy, r in ((-0.30, 0.34, 0.11), (-0.11, 0.20, 0.115), (0.11, 0.20, 0.115), (0.30, 0.34, 0.11)):
        cv2.ellipse(m, (int(L / 2 + dx * L), int(dy * L)), (int(r * L), int(r * L * 1.25)), 0, 0, 360, 255, -1, cv2.LINE_AA)
    a = cv2.resize(m, (l, l), interpolation=cv2.INTER_AREA).astype(np.float32) / 255 * alpha
    return a_sprite(np.full((l, l, 3), color, np.float32), a)


def fp_rot(spr, ang):
    h, w = spr.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), ang, 1.0)
    return cv2.warpAffine(spr, M, (w, h), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))


def globo(nombre, detalle):
    tam = ajustar(nombre, FREDOKA, 74, 860)
    s1 = T(nombre, FREDOKA, tam, AZUL)
    s2 = T(detalle, FREDOKA, 44, NARANJA) if detalle else None
    pad = int(tam * 0.35)
    w = max(s1.shape[1] - 2 * pad, (s2.shape[1] - 30) if s2 is not None else 0) + 110
    h = 190 if s2 is not None else 130
    base = np.zeros((h + 34, w, 4), np.float32)
    base = sobre(base, caja(w, h, 60, BLANCO), 0, 34)
    tri = np.zeros((40, 70), np.uint8)
    cv2.fillPoly(tri, [np.array([[0, 39], [69, 39], [35, 0]])], 255, cv2.LINE_AA)
    a = tri.astype(np.float32) / 255
    base = sobre(base, a_sprite(np.full((40, 70, 3), BLANCO, np.float32), a), w // 2 - 35, 0)
    base = centrar(base, s1, w / 2, 34 + (62 if s2 is not None else h / 2) + 4)
    if s2 is not None:
        base = centrar(base, s2, w / 2, 34 + 140)
    return base


class Video:
    musica = os.path.join(AQUI, "musica", "Life_of_Riley.mp3")
    musica_inicio = 5.0

    def __init__(self):
        g = self.guion = Guion(GUION)
        self.mask = mascara_circulo(D)
        self.img, self.pngs = {}, {}
        for k, tipo, src, cam, *_ in ITEMS:
            if tipo == "foto":
                self.img[k] = realzar(foto(src, 3200), 1.06, 0.08)
            else:
                self.pngs[k] = [recorte_png(p, 600 if len(src) == 1 else 560) for p in src]
        self.cam = {k: c for k, _, _, c, *_ in ITEMS}
        self.tipo = {k: tp for k, tp, *_ in ITEMS}
        self.orden = [k for k, *_ in ITEMS]
        # ---- tiempos
        g["intro"]["t0"] = 0.7
        t = max(3.8, g.fin("intro") + 0.9)
        self.cambios = [("intro", 0.0)]
        for k in self.orden[1:]:
            g[k]["t0"] = t + 0.5
            self.cambios.append((k, t))
            t += max(3.2, g[k]["dur"] + 1.1)
        self.t_cierre = t
        g["fin"]["t0"] = t + 0.5
        self.dur = round(max(t + 8.0, g.fin("fin") + 4.5), 2)
        # ---- piezas
        self.globos = {k: globo(n, d) for k, _, _, _, n, d in ITEMS}
        self.sh_globo = {k: sombra(v, 12, 0.18) for k, v in self.globos.items()}
        self.huella = huella(70, AZUL, 0.10)
        self.huella_fondo = fp_rot(huella(90, BLANCO, 0.35), -20)
        self.huella_paso = fp_rot(huella(64, NARANJA), -90)
        self.sh_bolsas = {k: [sombra(b, 14, 0.25) for b in v] for k, v in self.pngs.items()}
        self.anillo = self._anillo()
        self.huella_ok = huella(46, NARANJA)
        self.huella_no = huella(46, (150, 186, 222))
        self.marca = T("FORRALITAS", LILITA, 50, AZUL)
        self.cierre = Cierre(dict(titulo_f=LILITA, texto_f=FREDOKA, num_f=BALOO, col_titulo=AZUL, col_texto=AZUL,
                                  col_sub=NARANJA, tarjeta=BLANCO, tarjeta_alpha=0.95, ic_fondo=NARANJA, ic_tinta=BLANCO,
                                  espera="¡TE ESPERAMOS!", espera_f=LILITA, col_espera=NARANJA))
        t1 = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
        self.fondo0 = (np.array(CELESTE, np.float32) * (1 - t1) + np.array(CELESTE2, np.float32) * t1 *
                       np.ones((1, W, 1), np.float32)).astype(np.uint8)
        self._subs = {}
        self.estilo_sub = dict(fuente=FREDOKA, tam=58, color=AZUL, resaltado=NARANJA, y=1665, caja=BLANCO, caja_alpha=0.97)

    @staticmethod
    def _anillo():
        anillo = np.zeros((D + 120, D + 120), np.uint8)
        cv2.circle(anillo, ((D + 120) // 2,) * 2, D // 2 + 22, 255, 22, cv2.LINE_AA)
        a = anillo.astype(np.float32) / 255
        return a_sprite(np.full(a.shape + (3,), NARANJA, np.float32), a)

    def sfx(self):
        return [(c - 0.2, "whoosh") for _, c in self.cambios[1:]] + [(self.t_cierre - 0.25, "whoosh")] + \
               [(c + 0.05, "pop") for _, c in self.cambios[1:]]

    def fondo(self, t):
        f = self.fondo0.copy()
        off = (t * 40) % 240
        for j, y in enumerate(range(-240, H + 240, 240)):
            for i, x in enumerate(range(-120 if j % 2 else 0, W + 240, 240)):
                blit(f, self.huella_fondo, x + off * 0.6, y + off)
        return f

    def contenido(self, k, t, t0):
        """Lo que va dentro del círculo (foto con zoom lento o bolsas que rebotan)."""
        if self.tipo[k] == "foto":
            cx, cy, z = self.cam[k]
            return cover(self.img[k], D, D, cx, cy, z * (1 + 0.08 * clamp01((t - t0) / 3.5))), None
        return np.full((D, D, 3), (255, 248, 236), np.uint8), self.pngs[k]

    def circulo(self, f, k, t, t0, esc, ang):
        if esc <= 0.02:
            return
        img, bolsas = self.contenido(k, t, t0)
        disco = np.dstack([img.astype(np.float32) * self.mask[..., None], self.mask])
        # anillos
        c = ((D + 120) // 2,) * 2
        blit(f, self.anillo, CX, CY, escala=esc)
        punt = np.zeros((D + 120, D + 120), np.uint8)
        for i in range(36):
            a0 = i * 10 + t * 30 + ang
            cv2.ellipse(punt, c, (D // 2 + 52, D // 2 + 52), 0, a0, a0 + 5, 255, 8, cv2.LINE_AA)
        p = punt.astype(np.float32) / 255
        blit(f, a_sprite(np.full(p.shape + (3,), AZUL, np.float32), p), CX, CY, escala=esc)
        blit(f, disco, CX, CY, escala=esc, ang=ang)
        if bolsas:
            n = len(bolsas)
            for i, b in enumerate(bolsas):
                q = prog(t, t0 + 0.25 + 0.15 * i, 0.5)
                x = CX + (i - (n - 1) / 2) * 330 * esc
                salto = 14 * np.sin((t - t0) * 3 + i)
                blit(f, self.sh_bolsas[k][i], x + 10, CY + 30 + 18, alpha=clamp01(q * 3), escala=esc)
                blit(f, b, x, CY + 30 - salto - (1 - e_out(q)) * 300, alpha=clamp01(q * 3),
                     escala=esc * max(e_back(q, 1.8), 0.01), ang=(i - (n - 1) / 2) * 6)

    def huellitas(self, f, t):
        """Huellitas que cruzan caminando cuando cambia el producto."""
        for _, c in self.cambios[1:]:
            tl = t - (c - 0.3)
            if 0 <= tl <= 1.4:
                for i in range(8):
                    ti = i * 0.1
                    if tl < ti:
                        continue
                    a = clamp01(1 - (tl - ti) / 0.9)
                    x = 80 + i * 130
                    y = 1365 + (22 if i % 2 else -22)
                    blit(f, self.huella_paso, x, y, alpha=a)

    def escena(self, t):
        f = self.fondo(t)
        q = prog(t, 0.1, 0.5)
        blit(f, self.marca, W / 2, 175 - (1 - e_out(q)) * 60, alpha=clamp01(q * 3))
        # progreso con huellitas
        n = len(self.orden) - 1
        idx = max(i for i, (_, c) in enumerate(self.cambios) if t >= c)
        for i in range(n):
            x = W / 2 + (i - (n - 1) / 2) * 70
            blit(f, self.huella_ok if i < idx else self.huella_no, x, 255, alpha=clamp01(q * 3))
        k, c = self.cambios[idx]
        # el círculo anterior se achica girando, el nuevo entra con rebote
        if idx > 0 and t < c + 0.35:
            kp, cp = self.cambios[idx - 1]
            sale = e_inout(clamp01((t - c + 0.15) / 0.35))
            self.circulo(f, kp, t, cp, 1 - sale, sale * 90)
        qe = prog(t, c + (0.15 if idx else 0.05), 0.55)
        self.circulo(f, k, t, c, max(e_back(qe, 1.7), 0.0), (1 - e_out(qe)) * -40)
        qg = prog(t, c + 0.4, 0.45)
        y = 1390
        blit(f, self.sh_globo[k], W / 2 + 4, y + 10, alpha=clamp01(qg * 3))
        blit(f, self.globos[k], W / 2, y, alpha=clamp01(qg * 3), escala=max(e_back(qg, 2.2), 0.01))
        self.huellitas(f, t)
        return f

    def esc_cierre(self, t):
        f = self.fondo(t)
        self.cierre.dibujar(f, t - self.t_cierre, y0=190, desde="alterno")
        return f

    def frame(self, t):
        t = min(t, self.dur - 1e-3)
        c = self.t_cierre
        if c - 0.3 <= t < c + 0.3:                       # el cierre entra como una burbuja desde abajo
            p = e_inout((t - (c - 0.3)) / 0.6)
            a, b = self.escena(min(t, c - 1e-3)), self.esc_cierre(max(t, c))
            m = np.zeros((H, W), np.uint8)
            cv2.circle(m, (W // 2, H + 200), int(p * 2400), 255, -1, cv2.LINE_AA)
            m = (m.astype(np.float32) / 255)[..., None]
            f = (a * (1 - m) + b * m).astype(np.uint8)
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
    ejecutar(Video(), "forralitas_mascotas")
