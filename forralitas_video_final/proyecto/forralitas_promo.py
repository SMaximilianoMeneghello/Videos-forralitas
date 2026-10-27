"""Promo "Llegó la mercadería" — Forrajería Forralitas.

Requiere haber corrido una vez:  python preparar.py
Renderizar todo:                 python forralitas_promo.py
Solo un corte:                   python forralitas_promo.py --corte principal|estado|cuadrado
Vista previa de cuadros:         python forralitas_promo.py --corte principal --cuadros 1 5 12

Para cambiar textos, teléfonos o la locución, editá DATOS y VOZ más abajo y volvé a correr.
"""
import argparse
import json
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy.io import wavfile
from scipy.signal import butter, resample_poly, sosfilt

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", ".."))
os.chdir(AQUI)
sys.path.insert(0, RAIZ)
import audio as sfxlib          # noqa: E402  (efectos de sonido sintetizados: whoosh, golpe)
import voz_tts                  # noqa: E402  (locución con edge-tts, voz es-AR)

SALIDA = os.path.abspath(os.path.join(AQUI, ".."))

# ============================================================ DATOS (editables)
DATOS = {
    "titulo1": "LLEGÓ LA",
    "titulo2": "MERCADERÍA",
    "maiz": "MAÍZ",
    "bolsas": "Bolsas de 40 kg y 50 kg",
    "alfa": "ALFA",
    "nombre": "FORRAJERÍA FORRALITAS",
    "rubro": "Forrajería y Semillería",
    "ruta": "Ruta 305 km 7,5",
    "localidad": "Las Talitas",
    "telefonos": ["381 526 9004", "381 633 4344"],     # dejar [] para no mostrar teléfonos
    "cta": "¡TE ESPERAMOS!",
    "veni": "VENÍ A BUSCARLO",
}
VOZ = {   # clave: texto exacto de la locución
    "L1": "¡Llegó mercadería a Forralitas!",
    "L2": "Maíz, en bolsas de cuarenta y cincuenta kilos.",
    "L3": "Y alfa para tus animales.",
    "L4": "Te esperamos en Ruta trescientos cinco, kilómetro siete y medio, Las Talitas.",
    "L5": "¡Forrajería Forralitas, con todo para tu campo!",
}
# subtítulos: cómo se escribe en pantalla cada palabra de la locución (misma cantidad de palabras;
# "_" = la palabra se dice pero no se muestra, p. ej. "trescientos cinco" → "305")
SUBS = {   # "|" separa los bloques de subtítulo que se muestran juntos
    "L1": "¡Llegó mercadería | a *Forralitas!*",
    "L2": "*Maíz,* | en bolsas de *40* | y *50* *kilos.*",
    "L3": "Y *alfa* para tus animales.",
    "L4": "Te esperamos en *Ruta* *305,* _ | kilómetro *7* *y* *medio,* | *Las* *Talitas.*",
    "L5": "¡Forrajería *Forralitas,* | con todo para tu campo!",
}
VOZ_NOMBRE, VOZ_VELOCIDAD = "es-AR-TomasNeural", "+0%"
MUSICA, MUSICA_INICIO, BPM = "musica/Montauk_Point.mp3", 130.17, 118.0
BEAT = 60 / BPM
PANEL_RATIO, PANEL_Y = 0.66, 0.43
FPS = 30
SR = 44100

# paleta tomada de las fotos
MAIZ_C = (247, 178, 32)
ORO = (255, 206, 72)
VERDE = (58, 112, 52)
VERDE_OSC = (20, 52, 26)
ROJO = (176, 46, 36)
BLANCO, NEGRO = (255, 255, 255), (12, 12, 10)
F_ANTON = "fuentes/Anton.ttf"
F_BEBAS = "fuentes/BebasNeue.ttf"
F_MONT = "fuentes/Montserrat.ttf"


# ============================================================ utilidades
def clamp01(x):
    return float(min(1.0, max(0.0, x)))


def prog(t, t0, d):
    return clamp01((t - t0) / d) if d > 0 else float(t >= t0)


def e_out(x):
    x = clamp01(x)
    return 1 - (1 - x) ** 3


