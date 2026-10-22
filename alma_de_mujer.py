"""Video publicitario de Alma de Mujer Lencería (vertical 1080x1920, ~20 s, sin audio).

Uso:
    python alma_de_mujer.py                   # genera videos_salida/alma_de_mujer.mp4
    python alma_de_mujer.py --frames 1 5 9.5  # vistas previas PNG en videos_salida/

Las fotos y el logo salen de assets/alma/ (ver alma_prep.py). Qué foto va en cada escena y
qué texto lleva: ver PRODUCTOS y MONTAJE (abajo).
"""
import argparse
import math
import subprocess
from functools import lru_cache
from multiprocessing import Pool
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
A = Path(__file__).parent / "assets/alma"
FOTOS = A / "fotos"
SALIDA = "videos_salida/alma_de_mujer.mp4"

SCRIPT = "GreatVibes-Regular.ttf"
SERIF = "CormorantGaramond[wght].ttf"
SANS = "Montserrat[wght].ttf"

CREMA = (253, 245, 241)
BLUSH = (244, 222, 218)
ROSA = (199, 102, 120)
ROSA_OSC = (150, 66, 86)
ORO = (196, 146, 84)
ORO_CL = (240, 208, 152)
ORO_OSC = (140, 94, 46)
BLANCO = (255, 255, 255)

# (foto, palabra en cursiva, bajada en mayúsculas)
PRODUCTOS = [
    ("conjunto_blanco_rojo", "Delicada", "CONJUNTOS FLORALES"),
    ("armados_varios", "Conjuntos", "ARMADOS · VARIOS COLORES"),
    (("armado_celeste", "armado_negro", "armado_verde"), "Elegí tu favorito", "VARIEDAD DE COLORES"),
    ("armado_morley", "Armado", "DE MORLEY"),
    ("regulables_algodon", "Regulables", "DE ALGODÓN"),
    ("colaless_lunares", "Colaless", "ALGODÓN CON LUNARES"),
    ("regulables_elastico_ancho", "Elástico ancho", "REGULABLES"),
]
PRECIO = "$4000"          # va sobre la última foto de PRODUCTOS
MONTAJE = ["conjunto_negro_flores", "colaless_estampadas", "armado_durazno", "conjunto_crema_fucsia"]


# ================================================================ easing
def clamp01(x):
    return min(1.0, max(0.0, x))


def prog(t, inicio, dur):
    return clamp01((t - inicio) / dur)


def ease_out(x):
    x = clamp01(x)
    return 1 - (1 - x) ** 3


