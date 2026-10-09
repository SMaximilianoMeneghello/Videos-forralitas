"""Herramientas de animación: easing, sprites de texto, cámara y transiciones."""
from functools import lru_cache

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
VERDE = (11, 77, 35)
VERDE_OSCURO = (5, 40, 17)
AMARILLO = (255, 213, 64)
BLANCO = (255, 255, 255)
FUENTE = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


# ---------------------------------------------------------------- easing
def clamp01(x):
    return min(1.0, max(0.0, x))


def prog(t, inicio, dur):
    return clamp01((t - inicio) / dur)


def ease_out_cubic(x):
    x = clamp01(x)
    return 1 - (1 - x) ** 3


def ease_in_out(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def ease_out_back(x, s=1.9):
    x = clamp01(x)
    return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


# ---------------------------------------------------------------- sprites
# Un sprite es un array float32 (h, w, 4) con RGB premultiplicado por alfa.
@lru_cache(maxsize=None)
def _fuente(tam):
    return ImageFont.truetype(FUENTE, tam)


def ancho_texto(txt, tam):
    return _fuente(tam).getlength(txt)


def texto(txt, tam, color=BLANCO, sombra=True):
    f = _fuente(tam)
    pad = 26
    w = int(f.getlength(txt)) + 2 * pad
    h = int(tam * 1.32) + 2 * pad
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).text((pad, pad), txt, font=f, fill=255)
    mask = np.asarray(m, np.float32) / 255
    rgb = np.empty((h, w, 3), np.float32)
    rgb[:] = color
    alfa = mask.copy()
    if sombra:
        sh = cv2.GaussianBlur(mask, (0, 0), 7) * 0.7
        sh = np.roll(sh, 7, axis=0)
        alfa = mask + sh * (1 - mask)
    return np.dstack([rgb * mask[..., None], alfa])


def caja(w, h, radio, color, alpha=1.0):
    ss = 3
    m = Image.new("L", (w * ss, h * ss), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w * ss - 1, h * ss - 1), radio * ss, fill=255)
    m = np.asarray(m.resize((w, h), Image.LANCZOS), np.float32) / 255 * alpha
    rgb = np.empty((h, w, 3), np.float32)
    rgb[:] = color
    return np.dstack([rgb * m[..., None], m])


def sobre(base, spr, x, y):
    """Compone el sprite `spr` sobre el sprite `base` (ambos premultiplicados)."""
    out = base.copy()
    H0, W0 = out.shape[:2]
    x0, y0 = max(x, 0), max(y, 0)
    x1, y1 = min(x + spr.shape[1], W0), min(y + spr.shape[0], H0)
    if x0 >= x1 or y0 >= y1:
        return out
    s = spr[y0 - y:y1 - y, x0 - x:x1 - x]
    reg = out[y0:y1, x0:x1]
    reg[:] = s + reg * (1 - s[:, :, 3:4])
    return out


def desde_pil(im):
    a = np.asarray(im.convert("RGBA"), np.float32) / 255
    a[:, :, :3] *= a[:, :, 3:4]
    a[:, :, :3] *= 255
    return a


def blit(frame, spr, x, y, alpha=1.0, escala=1.0, centro=False, wipe=1.0):
    """Dibuja un sprite sobre un frame uint8. `wipe` revela de izquierda a derecha."""
    if alpha <= 0.003 or escala <= 0.01 or wipe <= 0.001:
        return
    if escala != 1.0:
        h, w = spr.shape[:2]
        spr = cv2.resize(spr, (max(1, int(w * escala)), max(1, int(h * escala))),
                         interpolation=cv2.INTER_LINEAR)
    h, w = spr.shape[:2]
    if wipe < 1.0:
        w = max(1, int(w * wipe))
        spr = spr[:, :w]
    if centro:
        x -= spr.shape[1] / 2 if wipe >= 1.0 else w / 2
        y -= h / 2
    x, y = int(round(x)), int(round(y))
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if x0 >= x1 or y0 >= y1:
        return
    s = spr[y0 - y:y1 - y, x0 - x:x1 - x]
    a = s[:, :, 3:4] * alpha
    reg = frame[y0:y1, x0:x1].astype(np.float32)
    frame[y0:y1, x0:x1] = np.clip(s[:, :, :3] * alpha + reg * (1 - a), 0, 255).astype(np.uint8)