def e_inout(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def e_back(x, s=1.7):
    x = clamp01(x)
    return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


_FUENTES = {}


def fuente(ruta, tam):
    k = (ruta, tam)
    if k not in _FUENTES:
        _FUENTES[k] = ImageFont.truetype(ruta, tam)
    return _FUENTES[k]


def sprite(partes, ruta, tam, trazo=0, color_trazo=NEGRO, sombra=0.55, espaciado=0):
    """Texto (lista de (texto, color)) → array RGBA float premultiplicado, con sombra suave."""
    f = fuente(ruta, tam)
    pad = int(tam * 0.35) + trazo
    anchos = [f.getlength(t) + espaciado * max(len(t) - 1, 0) for t, _ in partes]
    w = int(sum(anchos)) + 2 * pad
    asc, desc = f.getmetrics()
    h = asc + desc + 2 * pad
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = pad
    for (t, c), a in zip(partes, anchos):
        if espaciado:
            xx = x
            for ch in t:
                d.text((xx, pad), ch, font=f, fill=c + (255,), stroke_width=trazo, stroke_fill=color_trazo + (255,))
                xx += f.getlength(ch) + espaciado
        else:
            d.text((x, pad), t, font=f, fill=c + (255,), stroke_width=trazo, stroke_fill=color_trazo + (255,))
        x += a
    if sombra:
        a = im.getchannel("A").filter(ImageFilter.GaussianBlur(max(3, tam // 14)))
        base = Image.new("RGBA", im.size, (0, 0, 0, 0))
        s = Image.new("RGBA", im.size, (0, 0, 0, 0))
        s.putalpha(a.point(lambda v: int(v * sombra)))
        base.alpha_composite(s, (max(2, tam // 30), max(3, tam // 20)))
        base.alpha_composite(im)
        im = base
    a = np.asarray(im, np.float32)
    a[..., :3] *= a[..., 3:4] / 255
    a[..., 3] /= 255
    return a


def caja(w, h, r, color, alpha=1.0):
    ss = 3
    m = Image.new("L", (w * ss, h * ss), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w * ss - 1, h * ss - 1), r * ss, fill=255)
    m = np.asarray(m.resize((w, h), Image.LANCZOS), np.float32) / 255 * alpha
    out = np.empty((h, w, 4), np.float32)
    out[..., :3] = np.array(color, np.float32) * m[..., None]
    out[..., 3] = m
    return out


def sobre(base, spr, x, y):
    out = base.copy()
    H0, W0 = out.shape[:2]
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + spr.shape[1], W0), min(y + spr.shape[0], H0)
    if x0 < x1 and y0 < y1:
        s = spr[y0 - y:y1 - y, x0 - x:x1 - x]
        out[y0:y1, x0:x1] = s + out[y0:y1, x0:x1] * (1 - s[..., 3:4])
    return out


def blit(f, spr, cx, cy, alpha=1.0, escala=1.0, ang=0.0):
    """Dibuja un sprite centrado en (cx, cy) sobre el cuadro uint8 f (in place)."""
    if alpha <= 0.004 or escala <= 0.01:
        return
    if escala != 1.0 or ang:
        h, w = spr.shape[:2]
        M = cv2.getRotationMatrix2D((w / 2, h / 2), ang, escala)
        nw, nh = int(w * escala * 1.15) + 4, int(h * escala * 1.15) + 4
        M[0, 2] += nw / 2 - w / 2
        M[1, 2] += nh / 2 - h / 2
        spr = cv2.warpAffine(spr, M, (nw, nh), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    h, w = spr.shape[:2]
    x, y = int(round(cx - w / 2)), int(round(cy - h / 2))
    H0, W0 = f.shape[:2]
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W0), min(y + h, H0)
    if x0 >= x1 or y0 >= y1:
        return
    s = spr[y0 - y:y1 - y, x0 - x:x1 - x]
    reg = f[y0:y1, x0:x1].astype(np.float32)
    f[y0:y1, x0:x1] = np.clip(s[..., :3] * alpha + reg * (1 - s[..., 3:4] * alpha), 0, 255).astype(np.uint8)


def a_sprite(rgb, mascara=None):
    m = np.ones(rgb.shape[:2], np.float32) if mascara is None else mascara
    return np.dstack([rgb.astype(np.float32) * m[..., None], m])


def icono_pin(l, color=ORO):
    ss = 4
    L = l * ss
    im = Image.new("RGBA", (L, L), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    u = L / 100
    d.polygon([(50 * u, 96 * u), (22 * u, 52 * u), (78 * u, 52 * u)], fill=color + (255,))
    d.ellipse((20 * u, 4 * u, 80 * u, 64 * u), fill=color + (255,))
    d.ellipse((38 * u, 22 * u, 62 * u, 46 * u), fill=(0, 0, 0, 0))
    im = im.resize((l, l), Image.LANCZOS)
    a = np.asarray(im, np.float32)
    a[..., :3] *= a[..., 3:4] / 255
    a[..., 3] /= 255
    return a


def icono_whatsapp(l):
    """Ícono genérico de teléfono en círculo verde (no usa el logo de WhatsApp)."""
    ss = 4
    L = l * ss
    im = Image.new("RGBA", (L, L), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    u = L / 100
    d.ellipse((0, 0, L - 1, L - 1), fill=(46, 170, 82, 255))
    d.rounded_rectangle((34 * u, 18 * u, 66 * u, 82 * u), 8 * u, outline=(255, 255, 255, 255), width=int(6 * u))
    d.ellipse((46 * u, 68 * u, 54 * u, 76 * u), fill=(255, 255, 255, 255))
    im = im.resize((l, l), Image.LANCZOS)
    a = np.asarray(im, np.float32)
    a[..., :3] *= a[..., 3:4] / 255
    a[..., 3] /= 255
    return a


def logo_circular(l):
    im = Image.open("material/logo.jpg").convert("RGB")
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).ellipse((55, 55, im.width - 55, im.height - 55), fill=255)
    im.putalpha(m)
    im = im.crop((55, 55, im.width - 55, im.height - 55)).resize((l, l), Image.LANCZOS)
    a = np.asarray(im, np.float32)
    a[..., :3] *= a[..., 3:4] / 255
    a[..., 3] /= 255
    return a


# ============================================================ material
class Video:
    def __init__(self, ruta, fps, t0=0.0):
        cap = cv2.VideoCapture(ruta)
        self.frames = []
        while True:
            ok, f = cap.read()
            if not ok:
                break
            self.frames.append(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))
        real = cap.get(cv2.CAP_PROP_FPS)
        self.fps, self.t0 = (real if fps == "real" and real else (fps if fps != "real" else 30)), t0
        self.h, self.w = self.frames[0].shape[:2]

    def at(self, t):
        """t en segundos del clip ORIGINAL."""
        k = int(round((t - self.t0) * self.fps))
        return self.frames[int(np.clip(k, 0, len(self.frames) - 1))]


class Foto:
    def __init__(self, ruta, max_lado=4000):
        im = Image.open(ruta).convert("RGB")
        s = min(1.0, max_lado / max(im.size))
        if s < 1:
            im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
        self.img = np.asarray(im)
        self.h, self.w = self.img.shape[:2]

    def at(self, t):
        return self.img


_MAT = {}
CACHE = "cache_previa" if os.environ.get("PREVIA") else "cache"


def material(nombre):
    if nombre not in _MAT:
        rutas = {
            "c1": lambda: Video(f"{CACHE}/clip1_ia.mp4", "real", 0.0),
            "c3": lambda: Video(f"{CACHE}/clip3_ia.mp4", "real", 1.5),
            "c1_lento": lambda: Video(f"{CACHE}/clip1_lento.mp4", 120, 4.9),
            "c3_lento": lambda: Video(f"{CACHE}/clip3_lento.mp4", 120, 6.1),
            "bolsa": lambda: Foto(f"{CACHE}/ia_foto_bolsa_maiz.png"),
            "mano": lambda: Foto(f"{CACHE}/ia_foto_mano_punado.png"),
            "galpon_a": lambda: Foto(f"{CACHE}/ia_foto_camion_galpon_a.png"),
            "galpon_b": lambda: Foto(f"{CACHE}/ia_foto_camion_galpon_b.png"),
            "fardos": lambda: Foto("material/foto_fardos_alfa.jpg"),
            "camiones": lambda: Foto("material/foto_camiones_alfa.jpg"),
        }
        _MAT[nombre] = rutas[nombre]()
    return _MAT[nombre]


# ============================================================ color
class Grade:
    """Corrección de color por toma: exposición y balance parejos, realce suave del amarillo/verde."""

    def __init__(self, perfil, muestra):
        x = muestra.astype(np.float32) / 255
        lum = (x * [0.2126, 0.7152, 0.0722]).sum(2)
        objetivo = {"calido": 0.50, "verde": 0.52, "noche": 0.38, "neutro": 0.47}[perfil]
        self.ganancia = float(np.clip(objetivo / max(np.median(lum), 1e-3), 0.75, 1.4))
        self.perfil = perfil
        # balance: neutraliza el 35% del tinte medio de los tonos claros (sin perder el color del producto)
        claros = x[lum > np.percentile(lum, 70)]
        m = claros.mean(0)
        self.wb = (m.mean() / np.maximum(m, 1e-3)) ** 0.35 if perfil in ("calido", "neutro") else np.ones(3)

    def __call__(self, img, vig):
        x = img.astype(np.float32) / 255 * self.ganancia * self.wb
        if self.perfil == "calido":
            x *= np.array([1.04, 1.0, 0.94], np.float32)
            sat, cont = 1.12, 0.22
        elif self.perfil == "verde":
            x *= np.array([1.02, 1.03, 0.95], np.float32)
            sat, cont = 1.10, 0.20
        elif self.perfil == "noche":
            x *= np.array([0.95, 1.0, 1.08], np.float32)
            sat, cont = 1.05, 0.26
        else:
            sat, cont = 1.06, 0.18
        g = (x * [0.2126, 0.7152, 0.0722]).sum(2, keepdims=True)
        x = np.clip(g + (x - g) * sat, 0, 1)
        x = (1 - cont) * x + cont * (x * x * (3 - 2 * x))           # curva S suave
        return np.clip(x * vig * 255, 0, 255).astype(np.uint8)


# ============================================================ tomas
def recorte(img, W, H, cx, cy, zoom):
    """Encuadre tipo 'cover' de img a WxH; cx, cy (0..1) centro; zoom ≥ 1."""
    h, w = img.shape[:2]
    s = max(W / w, H / h) * zoom
    vw, vh = W / s, H / s
    x0 = np.clip(cx * w - vw / 2, 0, w - vw)
    y0 = np.clip(cy * h - vh / 2, 0, h - vh)
    M = np.array([[s, 0, -x0 * s], [0, s, -y0 * s]], np.float32)
    interp = cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC
    return cv2.warpAffine(img, M, (W, H), flags=interp, borderMode=cv2.BORDER_REFLECT)


def curva_tiempo(dur, tramos):
    """tramos: [(t_local, velocidad)] → función t_local → tiempo de origen recorrido (suavizado)."""
    ts = np.linspace(0, dur + 1, int((dur + 1) * 600) + 1)
    v = np.zeros_like(ts)
    for t0, vel in tramos:
        v[ts >= t0] = vel
    k = 90
    v = np.convolve(np.pad(v, (k, k), mode="edge"), np.ones(2 * k + 1) / (2 * k + 1), mode="same")[k:-k]
    tau = np.concatenate([[0], np.cumsum((v[1:] + v[:-1]) / 2 * np.diff(ts))])
    return lambda t: float(np.interp(t, ts, tau))


class Toma:
    def __init__(self, mat, beats, perfil, cam, src=0.0, tramos=((0, 1.0),), panel=False):
        self.mat, self.beats, self.perfil, self.cam = mat, beats, perfil, cam
        self.src, self.tramos, self.panel = src, tramos, panel
        self.dur = beats * BEAT
        self.tiempo = curva_tiempo(self.dur + 1, list(tramos))
        self.grade = None

    def preparar(self):
        m = material(self.mat)
        muestra = m.at(self.src + self.tiempo(self.dur / 2))
        self.grade = Grade(self.perfil, cv2.resize(muestra, (240, int(240 * muestra.shape[0] / muestra.shape[1]))))

    def cuadro(self, t, W, H, vig):
        m = material(self.mat)
        img = m.at(self.src + self.tiempo(max(t, 0)))
        (cx0, cy0, z0), (cx1, cy1, z1) = self.cam
        p = e_inout(t / self.dur) * 0.85 + 0.15 * clamp01(t / self.dur)
        cx, cy, z = cx0 + (cx1 - cx0) * p, cy0 + (cy1 - cy0) * p, z0 + (z1 - z0) * p
        if not self.panel:
            return self.grade(recorte(img, W, H, cx, cy, z), vig)
        # foto horizontal: fondo desenfocado + panel nítido con paneo
        fondo = recorte(img, W // 4, H // 4, 0.5, 0.5, 1.0)
        fondo = cv2.resize(cv2.GaussianBlur(fondo, (0, 0), 9), (W, H)).astype(np.float32) * 0.62
        pw = int(W * (0.94 if H > W else 0.80))
        ph = int(pw * (PANEL_RATIO if H > W else 0.52))
        panel = self.grade(recorte(img, pw, ph, cx, cy, z), np.ones((ph, pw, 1), np.float32))
        f = self.grade(fondo.astype(np.uint8), vig)
        y0 = int(H * (PANEL_Y if H > W else 0.40) - ph / 2)
        x0 = (W - pw) // 2
        borde = 6
        cv2.rectangle(f, (x0 - borde, y0 - borde), (x0 + pw + borde - 1, y0 + ph + borde - 1), ORO, -1)
        f[y0:y0 + ph, x0:x0 + pw] = panel
        return f


# ============================================================ transiciones
def tr_corte(a, b, p):
    return b


def tr_zoom(a, b, p):
    """Zoom through: la toma A se acerca con desenfoque radial y aparece B."""
    H, W = a.shape[:2]
    e = e_inout(p)

    def zb(img, amt):
        acc = np.zeros(img.shape, np.float32)
        for i in range(6):
            s = 1 + amt * i / 5
            M = np.array([[s, 0, (1 - s) * W / 2], [0, s, (1 - s) * H / 2]], np.float32)
            acc += cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REFLECT)
        return (acc / 6).astype(np.uint8)
    if p < 0.5:
        return zb(cv2.warpAffine(a, cv2.getRotationMatrix2D((W / 2, H / 2), 0, 1 + 0.5 * e), (W, H),
                                 borderMode=cv2.BORDER_REFLECT), 0.25 * e * 2)
    q = (1 - p) * 2
    return zb(cv2.warpAffine(b, cv2.getRotationMatrix2D((W / 2, H / 2), 0, 1 + 0.25 * q), (W, H),
                             borderMode=cv2.BORDER_REFLECT), 0.2 * q)


def tr_whip(a, b, p):
    """Barrido rápido (whip pan) con desenfoque de movimiento."""
    H, W = a.shape[:2]
    e = e_inout(p)
    off = int(e * W)
    out = np.empty_like(a)
    out[:, :W - off] = a[:, off:]
    out[:, W - off:] = b[:, :off]
    k = int(1 + 150 * np.sin(np.pi * p))
    k += k % 2 == 0
    return cv2.blur(out, (k, 1)) if k > 1 else out


def tr_flash(a, b, p):
    """Corte con destello corto."""
    base = a if p < 0.5 else b
    fl = 0.8 * np.exp(-((p - 0.5) / 0.17) ** 2)
    return cv2.addWeighted(base, 1 - fl, np.full_like(base, (255, 246, 225)), fl, 0)


def tr_desliza(a, b, p):
    """Deslizamiento vertical suave."""
    H, W = a.shape[:2]
    e = e_inout(p)
    off = int(e * H)
    out = np.empty_like(a)
    out[:H - off] = a[off:]
    out[H - off:] = b[:off]
    return out


TRANS = {"corte": (tr_corte, 0.0), "zoom": (tr_zoom, 0.42), "whip": (tr_whip, 0.34), "flash": (tr_flash, 0.26),
         "desliza": (tr_desliza, 0.45)}


# ============================================================ capas gráficas
class Capas:
    def __init__(self, W, H):
        self.W, self.H = W, H
        self.vert = H > W
        self.k = 1.0 if self.vert else 0.84
        k = self.k
        # zonas seguras (vertical): 250 px arriba, 400 px abajo
        self.y_top = 250 if self.vert else 70
        self.y_bot = H - 400 if self.vert else H - 70
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.hypot(xx - W / 2, yy - H / 2) / np.hypot(W / 2, H / 2)
        self.vig = (1 - 0.14 * r ** 2.4)[..., None].astype(np.float32)
        # gradientes de legibilidad arriba y abajo
        y = yy[:, :1] / H
        self.grad = (1 - 0.42 * np.clip((0.38 - y) / 0.30, 0, 1) - 0.50 * np.clip((y - 0.62) / 0.30, 0, 1))[..., None]
        T = lambda txt, ruta, tam, col=BLANCO, tr=0, esp=0: sprite([(txt, col)], ruta, int(tam * k), int(tr * k), espaciado=esp)
        self.t1 = T(DATOS["titulo1"], F_ANTON, 110)
        self.t2 = T(DATOS["titulo2"], F_ANTON, 178 if self.vert else 150, MAIZ_C)
        self.maiz = T(DATOS["maiz"], F_ANTON, 260 if self.vert else 200, MAIZ_C)
        self.alfa = T(DATOS["alfa"], F_ANTON, 260 if self.vert else 200, (150, 214, 96))
        tb = T(DATOS["bolsas"], F_MONT, 54)
        w = tb.shape[1] - int(54 * k * 0.7) + int(80 * k)
        self.bolsas = sobre(caja(w, int(100 * k), int(50 * k), VERDE_OSC, 0.92), tb,
                            int(40 * k) - int(54 * k * 0.35), int((100 * k - tb.shape[0]) / 2) + int(2 * k))
        self.bolsas = sobre(caja(w + 8, int(100 * k) + 8, int(54 * k), MAIZ_C), self.bolsas, 4, 4)
        self.pin = icono_pin(int(80 * k))
        self.ruta = T(DATOS["ruta"], F_ANTON, 92, BLANCO)
        self.loc = T(DATOS["localidad"].upper(), F_BEBAS, 70, ORO, esp=int(4 * k))
        self.logo = logo_circular(int((300 if self.vert else 220) * k))
        self.nombre = T(DATOS["nombre"], F_ANTON, 92 if self.vert else 78, BLANCO)
        self.rubro = T(DATOS["rubro"], F_MONT, 40, ORO)
        self.cta = T(DATOS["cta"], F_ANTON, 120 if self.vert else 96, MAIZ_C)
        self.veni = T(DATOS["veni"], F_ANTON, 112 if self.vert else 90, MAIZ_C)
        self.tel = [T(n, F_ANTON, 74 if self.vert else 60, BLANCO) for n in DATOS["telefonos"]]
        self.ic_tel = icono_whatsapp(int(64 * k))
        loc_txt = T(f"{DATOS['ruta']} · {DATOS['localidad']}", F_MONT, 40, BLANCO)
        self.loc_linea = loc_txt
        self._subs = {}

    # ---- subtítulos estilo Reels (palabra activa en amarillo)
    def subtitulo(self, f, palabras, activa, t_ent):
        k = self.k
        clave = (tuple(palabras), activa)
        if clave not in self._subs:
            tam = int(70 * k)
            fu = fuente(F_MONT, tam)
            partes = []
            for i, (w, marcada) in enumerate(palabras):
                col = MAIZ_C if (i == activa or (marcada and i < activa)) else BLANCO
                if i == activa:
                    col = ORO
                partes.append((w + (" " if i < len(palabras) - 1 else ""), col))
            s = sprite(partes, F_MONT, tam, trazo=int(7 * k), color_trazo=NEGRO, sombra=0.5)
            while s.shape[1] > self.W - 60 and tam > 30:
                tam -= 4
                s = sprite(partes, F_MONT, tam, trazo=int(7 * k), color_trazo=NEGRO, sombra=0.5)
            self._subs[clave] = s
        s = self._subs[clave]
        q = e_back(prog(t_ent, 0, 0.16), 2.0)
        y = self.y_bot - int(90 * k) if self.vert else self.H - int(70 * k)
        blit(f, s, self.W / 2, y, alpha=clamp01(t_ent / 0.08), escala=0.9 + 0.1 * q)


def letras_pop(f, spr, cx, cy, t, t0, dur=0.42):
    q = prog(t, t0, dur)
    if q > 0:
        blit(f, spr, cx, cy + (1 - e_out(q)) * 60, alpha=clamp01(q * 3), escala=max(e_back(q, 2.2), 0.01))


def desliza(f, spr, cx, cy, t, t0, desde=1, dur=0.45, dist=None):
    q = prog(t, t0, dur)
    if q > 0:
        dist = dist or f.shape[1]
        blit(f, spr, cx + desde * (1 - e_out(q)) * dist, cy, alpha=clamp01(q * 3))


def brillos(f, t, zona, n, semilla, op):
    if op <= 0.01:
        return f
    rng = np.random.default_rng(semilla)
    out = f.astype(np.float32)
    x0, y0, x1, y1 = zona
    for _ in range(n):
        cx, cy = rng.uniform(x0, x1), rng.uniform(y0, y1)
        per, fase, esc = rng.uniform(1.0, 2.0), rng.uniform(0, 6.28), rng.uniform(16, 34)
        a = max(0.0, np.sin(t * 2 * np.pi / per + fase)) ** 4 * op
        if a < 0.03:
            continue
        l = int(esc * 3)
        yy, xx = np.mgrid[-l:l + 1, -l:l + 1].astype(np.float32)
        estrella = (np.exp(-np.abs(xx) / 1.4) * np.exp(-np.abs(yy) / esc) + np.exp(-np.abs(yy) / 1.4) * np.exp(-np.abs(xx) / esc)
                    + np.exp(-(xx ** 2 + yy ** 2) / 18)) * a
        xa, ya = int(cx) - l, int(cy) - l
        xa0, ya0 = max(xa, 0), max(ya, 0)
        xa1, ya1 = min(xa + 2 * l + 1, f.shape[1]), min(ya + 2 * l + 1, f.shape[0])
        if xa0 < xa1 and ya0 < ya1:
            out[ya0:ya1, xa0:xa1] += estrella[ya0 - ya:ya1 - ya, xa0 - xa:xa1 - xa, None] * np.array([255, 236, 180])
    return np.clip(out, 0, 255).astype(np.uint8)


# ============================================================ cortes (montaje)
def corte_principal():
    """Devuelve (tomas con transición de entrada, voces [(beat, clave)], textos)."""
    tomas = [
        # HOOK 0–8 beats: granos cayendo de la mano, speed ramp a cámara lenta
        ("corte", Toma("c1_lento", 8, "calido", ((0.5, 0.42, 1.35), (0.5, 0.45, 1.12)), src=5.15,
                       tramos=((0, 1.0), (0.55, 0.3)))),
        # MAÍZ 8–24
        ("zoom", Toma("c3", 4, "calido", ((0.5, 0.55, 1.05), (0.5, 0.5, 1.18)), src=2.1)),
        ("corte", Toma("c1", 4, "calido", ((0.45, 0.35, 1.25), (0.5, 0.42, 1.1)), src=0.0, tramos=((0, 0.7),))),
        ("corte", Toma("c3_lento", 4, "calido", ((0.5, 0.5, 1.12), (0.5, 0.48, 1.25)), src=6.2, tramos=((0, 0.42),))),
        ("whip", Toma("bolsa", 4, "calido", ((0.5, 0.55, 1.0), (0.5, 0.5, 1.12)))),
        # ALFA 24–36
        ("flash", Toma("fardos", 6, "verde", ((0.35, 0.55, 1.0), (0.55, 0.5, 1.18)))),
        ("zoom", Toma("camiones", 6, "noche", ((0.29, 0.47, 1.0), (0.32, 0.42, 1.14)))),
        # PRESENCIA 36–48
        ("whip", Toma("galpon_a", 6, "noche", ((0.25, 0.5, 1.0), (0.62, 0.5, 1.0)), panel=True)),
        ("corte", Toma("galpon_b", 6, "noche", ((0.3, 0.5, 1.35), (0.45, 0.5, 1.0)), panel=True)),
    ]
    voces = [(1.0, "L1"), (9.0, "L2"), (25.0, "L3"), (37.0, "L4"), (50.0, "L5")]
    cierre_beat, fin_beat = 48, 65
    return tomas, voces, cierre_beat, fin_beat


def corte_estado():
    tomas = [
        ("corte", Toma("c1_lento", 6, "calido", ((0.5, 0.42, 1.35), (0.5, 0.45, 1.12)), src=5.15,
                       tramos=((0, 1.0), (0.5, 0.3)))),
        ("zoom", Toma("c3_lento", 4, "calido", ((0.5, 0.5, 1.12), (0.5, 0.48, 1.25)), src=6.2, tramos=((0, 0.45),))),
        ("whip", Toma("bolsa", 4, "calido", ((0.5, 0.55, 1.0), (0.5, 0.5, 1.12)))),
        ("flash", Toma("fardos", 6, "verde", ((0.35, 0.55, 1.0), (0.55, 0.5, 1.18)))),
    ]
    voces = [(0.8, "L1"), (6.6, "L2"), (14.5, "L3"), (21.0, "L5")]
    return tomas, voces, 20, 30


def corte_cuadrado():
    return corte_principal()


CORTES = {
    "principal": ("forralitas_promo_9x16.mp4", 1080, 1920, corte_principal),
    "estado": ("forralitas_promo_15s_estado.mp4", 1080, 1920, corte_estado),
    "cuadrado": ("forralitas_promo_1x1.mp4", 1080, 1080, corte_cuadrado),
}


# ============================================================ voz
def preparar_voces(voces):
    out = []
    for beat, clave in voces:
        audio, tiempos = voz_tts.clip_palabras(VOZ[clave], voz=VOZ_NOMBRE, rate=VOZ_VELOCIDAD)
        pal_sub = SUBS[clave].replace("|", "").split()
        assert len(pal_sub) == len(VOZ[clave].split()), clave
        out.append(dict(clave=clave, t0=beat * BEAT, audio=audio, tiempos=tiempos, dur=len(audio) / SR,
                        palabras=[(w.replace("*", ""), w.startswith("*")) for w in pal_sub],
                        bloques=[len(b.split()) for b in SUBS[clave].split("|")]))
    return out


def grupos_subtitulo(v, max_pal=None):
    """Bloques de subtítulo según los "|" de SUBS."""
    grupos, i = [], 0
    for n in v["bloques"]:
        grupos.append(list(range(i, i + n)))
        i += n
    return grupos


# ============================================================ render
class Render:
    def __init__(self, corte):
        self.nombre_archivo, self.W, self.H, fn = CORTES[corte]
        self.corte = corte
        self.tomas, voces, self.cierre_b, fin_b = fn()
        self.voces = preparar_voces(voces)
        self.dur = fin_b * BEAT
        self.c = Capas(self.W, self.H)
        t = 0.0
        self.inicios = []
        for _, tm in self.tomas:
            self.inicios.append(t)
            t += tm.dur
        self.t_cierre = self.cierre_b * BEAT
        for _, tm in self.tomas:
            tm.preparar()
        self.fondo_cierre = None
        # secciones del corte principal (para títulos)
        self.secciones = self._secciones()

    def _secciones(self):
        b = BEAT
        if self.corte == "estado":
            return dict(hook=(0, 6 * b), maiz=(6 * b, 14 * b), alfa=(14 * b, 20 * b), presencia=None)
        return dict(hook=(0, 8 * b), maiz=(8 * b, 24 * b), alfa=(24 * b, 36 * b), presencia=(36 * b, 48 * b))

    # ---- imagen de las tomas
    def cuadro_toma(self, i, t):
        return self.tomas[i][1].cuadro(t - self.inicios[i], self.W, self.H, self.c.vig)

    def base(self, t):
        n = len(self.tomas)
        for i in range(1, n):
            tr, d = TRANS[self.tomas[i][0]]
            b = self.inicios[i]
            if d and b - d / 2 <= t < b + d / 2:
                p = (t - (b - d / 2)) / d
                return tr(self.cuadro_toma(i - 1, t), self.cuadro_toma(i, t), p)
        i = max(k for k in range(n) if t >= self.inicios[k])
        return self.cuadro_toma(i, t)

    # ---- cierre
    def cierre(self, t):
        c, W, H, k = self.c, self.W, self.H, self.c.k
        if self.fondo_cierre is None:
            img = material("c3").at(10.3)
            img = recorte(img, W // 4, H // 4, 0.5, 0.5, 1.2)
            self.fondo_cierre = cv2.resize(cv2.GaussianBlur(img, (0, 0), 6), (W, H))
        z = 1 + 0.04 * t / 8
        M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, z)
        f = cv2.warpAffine(self.fondo_cierre, M, (W, H), borderMode=cv2.BORDER_REFLECT).astype(np.float32)
        verde = np.array(VERDE_OSC, np.float32)
        f = (f * 0.20 + verde * 0.80)
        f = np.clip(f * c.vig, 0, 255).astype(np.uint8)
        f = brillos(f, t, (0, 0, W, H), 10, 7, 0.35)
        if self.c.vert:
            y_logo, y_nom, y_rub, y_lin, y_ruta, y_tel, y_cta = 455, 680, 752, 800, 880, 1075, 1290
        else:
            y_logo, y_nom, y_rub, y_lin, y_ruta, y_tel, y_cta = 150, 300, 352, 386, 450, 600, 830
        q = prog(t, 0.05, 0.6)
        blit(f, c.logo, W / 2, y_logo, alpha=clamp01(q * 3), escala=max(e_back(q, 1.6), 0.01), ang=-20 * (1 - e_out(q)))
        letras_pop(f, c.nombre, W / 2, y_nom, t, 0.35)
        q = prog(t, 0.6, 0.45)
        blit(f, c.rubro, W / 2, y_rub, alpha=clamp01(q * 3))
        q = e_out(prog(t, 0.6, 0.5))
        cv2.line(f, (int(W / 2 - 260 * k * q), y_lin), (int(W / 2 + 260 * k * q), y_lin), MAIZ_C, max(2, int(4 * k)), cv2.LINE_AA)
        # ubicación
        q = prog(t, 0.9, 0.45)
        ancho = c.ruta.shape[1] + c.pin.shape[1]
        x0 = W / 2 - ancho / 2
        blit(f, c.pin, x0 + c.pin.shape[1] / 2, y_ruta, alpha=clamp01(q * 3), escala=max(e_back(q, 2.2), 0.01))
        desliza(f, c.ruta, x0 + c.pin.shape[1] + c.ruta.shape[1] / 2 - 10 * k, y_ruta, t, 0.95, 1, 0.45, 300 * k)
        letras_pop(f, c.loc, W / 2, y_ruta + 80 * k, t, 1.15)
        # teléfonos
        for j, spr in enumerate(c.tel):
            tj = 1.5 + 0.25 * j
            y = y_tel + j * int(92 * k)
            q = prog(t, tj, 0.45)
            if q <= 0:
                continue
            ancho = spr.shape[1] + c.ic_tel.shape[1]
            x0 = W / 2 - ancho / 2
            blit(f, c.ic_tel, x0 + c.ic_tel.shape[1] / 2, y, alpha=clamp01(q * 3), escala=max(e_back(q, 2.2), 0.01))
            desliza(f, spr, x0 + c.ic_tel.shape[1] + spr.shape[1] / 2 + 6 * k, y, t, tj, -1, 0.45, 300 * k)
        # llamada a la acción
        q = prog(t, 2.2, 0.5)
        if q > 0:
            pul = 1 + 0.035 * np.sin((t - 2.7) * 5.5) * clamp01((t - 2.7) * 2)
            blit(f, c.cta, W / 2, y_cta, alpha=clamp01(q * 3), escala=max(e_back(q, 2.0), 0.01) * pul)
        return f

    # ---- títulos por sección
    def titulos(self, f, t):
        c, W, k = self.c, self.W, self.c.k
        s = self.secciones
        top = c.y_top
        if t < s["hook"][1] + 0.1:
            sale = 1 - prog(t, s["hook"][1] - 0.25, 0.25)
            q = prog(t, 0.35, 0.4)
            blit(f, c.t1, W / 2 - (1 - e_out(q)) * W, top + 90 * k, alpha=clamp01(q * 3) * sale)
            q = prog(t, 0.6, 0.5)
            blit(f, c.t2, W / 2, top + 230 * k, alpha=clamp01(q * 3) * sale, escala=max(e_back(q, 1.8), 0.01) * (1 + 0.6 * (1 - e_out(q))))
        a, b = s["maiz"]
        if a - 0.1 <= t < b + 0.1:
            sale = 1 - prog(t, b - 0.25, 0.25)
            tl = t - a
            q = prog(tl, 0.15, 0.45)
            blit(f, c.maiz, W / 2, top + 150 * k, alpha=clamp01(q * 3) * sale, escala=max(e_back(q, 1.8), 0.01))
            v2 = next((v for v in self.voces if v["clave"] == "L2"), None)
            t_bol = (v2["t0"] + v2["tiempos"][3] - 0.15) if v2 else a + 1.5
            q = prog(t, t_bol, 0.45)
            blit(f, c.bolsas, W / 2, top + 330 * k, alpha=clamp01(q * 3) * sale, escala=max(e_back(q, 2.0), 0.01))
        a, b = s["alfa"]
        if a - 0.1 <= t < b + 0.1:
            sale = 1 - prog(t, b - 0.25, 0.25)
            q = prog(t - a, 0.2, 0.45)
            blit(f, c.alfa, W / 2, top + 150 * k, alpha=clamp01(q * 3) * sale, escala=max(e_back(q, 1.8), 0.01))
        if s["presencia"]:
            a, b = s["presencia"]
            if a - 0.1 <= t < b + 0.1:
                sale = 1 - prog(t, b - 0.25, 0.25)
                v4 = next(v for v in self.voces if v["clave"] == "L4")
                t_ruta = v4["t0"] + v4["tiempos"][3] - 0.2
                y = int(self.H * PANEL_Y + self.W * 0.94 * PANEL_RATIO / 2 + 110 * k) if c.vert else int(self.H * 0.40 + self.W * 0.80 * 0.52 / 2 + 70 * k)
                q = prog(t - a, 0.15, 0.45)
                blit(f, c.veni, W / 2 - (1 - e_out(q)) * W, top + 70 * k, alpha=clamp01(q * 3) * sale)
                q = prog(t, t_ruta, 0.45)
                ancho = c.ruta.shape[1] + c.pin.shape[1]
                x0 = W / 2 - ancho / 2
                blit(f, c.pin, x0 + c.pin.shape[1] / 2, y, alpha=clamp01(q * 3) * sale, escala=max(e_back(q, 2.2), 0.01))
                desliza(f, c.ruta, x0 + c.pin.shape[1] + c.ruta.shape[1] / 2 - 10 * k, y, t, t_ruta + 0.05, 1, 0.45, 300 * k)
                t_loc = v4["t0"] + v4["tiempos"][-2] - 0.15
                q = prog(t, t_loc, 0.4)
                blit(f, c.loc, W / 2, y + 85 * k, alpha=clamp01(q * 3) * sale, escala=max(e_back(q, 2.2), 0.01))

    def subtitulos(self, f, t):
        for v in self.voces:
            if not (v["t0"] - 0.1 <= t <= v["t0"] + v["dur"] + 0.4):
                continue
            tiempos = [v["t0"] + x for x in v["tiempos"]]
            grupos = grupos_subtitulo(v)
            for gi, g in enumerate(grupos):
                ini = tiempos[g[0]] - 0.05
                fin = tiempos[grupos[gi + 1][0]] - 0.05 if gi + 1 < len(grupos) else v["t0"] + v["dur"] + 0.4
                if ini <= t < fin:
                    activa = max(j for j, idx in enumerate(g) if tiempos[idx] - 0.03 <= t) if t >= tiempos[g[0]] - 0.03 else 0
                    vis = [(j, v["palabras"][idx]) for j, idx in enumerate(g) if v["palabras"][idx][0] != "_"]
                    act = max([n for n, (j, _) in enumerate(vis) if j <= activa] or [0])
                    self.c.subtitulo(f, [p for _, p in vis], act, t - ini)
                    return

    def frame(self, t):
        t = min(t, self.dur - 1e-3)
        W, H = self.W, self.H
        if t < self.t_cierre - 0.22:
            f = self.base(t)
            f = (f.astype(np.float32) * self.c.grad).astype(np.uint8)
            hook_end = self.secciones["hook"][1]
            if t < hook_end:
                f = brillos(f, t, (W * 0.15, H * 0.35, W * 0.85, H * 0.7), 7, 3, 0.75 * clamp01((t - 1.0) * 2))
            self.titulos(f, t)
        elif t < self.t_cierre + 0.22:
            p = (t - (self.t_cierre - 0.22)) / 0.44
            a = (self.base(t).astype(np.float32) * self.c.grad).astype(np.uint8)
            self.titulos(a, t)
            f = tr_zoom(a, self.cierre(max(t - self.t_cierre, 0)), p)
        else:
            f = self.cierre(t - self.t_cierre)
        # entrada: destello cálido al inicio
        if t < 0.35:
            a = 0.85 * (1 - t / 0.35) ** 2
            f = cv2.addWeighted(f, 1 - a, np.full_like(f, (255, 246, 225)), a, 0)
        f = np.ascontiguousarray(f)
        self.subtitulos(f, t)
        return f

    # ============================================================ audio
    def cortes_t(self):
        return [(self.inicios[i], self.tomas[i][0]) for i in range(1, len(self.tomas))] + [(self.t_cierre, "zoom")]

    def ambiente(self, n):
        """Sonido real de los clips, bajo y limpio (afftdn), siguiendo la velocidad de cada toma."""
        amb = np.zeros(n, np.float32)
        src_audio = {"c1": ("material/clip1_maiz_tolva.mp4", 0.0), "c1_lento": ("material/clip1_maiz_tolva.mp4", 0.0),
                     "c3": ("material/clip3_manos_bolsa.mp4", 0.0), "c3_lento": ("material/clip3_manos_bolsa.mp4", 0.0)}
        cache = {}
        for (tr, tm), t0 in zip(self.tomas, self.inicios):
            if tm.mat not in src_audio:
                continue
            ruta, _ = src_audio[tm.mat]
            if ruta not in cache:
                raw = subprocess.run(["ffmpeg", "-v", "error", "-i", ruta, "-af", "afftdn=nf=-25,highpass=f=120",
                                      "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
                cache[ruta] = np.frombuffer(raw, np.float32)
            a = cache[ruta]
            m = int(tm.dur * SR)
            ts = np.arange(m) / SR
            src_t = np.array([tm.src + tm.tiempo(x) for x in ts[::441]])
            src_t = np.interp(ts, ts[::441], src_t)
            idx = np.clip((src_t * SR).astype(int), 0, len(a) - 1)
            seg = a[idx]
            env = np.minimum(np.minimum(ts / 0.05, 1), np.minimum((tm.dur - ts) / 0.05, 1))
            i0 = int(t0 * SR)
            amb[i0:i0 + m] += (seg * env)[:max(0, n - i0)]
        return amb

    def audio(self, ruta_wav):
        n = int(self.dur * SR)
        # voz
        voz = np.zeros(n, np.float32)
        for v in self.voces:
            x = v["audio"] * (10 ** (-18 / 20) / (np.sqrt((v["audio"] ** 2).mean()) + 1e-9))
            i = int(v["t0"] * SR)
            voz[i:i + x.size] += x[:max(0, n - i)]
        voz = sosfilt(butter(2, 80, btype="highpass", fs=SR, output="sos"), voz)
        # música
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(MUSICA_INICIO), "-t", str(self.dur + 1), "-i", MUSICA,
                              "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
        mus = np.frombuffer(raw, np.float32).reshape(-1, 2)[:n].copy()
        if len(mus) < n:
            mus = np.pad(mus, ((0, n - len(mus)), (0, 0)))
        mus *= 10 ** (-21 / 20) / (np.sqrt((mus ** 2).mean()) + 1e-9)
        # ducking: la música baja ~10 dB cuando habla la voz
        env = np.sqrt(np.convolve(voz ** 2, np.ones(int(0.04 * SR)) / int(0.04 * SR), mode="same"))
        act = (env > 0.01).astype(np.float32)
        kk = int(0.35 * SR)
        sm = np.convolve(np.pad(act, (kk, kk), mode="edge"), np.ones(kk) / kk, mode="same")[kk:-kk]
        mus *= (1 - 0.68 * np.clip(sm * 1.4, 0, 1))[:, None]
        fi, fo = int(0.15 * SR), int(1.6 * SR)
        mus[:fi] *= np.linspace(0, 1, fi)[:, None]
        mus[-fo:] *= np.linspace(1, 0, fo)[:, None]
        # ambiente real
        amb = self.ambiente(n)
        amb *= 10 ** (-34 / 20) / (np.sqrt((amb[amb != 0] ** 2).mean()) + 1e-9) if np.any(amb) else 1
        # efectos
        sfx = np.zeros(n, np.float32)

        def poner(x, t, g):
            i = int(t * SR)
            if 0 <= i < n:
                m = min(len(x), n - i)
                sfx[i:i + m] += x[:m] * g
        for t, tr in self.cortes_t():
            if tr in ("whip", "zoom"):
                poner(sfxlib.whoosh(0.5), t - 0.25, 0.10)
            elif tr == "flash":
                poner(sfxlib.whoosh(0.35), t - 0.18, 0.07)
        golpe = sfxlib.golpe()
        golpe = sosfilt(butter(2, 900, btype="lowpass", fs=SR, output="sos"), golpe)
        poner(golpe, 0.62, 0.30)                                       # impacto suave del título
        pop = np.sin(2 * np.pi * 900 * np.arange(int(0.06 * SR)) / SR) * np.exp(-np.arange(int(0.06 * SR)) / SR * 70)
        s = self.secciones
        for t in (s["maiz"][0] + 0.18, s["alfa"][0] + 0.22, self.t_cierre + 0.4, self.t_cierre + 2.25):
            poner(pop, t, 0.06)
        mix = mus + (voz + amb + sfx)[:, None]
        tmp = ruta_wav.replace(".wav", "_crudo.wav")
        wavfile.write(tmp, SR, np.clip(mix, -1, 1).astype(np.float32))
        # máster: compresión suave + loudnorm en dos pasadas (-14 LUFS, pico -1 dBTP) a 48 kHz
        cadena = "acompressor=threshold=-20dB:ratio=2.2:attack=15:release=180:makeup=2"
        med = subprocess.run(["ffmpeg", "-hide_banner", "-i", tmp, "-af", cadena + ",loudnorm=I=-14:TP=-1.5:LRA=9:print_format=json",
                              "-f", "null", "-"], capture_output=True, text=True).stderr
        j = json.loads(med[med.rfind("{"):med.rfind("}") + 1])
        ln = (f"loudnorm=I=-14:TP=-1.5:LRA=9:measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
              f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af", f"{cadena},{ln},alimiter=limit=0.89:level=false",
                        "-ar", "48000", "-ac", "2", ruta_wav], check=True)
        return ruta_wav

    # ============================================================ salida
    def exportar(self):
        os.makedirs("cache", exist_ok=True)
        wav = self.audio(f"cache/audio_{self.corte}.wav")
        salida = os.path.join(SALIDA, self.nombre_archivo)
        n = int(round(self.dur * FPS))
        cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{self.W}x{self.H}",
               "-r", str(FPS), "-i", "-", "-i", wav, "-map", "0:v", "-map", "1:a",
               "-c:v", "libx264", "-profile:v", "high", "-preset", "slow", "-b:v", "14M", "-minrate", "12M", "-maxrate", "16M",
               "-bufsize", "16M", "-x264-params", "nal-hrd=vbr", "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709",
               "-colorspace", "bt709", "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-shortest",
               "-movflags", "+faststart", salida]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for i in range(n):
            p.stdin.write(self.frame(i / FPS).tobytes())
            if i % 90 == 0:
                print(f"{self.corte}: {i}/{n}", flush=True)
        p.stdin.close()
        p.wait()
        print("Listo:", salida)
        return salida


# ============================================================ subtítulos .srt, guion y portada
def escribir_srt(r, ruta):
    def ts(x):
        ms = int(round(x * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    lineas, k = [], 1
    for v in r.voces:
        tiempos = [v["t0"] + x for x in v["tiempos"]]
        grupos = grupos_subtitulo(v, max_pal=6)
        for gi, g in enumerate(grupos):
            ini = tiempos[g[0]]
            fin = tiempos[grupos[gi + 1][0]] - 0.02 if gi + 1 < len(grupos) else v["t0"] + v["dur"] + 0.3
            txt = " ".join(v["palabras"][i][0] for i in g if v["palabras"][i][0] != "_")
            lineas.append(f"{k}\n{ts(ini)} --> {ts(fin)}\n{txt}\n")
            k += 1
    open(ruta, "w", encoding="utf-8").write("\n".join(lineas))


def escribir_guion(r, ruta):
    txt = ["GUION DE LOCUCIÓN — Forrajería Forralitas (corte principal, ~33 s)",
           "Voz: masculina, rioplatense, cálida. Ritmo tranquilo, con las pausas indicadas.", ""]
    for v in r.voces:
        txt.append(f"[{v['t0']:5.1f} s]  {VOZ[v['clave']]}")
    txt += ["", "Lectura de números: 40 = cuarenta, 50 = cincuenta, Ruta 305 = trescientos cinco, km 7,5 = siete y medio.",
            "Si grabás tu propia voz: grabá cada frase por separado, en un lugar silencioso, y reemplazá la voz",
            "generada (ver README.txt)."]
    open(ruta, "w", encoding="utf-8").write("\n".join(txt) + "\n")


def portada(ruta):
    W, H = 1080, 1920
    c = Capas(W, H)
    img = material("c3").at(7.6)
    g = Grade("calido", cv2.resize(img, (240, 432)))
    f = g(recorte(img, W, H, 0.5, 0.5, 1.12), c.vig)
    f = (f.astype(np.float32) * c.grad).astype(np.uint8)
    f = brillos(f, 0.4, (W * 0.2, H * 0.4, W * 0.8, H * 0.65), 8, 3, 1.0)
    blit(f, c.t1, W / 2, 360)
    blit(f, c.t2, W / 2, 500)
    sub = sprite([("MAÍZ  ·  ALFA", BLANCO)], F_ANTON, 96, 0)
    blit(f, sub, W / 2, 650)
    blit(f, logo_circular(220), W / 2, 1290)
    blit(f, c.nombre, W / 2, 1450)
    linea = sprite([(f"{DATOS['ruta']} · {DATOS['localidad']}", ORO)], F_MONT, 42, 0)
    blit(f, linea, W / 2, 1525)
    Image.fromarray(f).save(ruta, quality=94)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corte", choices=list(CORTES), action="append")
    ap.add_argument("--cuadros", nargs="*", type=float)
    a = ap.parse_args()
    cortes = a.corte or list(CORTES)
    for corte in cortes:
        r = Render(corte)
        if a.cuadros is not None:
            os.makedirs("cache/previas", exist_ok=True)
            for t in a.cuadros:
                Image.fromarray(r.frame(t)).save(f"cache/previas/{corte}_{t:05.2f}.png")
            print(corte, "duración", round(r.dur, 2))
            continue
        r.exportar()
        if corte == "principal":
            escribir_srt(r, os.path.join(SALIDA, "subtitulos.srt"))
            escribir_guion(r, os.path.join(SALIDA, "guion_locucion.txt"))
            portada(os.path.join(SALIDA, "portada_1080x1920.jpg"))


if __name__ == "__main__":
    main()