def ease_in_out(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def ease_inout_fuerte(x):
    x = clamp01(x)
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def ease_back(x, s=1.7):
    x = clamp01(x)
    return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


# ================================================================ sprites
# Un sprite es float32 (h, w, 4): RGB 0-255 premultiplicado por alfa, alfa 0-1.
@lru_cache(None)
def fuente(nombre, tam, peso=None):
    f = ImageFont.truetype(str(A / "fuentes" / nombre), tam)
    if peso:
        f.set_variation_by_axes([peso])
    return f


def recortar(m, margen=30):
    ys, xs = np.nonzero(m > 0.01)
    y0, y1 = max(ys.min() - margen, 0), min(ys.max() + margen, m.shape[0])
    x0, x1 = max(xs.min() - margen, 0), min(xs.max() + margen, m.shape[1])
    return m[y0:y1, x0:x1]


def degradado(h, color):
    """color: tupla RGB, o "oro" para un degradado metálico vertical."""
    if color != "oro":
        return np.broadcast_to(np.array(color, np.float32), (h, 1, 3))
    stops = [(0, ORO_OSC), (0.3, ORO_CL), (0.5, ORO), (0.78, ORO_OSC), (1, ORO)]
    y = np.linspace(0, 1, h)
    cols = [np.interp(y, [s[0] for s in stops], [s[1][c] for s in stops]) for c in range(3)]
    return np.stack(cols, -1)[:, None, :].astype(np.float32)


def colorear(m, color):
    rgb = np.broadcast_to(degradado(m.shape[0], color), m.shape + (3,))
    return np.dstack([rgb * m[..., None], m]).astype(np.float32)


def sombra(spr, blur=7, dy=5, k=0.3, color=(120, 50, 66)):
    a = spr[..., 3]
    sh = np.roll(cv2.GaussianBlur(a, (0, 0), blur), dy, 0) * k
    fuera = sh * (1 - a)
    return np.dstack([spr[..., :3] + np.array(color, np.float32) * fuera[..., None], a + fuera])


def mascara_texto(txt, f, tracking=0):
    asc, desc = f.getmetrics()
    pad = int(f.size * 0.6)
    anchos = [f.getlength(c) for c in txt]
    w = int(sum(anchos) + tracking * (len(txt) - 1)) + 2 * pad
    m = Image.new("L", (w, asc + desc + 2 * pad), 0)
    d = ImageDraw.Draw(m)
    if tracking == 0:
        d.text((pad, pad), txt, font=f, fill=255)
    else:
        x = pad
        for c, cw in zip(txt, anchos):
            d.text((x, pad), c, font=f, fill=255)
            x += cw + tracking
    return np.asarray(m, np.float32) / 255


@lru_cache(None)
def texto(txt, nombre, tam, color, peso=None, tracking=0, con_sombra=True):
    spr = colorear(recortar(mascara_texto(txt, fuente(nombre, tam, peso), tracking)), color)
    return sombra(spr) if con_sombra else spr


@lru_cache(None)
def letras(txt, nombre, tam, color, peso=None, tracking=0):
    """Un sprite por letra (misma línea de base) con su desplazamiento desde el centro."""
    f = fuente(nombre, tam, peso)
    anchos = [f.getlength(c) for c in txt]
    x = -(sum(anchos) + tracking * (len(txt) - 1)) / 2
    out = []
    for c, cw in zip(txt, anchos):
        if c != " ":
            out.append((sombra(colorear(mascara_texto(c, f), color), 5, 4, 0.22), x + cw / 2))
        x += cw + tracking
    return out


def poner(frame, spr, cx, cy, alpha=1.0, escala=1.0, angulo=0.0):
    """Compone un sprite centrado en (cx, cy) sobre el frame float32."""
    if alpha <= 0.003 or escala <= 0.01:
        return
    if escala != 1.0 or angulo != 0.0:
        h, w = spr.shape[:2]
        M = cv2.getRotationMatrix2D((w / 2, h / 2), angulo, escala)
        c, s = abs(M[0, 0]), abs(M[0, 1])
        nw, nh = int(w * c + h * s) + 2, int(w * s + h * c) + 2
        M[0, 2] += nw / 2 - w / 2
        M[1, 2] += nh / 2 - h / 2
        spr = cv2.warpAffine(spr, M, (nw, nh), flags=cv2.INTER_LINEAR)
    h, w = spr.shape[:2]
    x, y = int(round(cx - w / 2)), int(round(cy - h / 2))
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if x0 >= x1 or y0 >= y1:
        return
    s = spr[y0 - y:y1 - y, x0 - x:x1 - x]
    reg = frame[y0:y1, x0:x1]
    reg *= 1 - s[..., 3:4] * alpha
    reg += s[..., :3] * alpha


def luz(frame, rgb, cx, cy, k=1.0):
    """Mezcla en modo trama (screen) una luz RGB 0-255 centrada en (cx, cy)."""
    if k <= 0.003:
        return
    h, w = rgb.shape[:2]
    x, y = int(round(cx - w / 2)), int(round(cy - h / 2))
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if x0 >= x1 or y0 >= y1:
        return
    s = rgb[y0 - y:y1 - y, x0 - x:x1 - x]
    reg = frame[y0:y1, x0:x1]
    reg[:] = 255 - (255 - reg) * (1 - s * (k / 255))


def wipe(spr, p, borde=0.18):
    """Revela el sprite de izquierda a derecha con borde suave (efecto escritura)."""
    if p >= 1:
        return spr
    x = np.arange(spr.shape[1], dtype=np.float32) / spr.shape[1]
    m = np.clip((p * (1 + borde) - x) / borde, 0, 1)
    return spr * m[None, :, None]


def brillo(spr, pos, ancho=0.1, k=0.7):
    """Destello diagonal que cruza el sprite (pos de -0.2 a 1.2)."""
    if not -0.3 < pos < 1.3:
        return spr
    h, w = spr.shape[:2]
    yy, xx = np.mgrid[:h, :w].astype(np.float32)
    u = (xx + yy * 0.45) / (w + h * 0.45)
    banda = np.exp(-((u - pos) / ancho) ** 2) * k
    out = spr.copy()
    a = spr[..., 3:4]
    out[..., :3] = np.minimum(spr[..., :3] + 255 * banda[..., None] * a, 255 * a)
    return out


def poner_letras(frame, ls, cx, cy, t, t0, paso=0.025, dur=0.4, subir=26, alpha=1.0):
    for i, (spr, dx) in enumerate(ls):
        q = ease_out(prog(t, t0 + i * paso, dur))
        poner(frame, spr, cx + dx, cy + (1 - q) * subir, alpha * q)


@lru_cache(None)
def redondeado(w, h, r):
    ss = 3
    m = Image.new("L", (w * ss, h * ss), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w * ss - 1, h * ss - 1), r * ss, fill=255)
    return np.asarray(m.resize((w, h), Image.LANCZOS), np.float32) / 255


