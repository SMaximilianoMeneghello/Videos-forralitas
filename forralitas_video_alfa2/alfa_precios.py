"""Video "Alfa verde en dos calidades" — Forrajería Forralitas (vertical 1080x1920).

Estilo nuevo: pantalla dividida. Arranca con el video a pantalla completa y se "encoge" a una franja
horizontal arriba; abajo, tarjetas de precio sobre fondo crema. Cierre claro con todos los datos.

Uso:  python alfa_precios.py                 → forralitas_alfa_precios_9x16.mp4 (+ versión solo música)
      python alfa_precios.py --cuadros 1 5 9  → previas/
"""
import json
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image
from scipy.io import wavfile

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, os.path.join(RAIZ, "forralitas_video_alfa"))
sys.path.insert(0, os.path.join(RAIZ, "forralitas_video_viruta"))
import viruta_promo as v1          # noqa: E402  (datos del local, utilidades de texto; cambia el cwd)
import viruta_promo_v2 as v2       # noqa: E402  (cámara, temblor, flash)
from verde_alfa import verde_lindo  # noqa: E402
from efectos import icono          # noqa: E402
import audio as sfxlib             # noqa: E402
import voz_tts                     # noqa: E402

fp = v1.fp
W, H, FPS, SR = 1080, 1920, 30, 44100
e_out, e_inout, e_back, prog, clamp01 = fp.e_out, fp.e_inout, fp.e_back, fp.prog, fp.clamp01
blit, caja, sobre = fp.blit, fp.caja, fp.sobre
ANTON, MONT = v1.ANTON, v1.MONT
T = v1.T
DATOS = v1.DATOS

# ============================================================ precios y guion
PRECIOS = {"c1": "$6.000", "c2": "$5.000", "c2_x10": "$4.500"}
VOZ = [   # (clave, texto que dice la voz, subtítulo: *resaltado*, | corta bloques, _ = palabra que no se muestra)
    ("intro", "¡Llegó alfa verde, y la tenemos en dos calidades!",
     "¡Llegó *alfa* *verde,* | y la tenemos en *dos* *calidades!*"),
    ("c1", "Calidad uno, a seis mil pesos el fardo.", "*Calidad* *1,* | a *$6.000* _ _ el fardo."),
    ("c2", "Calidad dos, a cinco mil pesos el fardo.", "*Calidad* *2,* | a *$5.000* _ _ el fardo."),
    ("promo", "Y llevando diez fardos o más de calidad dos, te queda a cuatro mil quinientos cada uno.",
     "Y llevando *10* fardos o más | de calidad 2, | te queda a *$4.500* _ _ cada uno."),
    ("fin", "¡Aprovechá! Te esperamos en Forralitas.", "*¡Aprovechá!* | Te esperamos en *Forralitas.*"),
]
VOZ_NOMBRE, VOZ_VEL = "es-AR-TomasNeural", "+4%"
MUSICA, MUSICA_INICIO = os.path.join(AQUI, "musica", "Carefree.mp3"), 40.0

# ============================================================ paleta (nueva: crema, verde profundo, lima)
CREMA = (246, 242, 231)
VERDE = (24, 74, 40)
LIMA = (176, 214, 72)
AMARILLO = (255, 198, 46)
ROJO = (214, 56, 46)
GRIS = (98, 104, 92)
BLANCO = (255, 255, 255)

BAND_Y, BAND_H = 262, 608            # franja de video en el modo dividido
SUB_Y = 1565


# ============================================================ material
class Fuente:
    def __init__(self, ruta):
        cap = cv2.VideoCapture(ruta)
        self.fps = cap.get(cv2.CAP_PROP_FPS)
        self.fr = []
        while True:
            ok, f = cap.read()
            if not ok:
                break
            self.fr.append(f)
        self.cache = {}

    def at(self, t):
        """Cuadro en el segundo t (mezcla los dos cuadros vecinos para que la cámara lenta sea suave)."""
        x = np.clip(t * self.fps, 0, len(self.fr) - 1.001)
        i = int(x)
        a = x - i
        k = (i, round(a, 2))
        if k not in self.cache:
            if len(self.cache) > 12:
                self.cache.clear()
            f = self.fr[i] if a < 0.05 else cv2.addWeighted(self.fr[i], 1 - a, self.fr[i + 1], a, 0)
            rgb = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
            rgb = verde_lindo(rgb, 0.8)
            rgb = np.clip(rgb.astype(np.float32) * 1.08 + 4, 0, 255).astype(np.uint8)
            self.cache[k] = rgb
        return self.cache[k]


