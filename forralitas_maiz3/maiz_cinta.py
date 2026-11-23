"""Maíz — diseño A "CINTA": video a pantalla completa, tipografía grande que golpea, franja con texto que corre
y transiciones con rayas amarillas y negras (estilo cinta de obra/depósito).
python maiz_cinta.py  |  python maiz_cinta.py --cuadros 1 5"""
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comun import MUSICA, Tramo, W, H, base, encuadre  # noqa: E402

fp = base.fp
T, blit, caja, centrar, sombra = base.T, base.blit, base.caja, base.centrar, base.sombra
prog, clamp01, e_out, e_inout, e_back = base.prog, base.clamp01, base.e_out, base.e_inout, base.e_back
ANTON, MONT = base.ANTON, base.MONT
AMARILLO = (255, 204, 0)
NEGRO = (18, 18, 18)
BLANCO = (255, 255, 255)

GUION = [
    ("llenado", "Maíz de primera calidad, acá en Forralitas.",
     "*MAÍZ* DE *PRIMERA* *CALIDAD,* | ACÁ EN *FORRALITAS.*"),
    ("pilas", "En bolsas de cuarenta y cincuenta kilos. Venta por mayor y menor.",
     "EN BOLSAS DE *40* Y *50* *KILOS.* | VENTA POR *MAYOR* Y *MENOR.*"),
    ("calidad", "Mirá la calidad del grano. Y hacemos envíos según la zona.",
     "MIRÁ LA *CALIDAD* | DEL *GRANO.* | Y HACEMOS *ENVÍOS* | SEGÚN LA *ZONA.*"),
    ("fin", "Vení a visitarnos o escribinos por WhatsApp. ¡Te esperamos!",
     "VENÍ A *VISITARNOS* | O ESCRIBINOS POR *WHATSAPP.* | *¡TE* *ESPERAMOS!*"),
]
CAPITULOS = [("llenado", "01", "EL LLENADO"), ("pilas", "02", "EL DEPÓSITO"), ("calidad", "03", "EL GRANO")]
ENCUADRE = {"llenado": (0.5, 0.5), "pilas": (0.5, 0.5), "calidad": (0.5, 0.5)}
TICKER = "MAÍZ DE PRIMERA CALIDAD  •  VENTA POR MAYOR Y MENOR  •  ENVÍOS SEGÚN LA ZONA  •  "
TR = 0.32          # media duración de la transición con rayas