@lru_cache(None)
def corazon(lado, color, relleno=True):
    ss = 4
    L = lado * ss
    t = np.linspace(0, 2 * np.pi, 200)
    x = 16 * np.sin(t) ** 3
    y = -(13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t))
    pts = [(L / 2 + xi * L / 36, L / 2 + yi * L / 36) for xi, yi in zip(x, y)]
    m = Image.new("L", (L, L), 0)
    d = ImageDraw.Draw(m)
    if relleno:
        d.polygon(pts, fill=255)
    else:
        d.line(pts + pts[:1], fill=255, width=int(L * 0.07), joint="curve")
    m = np.asarray(m.resize((lado, lado), Image.LANCZOS), np.float32) / 255
    return colorear(m, color)


@lru_cache(None)
def destello(lado=140):
    c = (lado - 1) / 2
    yy, xx = np.mgrid[:lado, :lado].astype(np.float32) - c
    r = np.hypot(xx, yy)
    s = (np.exp(-(xx / 2.2) ** 2 - (yy / (lado * 0.3)) ** 2) + np.exp(-(yy / 2.2) ** 2 - (xx / (lado * 0.3)) ** 2)
         + 0.9 * np.exp(-(r / 7) ** 2) + 0.25 * np.exp(-(r / 22) ** 2))
    return np.clip(s, 0, 1)[..., None] * np.array([255, 246, 228], np.float32)


@lru_cache(None)
def bokeh(r, color):
    lado = 2 * r + 4
    yy, xx = np.mgrid[:lado, :lado].astype(np.float32) - (lado - 1) / 2
    d = np.hypot(xx, yy) / r
    a = np.clip((1 - d) / 0.12, 0, 1) * (0.55 + 0.45 * d ** 5)
    return a[..., None] * np.array(color, np.float32)


@lru_cache(None)
def mancha(lado, color):
    """Luz grande y suave para los light leaks."""
    yy, xx = np.mgrid[:lado, :lado].astype(np.float32) - lado / 2
    return np.exp(-(np.hypot(xx, yy) / (lado * 0.28)) ** 2)[..., None] * np.array(color, np.float32)


# ================================================================ recursos
@lru_cache(None)
def foto(nombre, ancho=None):
    im = Image.open(FOTOS / f"{nombre}.jpg").convert("RGB")
    if ancho:
        im = im.resize((ancho, round(im.height * ancho / im.width)), Image.LANCZOS)
    return np.asarray(im, np.float32)


@lru_cache(None)
def fondo_foto(nombre):
    """La misma foto, desenfocada y lavada con rosa, cubriendo toda la pantalla (un 8% más grande)."""
    im = foto(nombre, 400)
    s = max(W * 1.08 / im.shape[1], H * 1.08 / im.shape[0])
    im = cv2.resize(im, (int(im.shape[1] * s), int(im.shape[0] * s)), interpolation=cv2.INTER_CUBIC)
    im = cv2.GaussianBlur(im, (0, 0), 38)
    return im * 0.5 + np.array(BLUSH, np.float32) * 0.5


@lru_cache(None)
def logo(ancho):
    m = Image.open(A / "logo_mascara.png")
    m = m.resize((ancho, round(m.height * ancho / m.width)), Image.LANCZOS)
    return colorear(np.asarray(m, np.float32) / 255, "oro")


@lru_cache(None)
def entrega(lado):
    im = Image.open(A / "entrega_inmediata.png").resize((lado, lado), Image.LANCZOS)
    a = np.asarray(im, np.float32)
    a[..., 3] /= 255
    a[..., :3] *= a[..., 3:4]
    return a


@lru_cache(None)
def fondo_base():
    yy, xx = np.mgrid[:H, :W].astype(np.float32)
    d = np.hypot((xx - W * 0.5) / W, (yy - H * 0.38) / H)
    k = np.clip(d / 0.75, 0, 1)[..., None] ** 1.4
    return np.array(CREMA, np.float32) * (1 - k) + np.array(BLUSH, np.float32) * k


@lru_cache(None)
def particulas():
    rng = np.random.default_rng(7)
    cols = [(255, 236, 214), (255, 255, 255), (246, 196, 202), (240, 210, 160)]
    return [dict(x=rng.uniform(0, W), y=rng.uniform(0, H), r=int(rng.uniform(14, 70)),
                 v=rng.uniform(25, 70), f=rng.uniform(0, 6.28), c=cols[i % 4], k=rng.uniform(0.18, 0.45))
            for i in range(22)]