# ---------------------------------------------------------------- iconos
def icono(nombre, lado=110, fondo=AMARILLO, tinta=VERDE_OSCURO):
    ss = 4
    L = lado * ss
    im = Image.new("RGBA", (L, L), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((0, 0, L - 1, L - 1), fill=fondo + (255,))
    u = L / 100
    k = tinta + (255,)
    if nombre == "telefono":
        d.rounded_rectangle((33 * u, 18 * u, 67 * u, 82 * u), 7 * u, outline=k, width=int(5 * u))
        d.line((44 * u, 27 * u, 56 * u, 27 * u), fill=k, width=int(3.5 * u))
        d.ellipse((46 * u, 69 * u, 54 * u, 77 * u), fill=k)
    elif nombre == "ubicacion":
        d.polygon([(50 * u, 84 * u), (27 * u, 47 * u), (73 * u, 47 * u)], fill=k)
        d.ellipse((27 * u, 18 * u, 73 * u, 64 * u), fill=k)
        d.ellipse((41 * u, 32 * u, 59 * u, 50 * u), fill=fondo + (255,))
    elif nombre == "reloj":
        d.ellipse((22 * u, 22 * u, 78 * u, 78 * u), outline=k, width=int(6 * u))
        d.line((50 * u, 50 * u, 50 * u, 33 * u), fill=k, width=int(6 * u))
        d.line((50 * u, 50 * u, 63 * u, 58 * u), fill=k, width=int(6 * u))
    elif nombre == "camion":
        d.rectangle((15 * u, 33 * u, 56 * u, 66 * u), fill=k)
        d.polygon([(58 * u, 43 * u), (74 * u, 43 * u), (86 * u, 55 * u), (86 * u, 66 * u), (58 * u, 66 * u)], fill=k)
        for cx in (31, 72):
            d.ellipse(((cx - 8) * u, 59 * u, (cx + 8) * u, 75 * u), fill=k, outline=fondo + (255,), width=int(3 * u))
    elif nombre == "efectivo":
        d.rounded_rectangle((13 * u, 29 * u, 87 * u, 71 * u), 6 * u, outline=k, width=int(5 * u))
        d.ellipse((38 * u, 38 * u, 62 * u, 62 * u), outline=k, width=int(5 * u))
        for cx, cy in ((24, 40), (76, 60)):
            d.ellipse(((cx - 3) * u, (cy - 3) * u, (cx + 3) * u, (cy + 3) * u), fill=k)
    elif nombre == "transferencia":
        d.line((22 * u, 38 * u, 70 * u, 38 * u), fill=k, width=int(6 * u))
        d.polygon([(68 * u, 24 * u), (88 * u, 38 * u), (68 * u, 52 * u)], fill=k)
        d.line((30 * u, 64 * u, 78 * u, 64 * u), fill=k, width=int(6 * u))
        d.polygon([(32 * u, 50 * u), (12 * u, 64 * u), (32 * u, 78 * u)], fill=k)
    elif nombre == "debito":
        d.rounded_rectangle((13 * u, 27 * u, 87 * u, 73 * u), 7 * u, fill=k)
        d.rectangle((13 * u, 38 * u, 87 * u, 49 * u), fill=fondo + (255,))
        d.rectangle((22 * u, 59 * u, 42 * u, 65 * u), fill=fondo + (255,))
    elif nombre == "credito":
        d.rounded_rectangle((13 * u, 27 * u, 87 * u, 73 * u), 7 * u, outline=k, width=int(5 * u))
        d.rounded_rectangle((23 * u, 37 * u, 41 * u, 52 * u), 3 * u, fill=k)
        for x in (24, 40, 56, 72):
            d.ellipse(((x - 2.5) * u, 60 * u, (x + 2.5) * u, 65 * u), fill=k)
    elif nombre == "tienda":
        d.polygon([(18 * u, 42 * u), (24 * u, 24 * u), (76 * u, 24 * u), (82 * u, 42 * u)], fill=k)
        d.rectangle((24 * u, 44 * u, 76 * u, 76 * u), fill=k)
        d.rectangle((43 * u, 56 * u, 57 * u, 76 * u), fill=fondo + (255,))
    im = im.resize((lado, lado), Image.LANCZOS)
    return desde_pil(im)


def logo_redondo(lado, ruta="assets/logo.jpg"):
    im = Image.open(ruta).convert("RGB")
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).ellipse((55, 55, im.width - 55, im.height - 55), fill=255)
    im.putalpha(m)
    im = im.crop((55, 55, im.width - 55, im.height - 55)).resize((lado, lado), Image.LANCZOS)
    return desde_pil(im)