def ida_vuelta(t, a, b, vel):
    """Recorre [a, b] a velocidad vel y vuelve, sin saltos."""
    L = b - a
    x = (t * vel) % (2 * L)
    return a + (x if x <= L else 2 * L - x)


# ============================================================ piezas gráficas
def centrar(base, spr, cx, cy):
    return sobre(base, spr, int(round(cx - spr.shape[1] / 2)), int(round(cy - spr.shape[0] / 2)))


def sombra(spr, blur=18, op=0.30, pad=40):
    h, w = spr.shape[:2]
    a = np.zeros((h + 2 * pad, w + 2 * pad), np.float32)
    a[pad:pad + h, pad:pad + w] = spr[..., 3]
    a = cv2.GaussianBlur(a, (0, 0), blur) * op
    return np.dstack([np.zeros(a.shape + (3,), np.float32), a])


def bloque(txt, tam, fondo, tinta, padx=34, alto=None):
    s = T(txt, ANTON, tam, tinta, 0, 0)
    pad = int(tam * 0.35)
    w = s.shape[1] - 2 * pad + 2 * padx
    h = alto or int(tam * 1.28)
    return centrar(caja(w, h, 14, fondo), s, w / 2, h / 2 + tam * 0.04)


def pastilla(txt, tam, fondo, tinta, ruta=MONT):
    s = T(txt, ruta, tam, tinta, 0, 0)
    pad = int(tam * 0.35)
    w = s.shape[1] - 2 * pad + 2 * int(tam * 0.8)
    h = int(tam * 1.9)
    return centrar(caja(w, h, h // 2, fondo), s, w / 2, h / 2 + 2)


def tarjeta(nombre, precio):
    w, h = 480, 470
    base = caja(w, h, 38, BLANCO)
    base = centrar(base, caja(440, 96, 48, VERDE), w / 2, 68)
    base = centrar(base, T(nombre, ANTON, 66, BLANCO, 0, 0), w / 2, 70)
    base = centrar(base, T(precio, ANTON, v1.ajustar(precio, ANTON, 156, 420), VERDE, 0, 0), w / 2, 238)
    base = centrar(base, T("por fardo", MONT, 40, GRIS, 0, 0), w / 2, 345)
    base = centrar(base, caja(120, 10, 5, LIMA), w / 2, 410)
    return base


def fardo_icono(w=84, h=60):
    im = np.zeros((h, w, 4), np.float32)
    im = sobre(im, caja(w, h, 10, (120, 168, 62)), 0, 0)
    im = sobre(im, caja(w - 10, h - 12, 8, (146, 190, 78)), 5, 4)
    for x in (int(w * 0.3), int(w * 0.7)):
        im = sobre(im, caja(5, h, 2, (62, 98, 34)), x - 2, 0)
    for k in range(5):                                   # textura de pasto
        y = 10 + k * 9
        im = sobre(im, caja(int(w * 0.55), 2, 1, (104, 150, 54), 0.8), int(8 + (k % 2) * 14), y)
    return im


def sello(precio):
    w, h = 500, 190
    base = caja(w, h, 34, AMARILLO)
    base = centrar(base, T(precio, ANTON, 122, VERDE, 0, 0), 205, h / 2 + 4)
    base = centrar(base, T("c/u", MONT, 50, VERDE, 0, 0), 425, h / 2 + 22)
    return base


# ============================================================ video
class Video:
    def __init__(self):
        self.src = Fuente(os.path.join(AQUI, "material", "video.mp4"))
        # ---- voz y tiempos
        self.voces = {}
        for clave, txt, sub in VOZ:
            audio, tiempos = voz_tts.clip_palabras(txt, voz=VOZ_NOMBRE, rate=VOZ_VEL)
            palabras = sub.replace("|", "").split()
            assert len(palabras) == len(txt.split()), clave
            self.voces[clave] = dict(audio=audio, tiempos=tiempos, dur=len(audio) / SR, txt=txt,
                                     bloques=[b.split() for b in sub.split("|")])
        V = self.voces
        V["intro"]["t0"] = 0.55
        self.t_split = 4.6
        V["c1"]["t0"] = max(5.55, V["intro"]["t0"] + V["intro"]["dur"] + 0.5)
        V["c2"]["t0"] = V["c1"]["t0"] + V["c1"]["dur"] + 0.45
        self.t_promo = V["c2"]["t0"] + V["c2"]["dur"] + 0.45
        V["promo"]["t0"] = self.t_promo + 0.45
        self.t_cierre = V["promo"]["t0"] + V["promo"]["dur"] + 0.75
        V["fin"]["t0"] = self.t_cierre + 0.45
        self.dur = round(max(self.t_cierre + 8.0, V["fin"]["t0"] + V["fin"]["dur"] + 5.0), 2)
        self.k = {
            "dos": self.tw("intro", 7), "c1": self.tw("c1", 0) - 0.12, "c2": self.tw("c2", 0) - 0.12,
            "diez": self.tw("promo", 2), "te": self.tw("promo", 9), "cuatro": self.tw("promo", 12),
        }
        # ---- piezas
        self.fondo_crema = self._fondo()
        self.i_llego = bloque("¡LLEGÓ", 150, VERDE, BLANCO)
        self.i_alfa = bloque("ALFA VERDE!", 170, LIMA, VERDE)
        self.i_dos = pastilla("EN DOS CALIDADES", 46, BLANCO, VERDE, ANTON)
        self.titulo = T("ALFA VERDE", ANTON, 118, VERDE, 0, 0)
        self.chip = pastilla("2 CALIDADES", 30, LIMA, VERDE, ANTON)
        self.card1, self.card2 = tarjeta("CALIDAD 1", PRECIOS["c1"]), tarjeta("CALIDAD 2", PRECIOS["c2"])
        self.sh1 = sombra(self.card1)
        self.cinta = bloque("LLEVANDO 10 FARDOS O MÁS", 64, AMARILLO, VERDE, alto=100)
        self.fardo = fardo_icono()
        self.sello = sello(PRECIOS["c2_x10"])
        self.sh_sello = sombra(self.sello, 14, 0.35)
        self.mascara_banda = caja(W - 60, BAND_H, 34, BLANCO)[..., 3]
        self._cierre_piezas()
        self._subs = {}

    def tw(self, clave, i):
        v = self.voces[clave]
        return v["t0"] + v["tiempos"][i]

    def _fondo(self):
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.hypot(xx - W / 2, yy - H * 0.45) / np.hypot(W / 2, H / 2)
        f = np.array(CREMA, np.float32) * (1 - 0.07 * r[..., None] ** 2)
        rayas = ((xx + yy * 0.7) % 90 < 45).astype(np.float32)[..., None]
        f = f * (1 - 0.018 * rayas)
        return np.clip(f, 0, 255).astype(np.uint8)

    # ---------------------------------------------------------------- video en pantalla
    def tiempo_fuente(self, t):
        if t < self.t_promo:
            return ida_vuelta(t, 0.15, 4.35, 0.55)
        return 6.05 + min((t - self.t_promo) * 0.36, 1.8)

    def cuadro_vertical(self, t):
        img = self.src.at(self.tiempo_fuente(t))
        cx = 0.36 + 0.24 * e_inout(clamp01(t / 4.6))
        return fp.recorte(img, W, H, cx, 0.5, 1.0 + 0.06 * t / 4.6)

    def cuadro_banda(self, t, w=W - 60, h=BAND_H):
        img = self.src.at(self.tiempo_fuente(t))
        if t < self.t_promo:
            return fp.recorte(img, w, h, 0.5, 0.5, 1.04 + 0.04 * np.sin(t * 0.4))
        # toma desde arriba: se recorta del lado izquierdo para dejar afuera las bolsas
        sub = img[:, :1050]
        return fp.recorte(sub, w, h, 0.5, 0.45, 1.05)

    def banda(self, f, t, y=BAND_Y):
        img = self.cuadro_banda(t)
        if self.t_promo - 0.2 <= t < self.t_promo + 0.2:           # cambio de toma con destello
            p = (t - (self.t_promo - 0.2)) / 0.4
            a = fp.recorte(self.src.at(ida_vuelta(self.t_promo, 0.15, 4.35, 0.55)), W - 60, BAND_H, 0.5, 0.5, 1.05)
            img = a if p < 0.5 else img
            fl = 0.7 * np.exp(-((p - 0.5) / 0.2) ** 2)
            img = cv2.addWeighted(img, 1 - fl, np.full_like(img, 255), fl, 0)
        spr = np.dstack([img.astype(np.float32) * self.mascara_banda[..., None], self.mascara_banda])
        blit(f, sombra(spr, 20, 0.35), W / 2, y + BAND_H / 2 + 14)
        blit(f, spr, W / 2, y + BAND_H / 2)

    # ---------------------------------------------------------------- escenas
    def intro(self, t):
        f = self.cuadro_vertical(t)
        y_ = (np.arange(H, dtype=np.float32) / H)[:, None, None]
        f = (f.astype(np.float32) * (1 - 0.45 * np.clip((y_ - 0.55) / 0.4, 0, 1))).astype(np.uint8)
        sale = e_inout(prog(t, 4.35, 0.35))
        q = prog(t, 0.35, 0.45)
        blit(f, self.i_llego, W / 2 - (1 - e_out(q)) * W - sale * W, 700, alpha=clamp01(q * 3), ang=-3)
        q = prog(t, 0.65, 0.45)
        blit(f, self.i_alfa, W / 2 + (1 - e_out(q)) * W + sale * W, 880, alpha=clamp01(q * 3), ang=2,
             escala=1 + 0.03 * np.sin(max(t - 1.1, 0) * 4) * (t > 1.1))
        q = prog(t, self.k["dos"] - 0.15, 0.4)
        blit(f, self.i_dos, W / 2, 1050 + sale * 200, alpha=clamp01(q * 3) * (1 - sale), escala=max(e_back(q, 2.0), 0.01))
        return f

    def morph(self, t):
        """El video pasa de pantalla completa a la franja de arriba."""
        p = e_inout(clamp01((t - self.t_split) / 0.7))
        f = self.fondo_crema.copy()
        full = self.cuadro_vertical(t) if p < 1 else None
        x0, y0, x1, y1 = 0, 0, W, H
        X0, Y0, X1, Y1 = 30, BAND_Y, W - 30, BAND_Y + BAND_H
        cx0, cy0 = x0 + (X0 - x0) * p, y0 + (Y0 - y0) * p
        cx1, cy1 = x1 + (X1 - x1) * p, y1 + (Y1 - y1) * p
        w, h = int(cx1 - cx0), int(cy1 - cy0)
        img = self.src.at(self.tiempo_fuente(t))
        # el recorte de la fuente pasa de vertical (9:16) a horizontal
        hh = img.shape[0]
        wv, wh = hh * 9 / 16, img.shape[1]
        cw = wv + (wh - wv) * p
        cxs = img.shape[1] * (0.6 + (0.5 - 0.6) * p)
        xs0 = int(np.clip(cxs - cw / 2, 0, img.shape[1] - cw))
        crop = img[:, xs0:xs0 + int(cw)]
        crop = cv2.resize(crop, (max(w, 2), max(h, 2)), interpolation=cv2.INTER_AREA)
        r = int(34 * p)
        m = caja(max(w, 2), max(h, 2), max(r, 1), BLANCO)[..., 3] if r > 0 else np.ones((h, w), np.float32)
        spr = np.dstack([crop.astype(np.float32) * m[..., None], m])
        blit(f, spr, cx0 + w / 2, cy0 + h / 2)
        del full
        return f

    def cabecera(self, f, t, t0):
        q = prog(t, t0, 0.45)
        blit(f, self.titulo, W / 2 - 110, 150 - (1 - e_out(q)) * 60, alpha=clamp01(q * 3))
        q2 = prog(t, t0 + 0.2, 0.4)
        blit(f, self.chip, W / 2 + 270, 152, alpha=clamp01(q2 * 3), escala=max(e_back(q2, 2.2), 0.01))

    def precios(self, t):
        f = self.fondo_crema.copy()
        self.banda(f, t)
        self.cabecera(f, t, self.t_split + 0.5)
        for card, t0, cx in ((self.card1, self.k["c1"], 285), (self.card2, self.k["c2"], 795)):
            q = prog(t, t0, 0.55)
            if q <= 0:
                continue
            e = e_back(q, 1.6)
            flip = max(abs(np.cos((1 - e_out(q)) * np.pi / 2)), 0.02)        # gira como una carta
            spr = cv2.resize(card, (max(int(card.shape[1] * flip), 2), card.shape[0]), interpolation=cv2.INTER_AREA)
            y = 1150 + (1 - e_out(q)) * 80
            blit(f, cv2.resize(self.sh1, (max(int(self.sh1.shape[1] * flip), 2), self.sh1.shape[0])), cx + 6, y + 14,
                 alpha=clamp01(q * 3))
            blit(f, spr, cx, y, alpha=clamp01(q * 3))
        return f

    def promo(self, t):
        f = self.fondo_crema.copy()
        self.banda(f, t)
        self.cabecera(f, t, -10)
        tl = t - self.t_promo
        # tarjeta 1 se va, tarjeta 2 va al centro y un poco más chica
        q = e_inout(clamp01(tl / 0.5))
        blit(f, self.sh1, 285 - q * 700 + 6, 1150 + 14)
        blit(f, self.card1, 285 - q * 700, 1150)
        cx, cy, esc = 795 + (540 - 795) * q, 1150 + (1250 - 1150) * q, 1 - 0.15 * q
        blit(f, self.sh1, cx + 6, cy + 14, escala=esc)
        blit(f, self.card2, cx, cy, escala=esc)
        # cinta "llevando 10 fardos o más"
        qc = prog(tl, 0.35, 0.45)
        blit(f, self.cinta, W / 2 + (1 - e_out(qc)) * W, 940, alpha=clamp01(qc * 3), ang=-2)
        # 10 fardos que aparecen de a uno
        for i in range(10):
            qi = prog(t, self.k["diez"] - 0.2 + i * 0.08, 0.3)
            if qi > 0:
                x = 540 + (i - 4.5) * 96
                blit(f, self.fardo, x, 1040 - (1 - e_out(qi)) * 40, alpha=clamp01(qi * 3),
                     escala=max(e_back(qi, 2.4), 0.01))
        # el precio de $5.000 se tacha y cae el sello de $4.500 c/u
        ql = e_out(prog(t, self.k["te"] - 0.1, 0.35))
        if ql > 0:
            y = int(1250 + (238 - 235) * 0.85 - 52 * 0.85 + 30)
            x0 = int(540 - 180 * 0.85)
            cv2.line(f, (x0, y + 10), (int(x0 + 360 * 0.85 * ql), y - 18), ROJO, 14, cv2.LINE_AA)
        qs = prog(t, self.k["cuatro"] - 0.1, 0.3)
        if qs > 0:
            esc = 2.2 - 1.2 * e_out(qs)
            blit(f, self.sh_sello, 740 + 8, 1395 + 12, alpha=clamp01(qs * 3), escala=esc, ang=-8)
            blit(f, self.sello, 740, 1395, alpha=clamp01(qs * 3), escala=esc, ang=-8)
        dx, dy, a = v2.temblor(t, self.k["cuatro"] + 0.2, 16)
        f = v2.camara(f, 1.0, dx, dy, a)
        return v2.flash(f, t, self.k["cuatro"] + 0.18, 0.15, 0.35)

    # ---------------------------------------------------------------- cierre
    def _cierre_piezas(self):
        c = {}
        c["logo"] = fp.logo_circular(170)
        c["nombre"] = T("FORRAJERÍA FORRALITAS", ANTON, 74, VERDE, 0, 0)
        c["rubro"] = T("Forrajería y Semillería", MONT, 36, GRIS, 0, 0)
        c["espera"] = T("¡TE ESPERAMOS!", ANTON, 128, VERDE, 0, 0)
        # resumen de precios
        res = caja(960, 150, 30, VERDE)
        for i, (lab, pr) in enumerate((("CALIDAD 1", PRECIOS["c1"]), ("CALIDAD 2", PRECIOS["c2"]),
                                        ("10 o más C2", PRECIOS["c2_x10"] + " c/u"))):
            cx = 160 + i * 320
            res = centrar(res, T(lab, MONT, 28, LIMA, 0, 0), cx, 46)
            res = centrar(res, T(pr, ANTON, v1.ajustar(pr, ANTON, 62, 290), BLANCO, 0, 0), cx, 100)
            if i:
                res = centrar(res, caja(3, 100, 1, (70, 112, 80)), cx - 160, 75)
        c["resumen"] = res

        def fila(ic, lineas, alto):
            base = caja(960, alto, 26, BLANCO)
            base = centrar(base, ic, 70, alto / 2)
            y = alto / 2 - (len(lineas) - 1) * 30
            for txt, ruta, tam, col in lineas:
                s = T(txt, ruta, v1.ajustar(txt, ruta, tam, 790), col, 0, 0)
                base = sobre(base, s, int(132 - tam * 0.35), int(y - s.shape[0] / 2))
                y += 60
            return base
        ic = lambda n: icono(n, 84, LIMA, VERDE)
        c["filas"] = [
            fila(ic("ubicacion"), [(DATOS["direccion"][0], ANTON, 52, VERDE), (DATOS["direccion"][1], MONT, 36, GRIS)], 140),
            fila(ic("reloj"), [("Lunes a viernes  " + DATOS["horarios"][0][1], MONT, 38, VERDE),
                               ("Sábados  " + DATOS["horarios"][1][1], MONT, 38, VERDE)], 140),
            fila(ic("efectivo"), [("Formas de pago", MONT, 32, GRIS), (DATOS["pagos"], MONT, 38, VERDE)], 140),
            fila(ic("camion"), [("Envíos según la zona", MONT, 38, VERDE), ("Venta por mayor y menor", MONT, 38, VERDE)], 140),
            fila(fp.icono_whatsapp(84), [(DATOS["whatsapp"][0], ANTON, 58, VERDE), (DATOS["whatsapp"][1], ANTON, 58, VERDE)], 160),
        ]
        self.cie = c

    def cierre(self, t):
        tl = t - self.t_cierre
        c = self.cie
        f = self.fondo_crema.copy()
        q = prog(tl, 0.05, 0.5)
        blit(f, c["logo"], 150, 175, alpha=clamp01(q * 3), escala=max(e_back(q, 1.6), 0.01))
        q = prog(tl, 0.2, 0.45)
        blit(f, c["nombre"], 610, 150 - (1 - e_out(q)) * 30, alpha=clamp01(q * 3))
        blit(f, c["rubro"], 610, 222, alpha=clamp01(prog(tl, 0.35, 0.4) * 3))
        q = prog(tl, 0.35, 0.45)
        blit(f, c["espera"], W / 2, 360, alpha=clamp01(q * 3), escala=max(e_back(q, 1.8), 0.01))
        q = prog(tl, 0.6, 0.45)
        blit(f, c["resumen"], W / 2, 535 + (1 - e_out(q)) * 40, alpha=clamp01(q * 3))
        y = 640
        for i, fila in enumerate(c["filas"]):
            h = fila.shape[0]
            q = prog(tl, 0.85 + 0.2 * i, 0.45)
            blit(f, sombra(fila, 10, 0.12), W / 2 + 4 - (1 - e_out(q)) * W, y + h / 2 + 6, alpha=clamp01(q * 3))
            blit(f, fila, W / 2 - (1 - e_out(q)) * W, y + h / 2, alpha=clamp01(q * 3))
            y += h + 16
        return f

    # ---------------------------------------------------------------- transición al cierre (barrido diagonal)
    def barrido(self, a, b, p):
        yy, xx = self._diag if hasattr(self, "_diag") else self._mk_diag()
        L = float(self._diag_max)
        pos1 = e_inout(clamp01(p * 1.5)) * (L + 300) - 150
        pos2 = e_inout(clamp01((p - 0.3) * 1.5)) * (L + 300) - 150
        d = self._D
        out = np.where((d < pos2)[..., None], b, np.where((d < pos1)[..., None], np.array(VERDE, np.uint8), a))
        borde = (np.abs(d - pos1) < 10)[..., None]
        return np.where(borde, np.array(LIMA, np.uint8), out).astype(np.uint8)

    def _mk_diag(self):
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        self._D = xx * 0.8 + yy * 0.6
        self._diag_max = self._D.max()
        self._diag = (yy, xx)
        return self._diag

    # ---------------------------------------------------------------- subtítulos (pastilla blanca)
    def subtitulos(self, f, t):
        for clave, v in self.voces.items():
            if not (v["t0"] - 0.05 <= t <= v["t0"] + v["dur"] + 0.45):
                continue
            tiempos = [v["t0"] + x for x in v["tiempos"]]
            i = 0
            for bi, b in enumerate(v["bloques"]):
                ini = tiempos[i] - 0.05
                fin = tiempos[i + len(b)] - 0.05 if bi + 1 < len(v["bloques"]) else v["t0"] + v["dur"] + 0.45
                if ini <= t < fin:
                    partes = []
                    vis = [(j, w) for j, w in enumerate(b) if w != "_"]
                    for n, (j, w) in enumerate(vis):
                        dicha = tiempos[i + j] - 0.03 <= t
                        col = (52, 130, 44) if (w.startswith("*") and dicha) else VERDE
                        partes.append((w.replace("*", "") + (" " if n < len(vis) - 1 else ""), col))
                    clave_s = tuple(partes)
                    if clave_s not in self._subs:
                        s = fp.sprite(partes, MONT, 60, 0, (0, 0, 0), 0)
                        while s.shape[1] > W - 120:
                            s = fp.sprite(partes, MONT, int(60 * (W - 140) / s.shape[1]), 0, (0, 0, 0), 0)
                        pad = 21
                        w, h = s.shape[1] - 2 * pad + 70, 100
                        base = centrar(caja(w, h, 50, BLANCO, 0.96), s, w / 2, h / 2 + 3)
                        self._subs[clave_s] = (base, sombra(base, 10, 0.25))
                    base, sh = self._subs[clave_s]
                    q = e_back(prog(t - ini, 0, 0.16), 2.0)
                    a = clamp01((t - ini) / 0.08)
                    blit(f, sh, W / 2 + 3, SUB_Y + 8, alpha=a, escala=0.9 + 0.1 * q)
                    blit(f, base, W / 2, SUB_Y, alpha=a, escala=0.9 + 0.1 * q)
                    return
                i += len(b)

    # ---------------------------------------------------------------- cuadro final
    def escena(self, t):
        if t < self.t_split:
            return self.intro(t)
        if t < self.t_split + 0.7:
            f = self.morph(t)
            a = clamp01((t - self.t_split - 0.35) / 0.35)
            if a > 0:
                self.cabecera(f, t, self.t_split + 0.5)
            return f
        if t < self.t_promo:
            return self.precios(t)
        return self.promo(t)

    def frame(self, t):
        t = min(t, self.dur - 1e-3)
        if t < self.t_cierre - 0.35:
            f = self.escena(t)
        elif t < self.t_cierre + 0.35:
            p = (t - (self.t_cierre - 0.35)) / 0.7
            if not hasattr(self, "_D"):
                self._mk_diag()
            f = self.barrido(self.escena(min(t, self.t_cierre - 0.36)), self.cierre(max(t, self.t_cierre)), p)
        else:
            f = self.cierre(t)
        f = np.ascontiguousarray(f)
        self.subtitulos(f, t)
        if t < 0.2:
            f = (f.astype(np.float32) * (t / 0.2)).astype(np.uint8)
        if t > self.dur - 0.4:
            f = (f.astype(np.float32) * ((self.dur - t) / 0.4)).astype(np.uint8)
        return f

    # ---------------------------------------------------------------- audio
    def audio(self, ruta, con_voz=True):
        n = int(self.dur * SR)
        voz = np.zeros(n, np.float32)
        if con_voz:
            for v in self.voces.values():
                x = v["audio"] * (10 ** (-17 / 20) / (np.sqrt((v["audio"] ** 2).mean()) + 1e-9))
                i = int(v["t0"] * SR)
                voz[i:i + x.size] += x[:max(0, n - i)]
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(MUSICA_INICIO), "-t", str(self.dur + 1), "-i", MUSICA,
                              "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
        mus = np.frombuffer(raw, np.float32).reshape(-1, 2)[:n].copy()
        mus *= 10 ** (-20 / 20) / (np.sqrt((mus ** 2).mean()) + 1e-9)
        if con_voz:
            env = np.sqrt(np.convolve(voz ** 2, np.ones(int(0.04 * SR)) / int(0.04 * SR), mode="same"))
            act = (env > 0.01).astype(np.float32)
            k = int(0.3 * SR)
            sm = np.convolve(np.pad(act, (k, k), mode="edge"), np.ones(k) / k, mode="same")[k:-k]
            mus *= (1 - 0.65 * np.clip(sm * 1.4, 0, 1))[:, None]
        fo = int(1.5 * SR)
        mus[-fo:] *= np.linspace(1, 0, fo)[:, None]
        sfx = np.zeros(n, np.float32)

        def poner(x, t, g):
            i = int(t * SR)
            if 0 <= i < n:
                m = min(len(x), n - i)
                sfx[i:i + m] += x[:m] * g
        poner(sfxlib.whoosh(0.5), self.t_split - 0.05, 0.08)
        poner(sfxlib.whoosh(0.5), self.t_cierre - 0.25, 0.08)
        for t0 in (self.k["c1"], self.k["c2"]):
            poner(sfxlib.whoosh(0.3), t0, 0.05)
        poner(sfxlib.golpe(), self.k["cuatro"] + 0.15, 0.22)
        mix = mus + (voz + sfx)[:, None]
        tmp = ruta.replace(".wav", "_crudo.wav")
        wavfile.write(tmp, SR, np.clip(mix, -1, 1).astype(np.float32))
        cadena = "acompressor=threshold=-20dB:ratio=2.2:attack=12:release=160:makeup=2"
        med = subprocess.run(["ffmpeg", "-hide_banner", "-i", tmp, "-af", cadena + ",loudnorm=I=-14:TP=-1.5:LRA=8:print_format=json",
                              "-f", "null", "-"], capture_output=True, text=True).stderr
        j = json.loads(med[med.rfind("{"):med.rfind("}") + 1])
        ln = (f"loudnorm=I=-14:TP=-1.5:LRA=8:measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
              f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af", f"{cadena},{ln},alimiter=limit=0.89:level=false",
                        "-ar", "48000", "-ac", "2", ruta], check=True)
        os.remove(tmp)
        return ruta


def main():
    v = Video()
    print("duración", v.dur, "| split", v.t_split, "promo", round(v.t_promo, 2), "cierre", round(v.t_cierre, 2),
          "| voces", {k: (round(x["t0"], 2), round(x["dur"], 2)) for k, x in v.voces.items()})
    if "--cuadros" in sys.argv:
        d = os.path.join(AQUI, "previas")
        os.makedirs(d, exist_ok=True)
        for s in [float(x) for x in sys.argv[sys.argv.index("--cuadros") + 1:]]:
            Image.fromarray(v.frame(s)).save(os.path.join(d, f"{s:05.2f}.png"))
        return
    sal = os.path.join(AQUI, "forralitas_alfa_precios_9x16.mp4")
    sal2 = os.path.join(AQUI, "forralitas_alfa_precios_9x16_solo_musica.mp4")
    wav, wav2 = v.audio(os.path.join(AQUI, "_voz.wav")), v.audio(os.path.join(AQUI, "_sin_voz.wav"), con_voz=False)
    tmp = os.path.join(AQUI, "_video.mp4")
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-profile:v", "high", "-preset", "slow", "-crf", "17",
                          "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for i in range(int(v.dur * FPS)):
        p.stdin.write(v.frame(i / FPS).tobytes())
    p.stdin.close()
    p.wait()
    for w, s in ((wav, sal), (wav2, sal2)):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-i", w, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-shortest", "-movflags", "+faststart", s], check=True)
        os.remove(w)
    os.remove(tmp)
    print("Listo:", sal, "|", sal2)


if __name__ == "__main__":
    main()