def fondo(t):
    f = fondo_base().copy()
    poner_bokeh(f, t)
    return f


def poner_bokeh(f, t, k=1.0):
    for p in particulas():
        y = (p["y"] - p["v"] * t) % (H + 200) - 100
        x = p["x"] + 30 * math.sin(t * 0.8 + p["f"])
        tw = 0.65 + 0.35 * math.sin(t * 2.2 + p["f"] * 3)
        luz(f, bokeh(p["r"], p["c"]), x, y, p["k"] * tw * k)


def poner_destellos(f, pts, t, t0, k=1.0):
    """Destellos en estrella que titilan en las posiciones pts=(x, y, fase, tamaño)."""
    for x, y, fase, tam in pts:
        q = prog(t, t0 + fase * 0.5, 0.25)
        tw = q * (0.55 + 0.45 * math.sin((t - t0) * 7 + fase * 9))
        if tw > 0.02:
            s = destello(int(tam))
            luz(f, s, x, y, tw * k)


def corazones(f, t, n=12, semilla=3, k=1.0):
    """Corazoncitos que suben flotando."""
    rng = np.random.default_rng(semilla)
    for i in range(n):
        x0, vel, lado, fase = rng.uniform(60, W - 60), rng.uniform(140, 260), int(rng.uniform(26, 60)), rng.uniform(0, 3)
        color = [ROSA, "oro", (232, 150, 160)][i % 3]
        y = H + 60 - ((t + fase) * vel) % (H + 160)
        x = x0 + 26 * math.sin((t + fase) * 2.4)
        a = 0.85 * clamp01((H + 60 - y) / 300) * k
        poner(f, corazon(lado, color, i % 2 == 0), x, y, a, angulo=14 * math.sin((t + fase) * 2))


def divisor(f, cx, cy, p, largo=150, color=ORO, alpha=1.0):
    """Línea fina con corazón al medio que crece desde el centro."""
    q = ease_out(p)
    if q <= 0:
        return
    l = int(largo * q)
    linea = colorear(np.ones((2, max(l, 1)), np.float32), color)
    poner(f, linea, cx - 34 - l / 2, cy, alpha)
    poner(f, linea, cx + 34 + l / 2, cy, alpha)
    poner(f, corazon(30, ROSA), cx, cy, alpha * q, escala=0.6 + 0.4 * ease_back(p))


# ================================================================ tarjeta de foto
@lru_cache(None)
def marco(w, h, b, r):
    """Paspartú crema con filete dorado, y su sombra."""
    W2, H2 = w + 2 * b, h + 2 * b
    m = redondeado(W2, H2, r + b)
    spr = colorear(m, CREMA)
    filete = redondeado(W2 - 10, H2 - 10, r + b - 5) - np.pad(redondeado(W2 - 14, H2 - 14, r + b - 7), 2)
    filete = np.pad(np.clip(filete, 0, 1), 5)
    spr[..., :3] = spr[..., :3] * (1 - filete[..., None]) + np.array(ORO, np.float32) * filete[..., None] * m[..., None]
    pad = 70
    sa = cv2.GaussianBlur(np.pad(m, pad), (0, 0), 26)
    sh = np.dstack([np.broadcast_to(np.array((110, 50, 64), np.float32), sa.shape + (3,)) * sa[..., None] * 0.33,
                    sa * 0.33])
    return spr, sh