def rotar_sprite(spr, grados):
    h, w = spr.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), grados, 1.0)
    return cv2.warpAffine(spr, M, (w, h), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))


# ---------------------------------------------------------------- fondos
def _degrade(a, b):
    t = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    col = np.array(a, np.float32) * (1 - t) + np.array(b, np.float32) * t
    return np.repeat(col, W, axis=1)


FONDO_VERDE = _degrade((16, 96, 46), VERDE_OSCURO)
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
DIST_CENTRO = np.hypot(_xx - W / 2, _yy - H / 2)
DIST_MAX = float(np.hypot(W / 2, H / 2))
BRILLO = np.clip(1 - DIST_CENTRO / (DIST_MAX * 0.75), 0, 1)[..., None] ** 1.5
DIAGONAL = (_xx * 0.5 + _yy * 0.866)


def fondo_animado(t, semilla=3, n=34):
    """Fondo verde con resplandor que respira y partículas flotando."""
    pulso = 0.55 + 0.45 * np.sin(t * 2.2)
    f = FONDO_VERDE + BRILLO * np.array((20, 70, 28), np.float32) * pulso
    f = np.clip(f, 0, 255).astype(np.uint8)
    rng = np.random.default_rng(semilla)
    xs, ys = rng.uniform(0, W, n), rng.uniform(0, H, n)
    rs, vel = rng.uniform(5, 26, n), rng.uniform(30, 110, n)
    fase = rng.uniform(0, 6.28, n)
    ov = f.copy()
    for x, y, r, v, ph in zip(xs, ys, rs, vel, fase):
        cx = x + 28 * np.sin(t * 0.9 + ph)
        cy = (y - v * t) % (H + 80) - 40
        cv2.circle(ov, (int(cx), int(cy)), int(r), (120, 210, 120), -1, cv2.LINE_AA)
    return cv2.addWeighted(ov, 0.16, f, 0.84, 0)


# ---------------------------------------------------------------- cámara
class Foto:
    """Foto con movimiento de cámara (zoom + paneo) a partir de subpíxeles."""

    def __init__(self, ruta, saturacion=1.18, contraste=1.08):
        from PIL import ImageEnhance
        im = Image.open(ruta).convert("RGB")
        s0 = max(W / im.width, H / im.height)
        pw, ph = int(round(im.width * s0)), int(round(im.height * s0))
        im = im.resize((max(pw, W), max(ph, H)), Image.LANCZOS)
        im = ImageEnhance.Color(im).enhance(saturacion)
        im = ImageEnhance.Contrast(im).enhance(contraste)
        self.img = np.asarray(im)
        self.ph, self.pw = self.img.shape[:2]

    def frame(self, p, z0, z1, a, b):
        """p en 0..1. a y b: foco inicial y final (0..1, 0..1) dentro del recorrido."""
        e = ease_in_out(p)
        z = z0 + (z1 - z0) * e
        px = a[0] + (b[0] - a[0]) * e
        py = a[1] + (b[1] - a[1]) * e
        vw, vh = W / z, H / z
        cx = vw / 2 + px * max(self.pw - vw, 0)
        cy = vh / 2 + py * max(self.ph - vh, 0)
        s = 1 / z
        M = np.array([[s, 0, cx - W / 2 * s], [0, s, cy - H / 2 * s]], np.float32)
        return cv2.warpAffine(self.img, M, (W, H),
                              flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP,
                              borderMode=cv2.BORDER_REPLICATE)


