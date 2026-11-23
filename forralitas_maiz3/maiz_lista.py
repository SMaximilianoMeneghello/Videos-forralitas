"""Maíz — diseño B "LISTA": fondo crema con verde y dorado, el video en una tarjeta redondeada, un sello giratorio
"PRIMERA CALIDAD" y una lista que se va tildando (primera calidad, bolsas, mayor y menor, envíos).
Las tarjetas de video se apilan una encima de la otra.   python maiz_lista.py  |  python maiz_lista.py --cuadros 1 5"""
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comun import MUSICA, Tramo, W, H, base, encuadre  # noqa: E402

fp = base.fp
T, blit, caja, centrar, sombra = base.T, base.blit, base.caja, base.centrar, base.sombra
prog, clamp01, e_out, e_inout, e_back = base.prog, base.clamp01, base.e_out, base.e_inout, base.e_back
BEBAS = os.path.join(base.RAIZ, "forralitas_video_final", "proyecto", fp.F_BEBAS)
MONT = base.MONT
CREMA = (246, 240, 226)
CREMA2 = (236, 226, 202)
VERDE = (26, 82, 46)
VERDE2 = (16, 56, 31)
ORO = (232, 160, 22)
BLANCO = (255, 255, 255)

GUION = [
    ("llenado", "¿Buscás maíz de primera calidad? En Forralitas lo tenemos.",
     "¿Buscás *maíz* | de *primera* *calidad?* | En *Forralitas* | lo *tenemos.*"),
    ("pilas", "Bolsas de cuarenta y cincuenta kilos, con venta por mayor y menor.",
     "Bolsas de *40* y *50* *kilos,* | con venta por *mayor* y *menor.*"),
    ("calidad", "Fijate qué grano. Y te lo llevamos, con envíos según la zona.",
     "Fijate qué *grano.* | Y te lo *llevamos,* | con *envíos* según la *zona.*"),
    ("fin", "Pedilo por WhatsApp o vení a buscarlo. ¡Te esperamos!",
     "Pedilo por *WhatsApp* | o vení a *buscarlo.* | *¡Te* *esperamos!*"),
]
ORDEN = ["llenado", "pilas", "calidad"]
ETIQUETA = {"llenado": "LLENANDO LAS BOLSAS", "pilas": "EN EL DEPÓSITO", "calidad": "MIRÁ EL GRANO"}
FOCO = {"llenado": (0.5, 0.45), "pilas": (0.5, 0.42), "calidad": (0.5, 0.45)}
# lista: (texto, clave del guion, índice de la palabra que la tilda)
LISTA = [("Maíz de primera calidad", "llenado", 4), ("Bolsas de 40 kg y 50 kg", "pilas", 0),
         ("Venta por mayor y menor", "pilas", 8), ("Envíos según la zona", "calidad", 8)]
VX, VY, VW, VH = 540, 840, 880, 1000      # centro y tamaño de la tarjeta de video
LISTA_Y, LISTA_DY = 1405, 74