def ken_burns(im, w, h, zoom, px, py):
    ih, iw = im.shape[:2]
    s = max(w / iw, h / ih) * zoom
    mx, my = (iw * s - w) / 2, (ih * s - h) / 2
    M = np.float32([[s, 0, -mx + px * mx], [0, s, -my + py * my]])
    return cv2.warpAffine(im, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def tarjeta(nombre, w, h, zoom, px, py, b=14, r=30):
    spr, sh = marco(w, h, b, r)
    spr = spr.copy()
    im = ken_burns(foto(nombre, int(w * 1.15)), w, h, zoom, px, py)
    m = redondeado(w, h, r)[..., None]
    reg = spr[b:b + h, b:b + w, :3]
    reg[:] = im * m + reg * (1 - m)
    return spr, sh


def poner_tarjeta(f, nombre, cx, cy, w, h, zoom, px, py, alpha=1.0, escala=1.0, angulo=0.0):
    spr, sh = tarjeta(nombre, w, h, zoom, px, py)
    poner(f, sh, cx, cy + 26 * escala, alpha, escala, angulo)
    poner(f, spr, cx, cy, alpha, escala, angulo)


# ================================================================ escenas
# Cada escena es una función render(t, dur) -> frame float32, con t desde su inicio.
def intro(t, dur):
    f = fondo(t)
    luz(f, mancha(900, (255, 255, 255)), W / 2, 820, 0.7 * ease_out(prog(t, 0.1, 1.0)))
    p = ease_inout_fuerte(prog(t, 0.15, 1.15))
    lg = logo(880)
    if p > 0:
        spr = wipe(lg, p, 0.35)
        blur = (1 - p) * 9
        if blur > 0.3:
            spr = cv2.GaussianBlur(spr, (0, 0), blur)
        spr = brillo(spr, (t - 1.25) / 0.8 * 1.5 - 0.2, 0.08, 0.85)
        poner(f, spr, W / 2, 800, clamp01(p * 1.6), 1.07 - 0.07 * p)
    poner_destellos(f, [(250, 560, 0.0, 150), (850, 700, 0.5, 110), (330, 1010, 1.0, 90), (900, 950, 0.3, 130)],
                    t, 1.05)
    q = prog(t, 1.15, 0.9)
    poner(f, wipe(texto("Nueva colección", SCRIPT, 132, ROSA), ease_in_out(q)), W / 2, 1220)
    divisor(f, W / 2, 1345, prog(t, 1.55, 0.6))
    return f


def escena_producto(i):
    nombre, palabra, bajada = PRODUCTOS[i]
    dz = 1 if i % 2 == 0 else -1
    px0, px1 = [(-0.6, 0.6), (0.5, -0.5), (0.0, 0.0), (0.6, -0.4)][i % 4]

    def render(t, dur):
        u = t / dur
        if isinstance(nombre, tuple):
            return collage(t, dur, nombre, palabra, bajada)
        bg = fondo_foto(nombre)
        f = cv2.resize(bg, None, fx=1 + 0.04 * u, fy=1 + 0.04 * u)
        y0, x0 = (f.shape[0] - H) // 2, (f.shape[1] - W) // 2
        f = np.ascontiguousarray(f[y0:y0 + H, x0:x0 + W])
        poner_bokeh(f, t + i * 3, 0.6)
        zoom = 1.02 + 0.1 * (u if dz > 0 else 1 - u)
        e = 0.96 + 0.04 * ease_out(prog(t, 0, 0.7))
        poner_tarjeta(f, nombre, W / 2, 900 + 6 * math.sin(t * 2), 880, 1173, zoom,
                      px0 + (px1 - px0) * u, 0.3 * (1 - 2 * u), escala=e)
        if i == len(PRODUCTOS) - 1:
            etiqueta_precio(f, t)
        rotulo(f, t, palabra, bajada)
        return f
    return render


@lru_cache(None)
def velo():
    y = np.linspace(0, 1, H)
    k = np.maximum(np.clip((y - 0.72) / 0.2, 0, 1) * 0.62, np.clip((0.12 - y) / 0.12, 0, 1) * 0.5)
    return k[:, None, None].astype(np.float32)


def halo(spr, k=0.75):
    """Halo crema suave alrededor del texto para que se lea sobre fondos con foto."""
    return sombra(np.pad(spr, ((14, 14), (14, 14), (0, 0))), 9, 0, k, CREMA)


def aclarar(f):
    v = velo()
    f *= 1 - v
    f += np.array(CREMA, np.float32) * v


def rotulo(f, t, palabra, bajada, y=1615, t0=0.3):
    aclarar(f)
    poner(f, wipe(texto(palabra, SCRIPT, 128, ROSA), ease_in_out(prog(t, t0, 0.65))), W / 2, y)
    ls = letras(bajada, SANS, 34, ROSA_OSC, 600, 7)
    poner_letras(f, ls, W / 2, y + 112, t, t0 + 0.25, paso=0.018, dur=0.35)


def etiqueta_precio(f, t):
    q = prog(t, 0.45, 0.55)
    if q <= 0:
        return
    disco = colorear(redondeado(250, 250, 125), ROSA)
    aro = colorear(np.clip(redondeado(230, 230, 115) - np.pad(redondeado(222, 222, 111), 4), 0, 1), ORO_CL)
    txt = texto(PRECIO, SERIF, 82, BLANCO, 700, 0, False)
    sub = texto("C/U", SANS, 22, CREMA, 600, 4, False)
    spr = disco.copy()
    for s, dy in ((aro, 0), (txt, -8), (sub, 52)):
        h, w = s.shape[:2]
        y, x = 125 + dy - h // 2, 125 - w // 2
        y0, x0 = max(y, 0), max(x, 0)
        reg = spr[y0:y + h, x0:x + w]
        ss = s[y0 - y:y0 - y + reg.shape[0], x0 - x:x0 - x + reg.shape[1]]
        reg[:] = ss + reg * (1 - ss[..., 3:4])
    spr = sombra(np.pad(spr, ((30, 30), (30, 30), (0, 0))), 12, 10, 0.35)
    spr = brillo(spr, (t - 1.1) / 0.6 * 1.4 - 0.2, 0.1, 0.6)
    ang = -12 + 12 * ease_back(q, 2.4) + 3 * math.sin(t * 3) * q
    poner(f, spr, 860, 360, clamp01(q * 3), 0.2 + 0.8 * ease_back(q, 2.2), ang)


def collage(t, dur, nombres, palabra, bajada):
    f = cv2.resize(fondo_foto(nombres[0]), None, fx=1 + 0.03 * t / dur, fy=1 + 0.03 * t / dur)
    y0, x0 = (f.shape[0] - H) // 2, (f.shape[1] - W) // 2
    f = np.ascontiguousarray(f[y0:y0 + H, x0:x0 + W])
    poner_bokeh(f, t + 9, 0.6)
    q = ease_back(prog(t, 0.2, 0.7), 1.3)
    u = t / dur
    for nombre, lado in ((nombres[1], -1), (nombres[2], 1)):
        poner_tarjeta(f, nombre, W / 2 + lado * 285 * q, 880 - 40 * q, 470, 627, 1.04 + 0.06 * u,
                      0, 0, escala=0.85 + 0.12 * q, angulo=-lado * 8 * q)
    e = 0.95 + 0.05 * ease_out(prog(t, 0, 0.6))
    poner_tarjeta(f, nombres[0], W / 2, 930 + 5 * math.sin(t * 2), 600, 800, 1.03 + 0.07 * u, 0, -0.3 + 0.6 * u,
                  escala=e)
    rotulo(f, t, palabra, bajada, y=1600, t0=0.45)
    return f


def montaje(t, dur):
    n = len(MONTAJE)
    slot = dur / n
    i = min(int(t / slot), n - 1)
    tl = t - i * slot
    nombre = MONTAJE[i]
    bg = fondo_foto(nombre)
    y0, x0 = (bg.shape[0] - H) // 2, (bg.shape[1] - W) // 2
    f = np.ascontiguousarray(bg[y0:y0 + H, x0:x0 + W])
    z = 1.14 - 0.1 * ease_out(tl / slot)
    im = ken_burns(foto(nombre, 1200), W, int(W * 1.335), z, 0.4 * (-1) ** i, 0)
    poner(f, np.dstack([im, np.ones(im.shape[:2], np.float32)]), W / 2, H / 2 - 40)
    oscuro = np.linspace(0, 1, H)[:, None, None] ** 3 * 0.55
    f *= 1 - oscuro
    flash = math.exp(-tl / 0.07) if i > 0 else 0
    f[:] = 255 - (255 - f) * (1 - 0.85 * flash)
    poner(f, wipe(texto("y mucho más...", SCRIPT, 140, BLANCO, con_sombra=True), ease_in_out(prog(t, 0.25, 0.8))),
          W / 2, 1640)
    return f


@lru_cache(None)
def rayos():
    L = 2400
    yy, xx = np.mgrid[:L, :L].astype(np.float32) - L / 2
    th = np.arctan2(yy, xx)
    r = np.hypot(xx, yy)
    v = (0.5 + 0.5 * np.cos(th * 16)) ** 5 * np.exp(-(r / 950) ** 2) * np.clip(r / 300, 0, 1)
    return v[..., None] * np.array([255, 238, 220], np.float32)


def escena_entrega(t, dur):
    f = fondo(t + 4)
    cx, cy = W / 2, 880
    ang = t * 9
    M = cv2.getRotationMatrix2D((1200, 1200), ang, 1.0)
    M[0, 2] += cx - 1200
    M[1, 2] += cy - 1200
    r = cv2.warpAffine(rayos(), M, (W, H))
    f[:] = 255 - (255 - f) * (1 - r * (0.55 * ease_out(prog(t, 0.1, 0.6)) / 255))
    corazones(f, t, 12, 5, clamp01(t / 0.5))
    q = prog(t, 0.08, 0.6)
    spr = entrega(880)
    spr = sombra(np.pad(spr, ((40, 40), (40, 40), (0, 0))), 20, 18, 0.35)
    spr = brillo(spr, (t - 0.85) / 0.7 * 1.5 - 0.2, 0.09, 0.55)
    pulso = 1 + 0.012 * math.sin(max(t - 0.7, 0) * 2 * math.pi * 1.2)
    poner(f, spr, cx, cy, clamp01(q * 3), (0.45 + 0.55 * ease_back(q, 1.8)) * pulso, -14 * (1 - ease_out(q)))
    poner_destellos(f, [(150, 520, 0.2, 150), (950, 610, 0.6, 120), (120, 1230, 1.0, 110), (960, 1290, 0.4, 150)],
                    t, 0.5)
    poner(f, wipe(texto("¡Pedilo hoy!", SCRIPT, 140, ROSA), ease_in_out(prog(t, 0.65, 0.7))), W / 2, 1520)
    poner_letras(f, letras("TE LO LLEVAMOS AL TOQUE", SANS, 34, ROSA_OSC, 600, 7), W / 2, 1640, t, 1.0, 0.018)
    return f


def outro(t, dur):
    f = fondo(t + 8)
    luz(f, mancha(1000, (255, 255, 255)), W / 2, 760, 0.65 * ease_out(prog(t, 0.0, 0.8)))
    corazones(f, t, 8, 11, 0.7)
    q = prog(t, 0.1, 0.9)
    spr = logo(820)
    blur = (1 - ease_out(q)) * 12
    if blur > 0.3:
        spr = cv2.GaussianBlur(spr, (0, 0), blur)
    spr = brillo(spr, (t - 0.9) / 0.8 * 1.5 - 0.2, 0.08, 0.85)
    poner(f, spr, W / 2, 740, ease_out(q), 0.9 + 0.1 * ease_out(q))
    poner_destellos(f, [(270, 520, 0.0, 140), (830, 640, 0.4, 110), (900, 930, 0.8, 120)], t, 0.8)
    poner(f, wipe(texto("Porque te lo merecés", SCRIPT, 112, ROSA), ease_in_out(prog(t, 0.6, 0.9))), W / 2, 1175)
    divisor(f, W / 2, 1290, prog(t, 1.2, 0.6), 170)
    poner_letras(f, letras("ESCRIBINOS Y HACÉ TU PEDIDO", SANS, 34, ROSA_OSC, 600, 7), W / 2, 1385, t, 1.4, 0.02)
    poner_letras(f, letras("ROPA INTERIOR · CONJUNTOS · COLALESS", SANS, 24, ORO_OSC, 500, 5), W / 2, 1460, t,
                 1.7, 0.012)
    return f


# ================================================================ transiciones
@lru_cache(None)
def grilla():
    yy, xx = np.mgrid[:H, :W].astype(np.float32)
    dist = np.hypot(xx - W / 2, yy - H * 0.47)
    diag = (xx * 0.9 + yy * 0.44) / (W * 0.9 + H * 0.44)
    return dist, diag


def mezclar(a, b, m):
    return a * (1 - m) + b * m


def brillo_global(f, k, color=(255, 242, 232)):
    return 255 - (255 - f) * (1 - np.array(color, np.float32) / 255 * k)


def tr_iris(a, b, p):
    q = ease_inout_fuerte(p)
    dist, _ = grilla()
    r = q * 1180
    m = np.clip((r - dist) / 5 + 0.5, 0, 1)[..., None]
    out = mezclar(a, b, m)
    aro = np.exp(-((dist - r) / 9) ** 2) + 0.35 * np.exp(-((dist - r) / 40) ** 2)
    return 255 - (255 - out) * (1 - aro[..., None] * np.array(ORO_CL, np.float32) / 255 * (1 - q * 0.6))


def tr_barrido(a, b, p, vertical=False):
    q = ease_inout_fuerte(p)
    if vertical:
        a, b = a.transpose(1, 0, 2), b.transpose(1, 0, 2)
    n = a.shape[1]
    off = int(q * n)
    out = np.concatenate([a[:, off:], b[:, :off]], 1) if off else a.copy()
    k = int(math.sin(math.pi * q) * 150) + 1
    if k > 2:
        out = cv2.blur(out, (k, 1))
    return out.transpose(1, 0, 2) if vertical else out


def tr_flash(a, b, p, k=0.9):
    m = ease_in_out((p - 0.3) / 0.4)
    return brillo_global(mezclar(a, b, m), k * math.sin(math.pi * p) ** 1.5)


def tr_diagonal(a, b, p):
    q = ease_inout_fuerte(p)
    _, s = grilla()
    pos = q * 1.1 - 0.05
    m = np.clip((pos - s) / 0.01 + 0.5, 0, 1)[..., None]
    out = mezclar(a, b, m)
    linea = np.exp(-((s - pos) / 0.004) ** 2) + 0.4 * np.exp(-((s - pos) / 0.03) ** 2)
    return 255 - (255 - out) * (1 - linea[..., None] * np.array(ORO_CL, np.float32) / 255)


def escalar(f, s):
    M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, s)
    return cv2.warpAffine(f, M, (W, H), borderMode=cv2.BORDER_REFLECT)