def _mapa_gradiente():
    yv = (_yy / H)[..., None]
    vig = np.clip(DIST_CENTRO / DIST_MAX, 0, 1)[..., None] ** 2.2 * 0.42
    abajo = np.clip((yv - 0.46) / 0.40, 0, 1) ** 1.2 * 0.66
    arriba = np.clip((0.2 - yv) / 0.2, 0, 1) * 0.5
    return ((1 - vig) * (1 - abajo) * (1 - arriba)).astype(np.float32)


MAPA_GRADIENTE = _mapa_gradiente()


# ---------------------------------------------------------------- transiciones
def escalar(frame, s):
    M = np.array([[s, 0, (1 - s) * W / 2], [0, s, (1 - s) * H / 2]], np.float32)
    return cv2.warpAffine(frame, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def mezclar(a, b, p):
    return cv2.addWeighted(a, 1 - p, b, p, 0)


def tr_zoom(a, b, p):
    e = ease_in_out(p)
    return mezclar(escalar(a, 1 + 0.45 * e), escalar(b, 1.35 - 0.35 * e), e)


def _blur(img, p, horizontal=True):
    k = int(1 + 90 * np.sin(np.pi * p))
    k += (k % 2 == 0)
    if k <= 1:
        return img
    return cv2.blur(img, (k, 1) if horizontal else (1, k))


def tr_empuje_izq(a, b, p):
    off = int(ease_in_out(p) * W)
    out = np.empty_like(a)
    out[:, :W - off] = a[:, off:]
    out[:, W - off:] = b[:, :off]
    return _blur(out, p, True)


def tr_empuje_der(a, b, p):
    off = int(ease_in_out(p) * W)
    out = np.empty_like(a)
    out[:, off:] = a[:, :W - off]
    out[:, :off] = b[:, W - off:]
    return _blur(out, p, True)


def tr_empuje_arriba(a, b, p):
    off = int(ease_in_out(p) * H)
    out = np.empty_like(a)
    out[:H - off] = a[off:]
    out[H - off:] = b[:off]
    return _blur(out, p, False)


def tr_iris(a, b, p):
    r = ease_in_out(p) * DIST_MAX * 1.02
    m = np.clip((r - DIST_CENTRO) / 5 + 0.5, 0, 1)[..., None]
    out = a.astype(np.float32) * (1 - m) + b.astype(np.float32) * m
    anillo = np.clip(1 - np.abs(DIST_CENTRO - r) / 14, 0, 1)[..., None] * (1 - p) ** 0.5
    out += anillo * np.array(AMARILLO, np.float32) * 0.9
    return np.clip(out, 0, 255).astype(np.uint8)


def tr_diagonal(a, b, p):
    gmax = float(DIAGONAL.max()) + 60
    u = ease_in_out(p) * gmax
    m = np.clip((u - DIAGONAL) / 5 + 0.5, 0, 1)[..., None]
    out = a.astype(np.float32) * (1 - m) + b.astype(np.float32) * m
    banda = np.clip(1 - np.abs(DIAGONAL - u) / 22, 0, 1)[..., None]
    out += banda * np.array(AMARILLO, np.float32) * 0.9
    return np.clip(out, 0, 255).astype(np.uint8)


def tr_destello(a, b, p):
    blanco = np.full_like(a, 255)
    if p < 0.5:
        return mezclar(escalar(a, 1 + 0.1 * p), blanco, ease_in_out(p * 2))
    return mezclar(blanco, escalar(b, 1.05 - 0.05 * (p - 0.5) * 2), ease_in_out((p - 0.5) * 2))