def sello(d, texto, fuente, centro_txt):
    """Sello circular dorado con texto alrededor (se dibuja grande y se reduce)."""
    ss = 3
    L = d * ss
    im = Image.new("RGBA", (L, L), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    dr.ellipse((0, 0, L - 1, L - 1), fill=ORO + (255,))
    dr.ellipse((L * 0.06, L * 0.06, L * 0.94, L * 0.94), outline=VERDE2 + (255,), width=int(3 * ss))
    dr.ellipse((L * 0.27, L * 0.27, L * 0.73, L * 0.73), fill=VERDE + (255,))
    f = fp.fuente(fuente, int(d * 0.12 * ss))
    r = L * 0.385
    paso = 360 / len(texto)
    for i, ch in enumerate(texto):
        ang = -90 + i * paso
        g = Image.new("RGBA", (int(f.size * 1.6), int(f.size * 1.6)), (0, 0, 0, 0))
        ImageDraw.Draw(g).text((g.width / 2, g.height / 2), ch, font=f, fill=VERDE2 + (255,), anchor="mm")
        g = g.rotate(-(ang + 90), resample=Image.BICUBIC)
        x = L / 2 + r * np.cos(np.radians(ang)) - g.width / 2
        y = L / 2 + r * np.sin(np.radians(ang)) - g.height / 2
        im.alpha_composite(g, (int(x), int(y)))
    fc = fp.fuente(BEBAS, int(d * 0.20 * ss))
    ImageDraw.Draw(im).text((L / 2, L / 2 + ss * 2), centro_txt, font=fc, fill=CREMA + (255,), anchor="mm")
    im = im.resize((d, d), Image.LANCZOS)
    a = np.asarray(im, np.float32)
    a[..., :3] *= a[..., 3:4] / 255
    a[..., 3] /= 255
    return a


def tilde(d, p):
    """Círculo con tilde dibujada hasta la fracción p."""
    L = d * 3
    m = np.zeros((L, L), np.uint8)
    col = np.zeros((L, L, 3), np.uint8)
    cv2.circle(m, (L // 2, L // 2), L // 2 - 2, 255, -1, cv2.LINE_AA)
    col[:] = VERDE if p > 0 else CREMA2
    pts = [(0.27, 0.52), (0.44, 0.68), (0.74, 0.35)]
    pts = [(int(x * L), int(y * L)) for x, y in pts]
    tl = np.zeros((L, L), np.uint8)
    if p > 0:
        a = min(p * 2, 1)
        q = (int(pts[0][0] + (pts[1][0] - pts[0][0]) * a), int(pts[0][1] + (pts[1][1] - pts[0][1]) * a))
        cv2.line(tl, pts[0], q, 255, int(L * 0.11), cv2.LINE_AA)
        if p > 0.5:
            b = (p - 0.5) * 2
            q2 = (int(pts[1][0] + (pts[2][0] - pts[1][0]) * b), int(pts[1][1] + (pts[2][1] - pts[1][1]) * b))
            cv2.line(tl, pts[1], q2, 255, int(L * 0.11), cv2.LINE_AA)
    tlf = tl.astype(np.float32)[..., None] / 255
    col = col.astype(np.float32) * (1 - tlf) + np.array(CREMA, np.float32) * tlf
    m = cv2.resize(m, (d, d), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    col = cv2.resize(col, (d, d), interpolation=cv2.INTER_AREA)
    return np.dstack([col * m[..., None], m])


class Video:
    musica = os.path.join(MUSICA, "Wholesome.mp3")
    musica_inicio = 4.0

    def __init__(self):
        self.tramos = {k: Tramo(k) for k in ORDEN}
        g = self.guion = base.Guion(GUION)
        t = 0.0
        self.ini = {}
        for k in ORDEN:
            self.ini[k] = t
            t += self.tramos[k].dur
        self.t_cierre = t
        g["llenado"]["t0"] = 1.0
        g["pilas"]["t0"] = self.ini["pilas"] + 0.6
        g["calidad"]["t0"] = self.ini["calidad"] + 0.5
        g["fin"]["t0"] = self.t_cierre + 0.7
        self.dur = round(max(self.t_cierre + 8.5, g.fin("fin") + 4.0), 2)
        # ---- piezas
        self.fondo = self._fondo()
        self.titulo = T("MAÍZ", BEBAS, 190, VERDE)
        s = T("DE PRIMERA CALIDAD", MONT, 46, CREMA)
        self.sub = centrar(caja(s.shape[1] - 32 + 50, 76, 38, VERDE), s, (s.shape[1] - 32 + 50) / 2, 38)
        self.sello = sello(250, "PRIMERA CALIDAD • PRIMERA CALIDAD • ", MONT, "MAÍZ")
        self.sh_sello = sombra(self.sello, 14, 0.30)
        self.logo = fp.logo_circular(120)
        self.marco = caja(VW + 24, VH + 24, 48, BLANCO)
        self.sh_marco = sombra(self.marco, 26, 0.32)
        self.mask = base.mascara_redonda(VW, VH, 38)
        self.etq = {}
        for k in ORDEN:
            s = T(ETIQUETA[k], BEBAS, 54, CREMA)
            w = s.shape[1] - 38 + 56
            self.etq[k] = centrar(caja(w, 78, 14, VERDE2, 0.92), s, w / 2, 41)
        self.items = [T(txt, MONT, 46, VERDE2) for txt, *_ in LISTA]
        self.tildes = {}
        self.cierre = base.Cierre(dict(titulo_f=BEBAS, texto_f=MONT, num_f=BEBAS, col_titulo=CREMA, col_texto=VERDE2,
                                       col_sub=(176, 112, 0), tarjeta=CREMA, tarjeta_alpha=0.97, ic_fondo=ORO,
                                       ic_tinta=VERDE2, espera="¡TE ESPERAMOS!", espera_f=BEBAS, col_espera=ORO))
        self.cierre.rubro = T(base.DATOS["rubro"], MONT, 36, ORO)
        self.fondo_cierre = self._fondo_cierre()
        self._subs = {}
        self.estilo_sub = dict(fuente=MONT, tam=54, color=CREMA, resaltado=ORO, y=1745, caja=VERDE2, caja_alpha=0.97)

    def _fondo(self):
        f = np.zeros((H, W, 3), np.float32)
        f[:] = CREMA
        rng = np.random.default_rng(7)
        ruido = cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 1.2)
        f += ruido[..., None] * 3
        # granos de maíz dibujados muy suaves
        for _ in range(70):
            x, y = int(rng.uniform(0, W)), int(rng.uniform(0, H))
            ang = rng.uniform(0, 180)
            cv2.ellipse(f, (x, y), (14, 10), ang, 0, 360, CREMA2, -1, cv2.LINE_AA)
        cv2.circle(f, (W + 60, 120), 330, (240, 214, 150), -1, cv2.LINE_AA)
        return np.clip(f, 0, 255).astype(np.uint8)

    def _fondo_cierre(self):
        f = np.zeros((H, W, 3), np.float32)
        f[:] = VERDE
        y = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
        f = f * (1 - 0.35 * y) + np.array(VERDE2, np.float32) * 0.35 * y
        rng = np.random.default_rng(3)
        for _ in range(60):
            x, yy = int(rng.uniform(0, W)), int(rng.uniform(0, H))
            cv2.ellipse(f, (x, yy), (14, 10), rng.uniform(0, 180), 0, 360, (36, 96, 56), -1, cv2.LINE_AA)
        cv2.circle(f, (-80, H - 60), 360, (36, 96, 56), -1, cv2.LINE_AA)
        return np.clip(f, 0, 255).astype(np.uint8)

    def sfx(self):
        s = [(self.ini[k] - 0.25, "whoosh") for k in ORDEN[1:]] + [(self.t_cierre - 0.3, "whoosh")]
        return s + [(self.guion.palabra(k, i) + 0.05, "pop") for _, k, i in LISTA]

    # ---------------------------------------------------------------- tarjeta de video
    def tarjeta(self, k, t):
        tl = t - self.ini[k]
        z = 1.02 + 0.08 * clamp01(tl / self.tramos[k].dur)
        cx, cy = FOCO[k]
        img = encuadre(self.tramos[k].cuadro(tl), VW, VH, cx, cy, z)
        spr = base.sobre(self.marco, base.a_sprite(img, self.mask), 12, 12)
        e = self.etq[k]
        return base.sobre(spr, e, 40, VH - 70)

    def dibujar_tarjeta(self, f, k, t, dy=0.0, ang=0.0, esc=1.0, osc=0.0, alpha=1.0):
        spr = self.tarjeta(k, t)
        if osc > 0:
            spr = spr.copy()
            spr[..., :3] *= 1 - 0.35 * osc
        blit(f, self.sh_marco, VX + 6, VY + 22 + dy, alpha=alpha, escala=esc, ang=ang)
        blit(f, spr, VX, VY + dy, alpha=alpha, escala=esc, ang=ang)

    def escena(self, t):
        f = self.fondo.copy()
        # título
        q = prog(t, 0.05, 0.5)
        blit(f, self.titulo, 70 + self.titulo.shape[1] / 2 - 60, 190 - (1 - e_out(q)) * 80, alpha=clamp01(q * 3))
        q2 = prog(t, 0.35, 0.45)
        blit(f, self.sub, 70 + self.sub.shape[1] / 2 - (1 - e_out(q2)) * 700, 312, alpha=clamp01(q2 * 3))
        blit(f, self.logo, W - 120, 190, alpha=clamp01(prog(t, 0.5, 0.4) * 3),
             escala=max(e_back(prog(t, 0.5, 0.4), 1.8), 0.01))
        # lista que se va tildando
        for i, ((txt, k, w), item) in enumerate(zip(LISTA, self.items)):
            y = LISTA_Y + i * LISTA_DY
            qa = prog(t, 1.2 + 0.12 * i, 0.45)
            if qa <= 0:
                continue
            tp = clamp01((t - self.guion.palabra(k, w)) / 0.35)
            clave = round(tp * 12) / 12
            if clave not in self.tildes:
                self.tildes[clave] = tilde(58, clave)
            dx = (1 - e_out(qa)) * -500
            blit(f, self.tildes[clave], 110 + dx, y, alpha=clamp01(qa * 3), escala=1 + 0.25 * np.sin(np.pi * tp))
            a = clamp01(qa * 3) * (0.45 + 0.55 * clamp01(tp * 2))
            blit(f, item, 160 + item.shape[1] / 2 - 16 + dx, y + 2, alpha=a)
        # tarjetas apiladas
        actual = max(i for i, k in enumerate(ORDEN) if t >= self.ini[k] - 0.45)
        qe = prog(t, 0.0, 0.7)
        if actual == 0:
            self.dibujar_tarjeta(f, "llenado", t, dy=(1 - e_out(qe)) * 1300, ang=(1 - e_out(qe)) * -8)
        else:
            k, kp = ORDEN[actual], ORDEN[actual - 1]
            p = clamp01((t - (self.ini[k] - 0.45)) / 0.75)
            if p < 1:
                self.dibujar_tarjeta(f, kp, min(t, self.ini[k] - 1e-3), esc=1 - 0.06 * e_out(p), ang=3 * e_out(p),
                                     osc=e_out(p))
            ang = -2.5 * (1 - e_back(p, 1.4)) * (1 if actual % 2 else -1) + (-6 * (1 - e_out(p)))
            self.dibujar_tarjeta(f, k, max(t, self.ini[k]), dy=(1 - e_out(p)) * 1400, ang=ang)
        # sello
        qs = prog(t, 0.9, 0.5)
        blit(f, self.sh_sello, 905, 405, alpha=clamp01(qs * 3), escala=max(e_back(qs, 2.0), 0.01))
        blit(f, self.sello, 900, 395, alpha=clamp01(qs * 3), escala=max(e_back(qs, 2.0), 0.01), ang=-t * 30)
        return f

    def esc_cierre(self, t):
        f = self.fondo_cierre.copy()
        self.cierre.dibujar(f, t - self.t_cierre, y0=190, desde="alterno")
        return f

    def frame(self, t):
        t = min(t, self.dur - 1e-3)
        c = self.t_cierre
        if c - 0.35 <= t < c + 0.35:                      # telón verde con borde redondeado que sube
            p = e_inout((t - (c - 0.35)) / 0.7)
            a, b = self.escena(min(t, c - 1e-3)), self.esc_cierre(max(t, c))
            borde = int(H + 300 - p * (H + 600))
            m = np.zeros((H, W), np.uint8)
            cv2.ellipse(m, (W // 2, borde + 300), (W, 300), 0, 180, 360, 255, -1, cv2.LINE_AA)
            m[max(0, borde + 300):] = 255
            m = (m.astype(np.float32) / 255)[..., None]
            f = (a * (1 - m) + b * m).astype(np.uint8)
        elif t < c:
            f = self.escena(t)
        else:
            f = self.esc_cierre(t)
        f = np.ascontiguousarray(f)
        base.subtitulos(f, self.guion, t, self.estilo_sub, self._subs)
        if t < 0.2:
            f = (f.astype(np.float32) * (t / 0.2)).astype(np.uint8)
        if t > self.dur - 0.5:
            f = (f.astype(np.float32) * ((self.dur - t) / 0.5)).astype(np.uint8)
        return f


if __name__ == "__main__":
    base.ejecutar(Video(), "forralitas_maiz_lista")