def tr_zoom(a, b, p):
    q = ease_inout_fuerte(p)
    aa = escalar(a, 1 + 0.4 * q)
    if q > 0.05:
        aa = cv2.GaussianBlur(aa, (0, 0), 1 + 10 * q)
    bb = escalar(b, 0.86 + 0.14 * q)
    return brillo_global(mezclar(aa, bb, q), 0.3 * math.sin(math.pi * q))


# ================================================================ línea de tiempo
TR = 0.4
ESCENAS = []          # (inicio, fin, render, transición hacia la siguiente)


def armar():
    t = 0.0

    def agregar(render, dur, tr):
        nonlocal t
        ESCENAS.append((t, t + dur, render, tr))
        t += dur - TR

    agregar(intro, 2.6, tr_iris)
    trans = [tr_barrido, tr_flash, tr_diagonal, tr_zoom, lambda a, b, p: tr_barrido(a, b, p, True), tr_iris, tr_flash]
    for i in range(len(PRODUCTOS)):
        dur = 2.3 if isinstance(PRODUCTOS[i][0], tuple) else 1.9
        agregar(escena_producto(i), dur, trans[i])
    agregar(montaje, 1.8, tr_zoom)
    agregar(escena_entrega, 2.8, lambda a, b, p: tr_flash(a, b, p, 0.7))
    agregar(outro, 3.0, None)