def rayas(w, h, ancho=46, a=AMARILLO, b=NEGRO):
    yy, xx = np.mgrid[0:h, 0:w]
    m = (((xx + yy) // ancho) % 2).astype(bool)
    out = np.empty((h, w, 3), np.uint8)
    out[m], out[~m] = a, b
    return out


class Video:
    musica = os.path.join(MUSICA, "Funkorama.mp3")
    musica_inicio = 12.0

    def __init__(self):
        self.tramos = {k: Tramo(k) for k, *_ in CAPITULOS}
        g = self.guion = base.Guion(GUION)
        # ---- tiempos: cada tramo dura lo que dura el video elegido
        t = 0.0
        self.ini = {}
        for k, *_ in CAPITULOS:
            self.ini[k] = t
            t += self.tramos[k].dur
        self.t_cierre = t
        g["llenado"]["t0"] = 1.3
        g["pilas"]["t0"] = self.ini["pilas"] + 0.7
        g["calidad"]["t0"] = self.ini["calidad"] + 0.5
        g["fin"]["t0"] = self.t_cierre + 0.6
        self.dur = round(max(self.t_cierre + 8.5, g.fin("fin") + 4.0), 2)
        # ---- piezas
        self.maiz = T("MAÍZ", ANTON, 330, AMARILLO, trazo=6, trazo_col=NEGRO)
        self.sh_maiz = sombra(self.maiz, 24, 0.55)
        s = T("DE PRIMERA CALIDAD", ANTON, 92, NEGRO)
        self.primera = centrar(caja(s.shape[1] - 60 + 70, 130, 6, AMARILLO), s, (s.shape[1] - 60 + 70) / 2, 66)
        self.logo = fp.logo_circular(132)
        self.caps = {}
        for k, n, txt in CAPITULOS:
            num = T(n, ANTON, 64, NEGRO)
            nom = T(txt, ANTON, 54, BLANCO)
            w = num.shape[1] + nom.shape[1] - 40
            spr = caja(w + 30, 96, 6, NEGRO, 0.85)
            spr = sobre_izq(spr, caja(num.shape[1] - 10, 96, 6, AMARILLO), 0)
            spr = sobre_izq(spr, num, 2, -2)
            spr = sobre_izq(spr, nom, num.shape[1] - 6, 0)
            self.caps[k] = spr
        # carteles de cada tramo
        self.kg = T("BOLSAS DE 40 KG Y 50 KG", ANTON, 96, AMARILLO, trazo=4, trazo_col=NEGRO)
        s = T("VENTA POR MAYOR Y MENOR", ANTON, 84, NEGRO)
        self.mayor = centrar(caja(s.shape[1] - 58 + 60, 124, 6, AMARILLO), s, (s.shape[1] - 58 + 60) / 2, 62)
        s = T("ENVÍOS SEGÚN LA ZONA", ANTON, 88, NEGRO)
        ic = base.icono("camion", 110, NEGRO, AMARILLO)
        w = s.shape[1] - 60 + 180
        self.envios = centrar(centrar(caja(w, 140, 6, AMARILLO), ic, 80, 70), s, 140 + (s.shape[1] - 60) / 2 + 10, 72)
        s = T("PRIMERA CALIDAD", ANTON, 70, NEGRO)
        self.sello = centrar(caja(s.shape[1] - 50 + 60, 104, 6, AMARILLO), s, (s.shape[1] - 50 + 60) / 2, 52)
        # franja que corre
        txt = T(TICKER * 2, ANTON, 52, AMARILLO)
        self.ticker_txt = txt
        self.ticker_paso = txt.shape[1] / 2 - 18
        bw, bh = 1500, 104
        b = np.zeros((bh, bw, 4), np.float32)
        b[..., :3], b[..., 3] = NEGRO, 1.0
        r = rayas(bw, 12, 12).astype(np.float32)
        b[:12, :, :3], b[-12:, :, :3] = r, r
        self.ticker_base = b
        self.rayas = rayas(W, H)
        # cierre
        self.cierre = base.Cierre(dict(titulo_f=ANTON, texto_f=MONT, num_f=ANTON, col_titulo=AMARILLO, col_texto=BLANCO,
                                       col_sub=AMARILLO, tarjeta=(34, 34, 34), tarjeta_alpha=0.93, ic_fondo=AMARILLO,
                                       ic_tinta=NEGRO, espera="¡TE ESPERAMOS!", espera_f=ANTON, col_espera=AMARILLO))
        f = self.tramos["calidad"].cuadro(3.0)
        f = cv2.GaussianBlur(f, (0, 0), 22).astype(np.float32) * 0.28
        self.fondo_cierre = np.clip(f, 0, 255).astype(np.uint8)
        borde = rayas(W, 34)
        self.fondo_cierre[:34], self.fondo_cierre[-34:] = borde, borde
        y = np.linspace(0, 1, H, dtype=np.float32)
        self.vin = (1 - 0.45 * np.clip(1 - y / 0.22, 0, 1) ** 2 - 0.55 * np.clip((y - 0.70) / 0.30, 0, 1) ** 1.5)[:, None, None]
        self._subs = {}
        self.estilo_sub = dict(fuente=ANTON, tam=70, color=NEGRO, resaltado=(200, 30, 20), y=1690, caja=AMARILLO,
                               caja_alpha=1.0, radio=8)

    def sfx(self):
        return [(self.ini[k] - 0.3, "whoosh") for k in ("pilas", "calidad")] + [(self.t_cierre - 0.3, "whoosh"),
                (0.3, "golpe"), (self.ini["pilas"] + 1.0, "golpe"), (self.ini["calidad"] + 0.5, "golpe")]

    # ---------------------------------------------------------------- piezas por tramo
    def toma(self, k, t):
        tl = t - self.ini[k]
        z = 1.0 + 0.07 * clamp01(tl / self.tramos[k].dur)
        f = self.tramos[k].cuadro(tl)
        cx, cy = ENCUADRE[k]
        f = encuadre(f, W, H, cx, cy, z) if z > 1.001 else f.copy()
        # oscurecido suave arriba y abajo para que se lea el texto
        return (f.astype(np.float32) * self.vin).astype(np.uint8)

    def ticker(self, f, t, alpha):
        b = self.ticker_base.copy()
        off = int((t * 150) % self.ticker_paso)
        tx = self.ticker_txt
        h = tx.shape[0]
        y = (b.shape[0] - h) // 2 + 2
        seg = tx[:, off:off + b.shape[1]]
        b = base.sobre(b, seg, 0, y)
        blit(f, b, W / 2, 1460, alpha=alpha, ang=4)

    def capitulo(self, f, k, t, desde=0.25):
        tl = t - self.ini[k]
        q = prog(tl, desde, 0.45)
        sale = prog(tl, self.tramos[k].dur - 0.9, 0.4)
        x = 40 + self.caps[k].shape[1] / 2 - (1 - e_out(q)) * 700 - e_inout(sale) * 700
        blit(f, self.caps[k], x, 300, alpha=clamp01(q * 3))

    def escena(self, k, t):
        f = self.toma(k, t)
        tl = t - self.ini[k]
        if k == "llenado":
            q = prog(t, 0.25, 0.30)
            sale = prog(t, 5.0, 0.45)
            esc = 1.0 + 0.7 * (1 - e_out(q))
            sx = np.sin(t * 90) * 10 * (1 - clamp01((t - 0.55) / 0.3)) if t > 0.55 else 0
            y = 820 - e_inout(sale) * 1300
            blit(f, self.sh_maiz, W / 2 + 10 + sx, y + 18, alpha=clamp01(q * 4), escala=esc)
            blit(f, self.maiz, W / 2 + sx, y, alpha=clamp01(q * 4), escala=esc)
            q2 = prog(t, 0.75, 0.40)
            blit(f, self.primera, W / 2 - (1 - e_out(q2)) * W - e_inout(sale) * W, y + 225, alpha=clamp01(q2 * 3), ang=-3)
            self.capitulo(f, k, t, desde=5.3)
        elif k == "pilas":
            self.capitulo(f, k, t)
            q = prog(tl, 1.0, 0.35)
            blit(f, self.kg, W / 2, 1060, alpha=clamp01(q * 4), escala=1 + 0.5 * (1 - e_out(q)))
            q2 = prog(tl, g_rel(self.guion, "pilas", 7, self.ini[k]) - 0.15, 0.4)
            blit(f, self.mayor, W / 2 + (1 - e_out(q2)) * W, 1200, alpha=clamp01(q2 * 3), ang=-3)
        elif k == "calidad":
            self.capitulo(f, k, t)
            q = prog(tl, 0.5, 0.4)
            blit(f, self.sello, W / 2, 1040, alpha=clamp01(q * 3), escala=max(e_back(q, 2.2), 0.01), ang=3)
            q2 = prog(tl, g_rel(self.guion, "calidad", 7, self.ini[k]) - 0.3, 0.4)
            blit(f, self.envios, W / 2 - (1 - e_out(q2)) * W, 1200, alpha=clamp01(q2 * 3), ang=-2)
        # logo y franja
        blit(f, self.logo, W - 110, 150, alpha=clamp01(prog(t, 0.6, 0.4) * 3))
        self.ticker(f, t, clamp01(prog(t, 3.0, 0.4) * 3))
        return f

    def esc_cierre(self, t):
        f = self.fondo_cierre.copy()
        self.cierre.dibujar(f, t - self.t_cierre, y0=200, desde="izq")
        return f

    def tramo_en(self, t):
        k = CAPITULOS[0][0]
        for kk, *_ in CAPITULOS:
            if t >= self.ini[kk]:
                k = kk
        return k

    def pintar(self, t):
        return self.esc_cierre(t) if t >= self.t_cierre else self.escena(self.tramo_en(t), t)

    def frame(self, t):
        t = min(t, self.dur - 1e-3)
        cortes = [self.ini["pilas"], self.ini["calidad"], self.t_cierre]
        c = next((c for c in cortes if c - TR <= t < c + TR), None)
        if c is None:
            f = self.pintar(t)
        else:                                            # barrido de rayas en diagonal
            p = (t - (c - TR)) / (2 * TR)
            frente = -600 + e_inout(min(1, 2 * p)) * (W + 1200)
            atras = -600 + e_inout(max(0, 2 * p - 1)) * (W + 1200)
            viejo = self.pintar(min(t, c - 1e-3)) if p < 1 else None
            nuevo = self.pintar(max(t, c))
            yy, xx = np.mgrid[0:H:8, 0:W:8]
            d = xx + (yy - H / 2) * 0.32
            m_n = cv2.resize((d < atras).astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)[..., None]
            m_r = cv2.resize(((d >= atras) & (d < frente)).astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)[..., None]
            f = nuevo * m_n + self.rayas * m_r + viejo * np.clip(1 - m_n - m_r, 0, 1)
            f = np.clip(f, 0, 255).astype(np.uint8)
        f = np.ascontiguousarray(f)
        base.subtitulos(f, self.guion, t, self.estilo_sub, self._subs)
        if t < 0.15:
            f = (f.astype(np.float32) * (t / 0.15)).astype(np.uint8)
        if t > self.dur - 0.5:
            f = (f.astype(np.float32) * ((self.dur - t) / 0.5)).astype(np.uint8)
        return f


def sobre_izq(base_spr, spr, x, dy=0):
    h = base_spr.shape[0]
    return base.sobre(base_spr, spr, int(x), int((h - spr.shape[0]) / 2 + dy))


def g_rel(guion, k, i, ini):
    """segundo (relativo al inicio del tramo) en que se dice la palabra i del texto k."""
    return guion.palabra(k, i) - ini


if __name__ == "__main__":
    base.ejecutar(Video(), "forralitas_maiz_cinta")