armar()
DURACION = ESCENAS[-1][1]
FIN_PRODUCTOS = ESCENAS[len(PRODUCTOS)][1]


@lru_cache(None)
def marca_superior():
    a = texto("ALMA DE MUJER", SERIF, 50, "oro", 650, 12, False)
    b = texto("LENCERÍA", SANS, 20, ROSA_OSC, 600, 10, False)
    return halo(a), halo(b)


@lru_cache(None)
def vineta():
    yy, xx = np.mgrid[:H, :W].astype(np.float32)
    d = np.hypot((xx - W / 2) / W, (yy - H / 2) / H)
    return (1 - 0.16 * np.clip((d - 0.3) / 0.45, 0, 1) ** 2)[..., None]


LEAKS = [(0.0, 1.8, (255, 214, 190)), (5.0, 1.6, (255, 226, 200)), (9.4, 1.6, (255, 205, 196)),
         (14.0, 1.4, (255, 224, 196)), (16.6, 1.8, (255, 216, 200))]


def cuadro(t):
    act = [e for e in ESCENAS if e[0] <= t < e[1]] or [ESCENAS[-1]]
    if len(act) == 1:
        e = act[0]
        f = e[2](t - e[0], e[1] - e[0])
    else:
        a, b = act[0], act[1]
        fa = a[2](t - a[0], a[1] - a[0])
        fb = b[2](t - b[0], b[1] - b[0])
        f = a[3](fa, fb, (t - b[0]) / TR)
    # marca arriba durante los productos
    k = prog(t, ESCENAS[1][0] + 0.2, 0.5) * (1 - prog(t, FIN_PRODUCTOS - 0.5, 0.3))
    if k > 0:
        a, b = marca_superior()
        poner(f, a, W / 2, 128, k)
        poner(f, b, W / 2, 182, k)
    for t0, d, col in LEAKS:
        p = prog(t, t0, d)
        if 0 < p < 1:
            luz(f, mancha(1500, col), -300 + 1700 * p, 200 + 900 * p, 0.55 * math.sin(math.pi * p))
    f *= vineta()
    return np.clip(f, 0, 255).astype(np.uint8)


def render_n(n):
    return cuadro(n / FPS).tobytes()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", nargs="*", type=float, help="segundos a exportar como PNG")
    args = ap.parse_args()
    Path("videos_salida").mkdir(exist_ok=True)
    if args.frames:
        for s in args.frames:
            Image.fromarray(cuadro(s)).save(f"videos_salida/alma_{s:05.2f}.png")
        return
    n = int(round(DURACION * FPS))
    print(f"Duración {DURACION:.1f} s, {n} cuadros")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264",
                           "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                           SALIDA], stdin=subprocess.PIPE)
    with Pool() as pool:
        for i, b in enumerate(pool.imap(render_n, range(n), chunksize=4)):
            ff.stdin.write(b)
            if i % 60 == 0:
                print(f"  {i}/{n}")
    ff.stdin.close()
    ff.wait()
    print("Listo:", SALIDA)


if __name__ == "__main__":
    main()
