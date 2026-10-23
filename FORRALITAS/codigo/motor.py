"""Motor de motion graphics de FORRALITAS (numpy + OpenCV + Pillow): cámara virtual, parallax, tarjetas con
sombra, tipografía cinética, subtítulos por palabra, transiciones con motion blur, partículas y corrección de color.
Todo se dibuja cuadro a cuadro en 1080 x 1920 (9:16)."""
import sys
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from efectos import (W, H, blit, clamp01, ease_in_out, ease_out_back, ease_out_cubic, icono,  # noqa: E402
                     logo_redondo, prog)

PREP = RAIZ / "FORRALITAS/fotos_preparadas"
FPS = 30
VERDE = (11, 77, 35)            # verde del logo
VERDE_OSC = (4, 38, 18)
VERDE_MED = (22, 112, 52)
ORO = (236, 178, 38)            # dorado (trigo)
ORO_CLARO = (255, 214, 92)
CREMA = (250, 244, 228)
TINTA = (24, 34, 24)
BLANCO = (255, 255, 255)
F = "/usr/share/fonts/opentype/inter/"
NEGRA, EXTRA, SEMI = F + "InterDisplay-Black.otf", F + "InterDisplay-ExtraBold.otf", F + "InterDisplay-SemiBold.otf"
SERIF = "/usr/share/fonts/truetype/crosextra/Caladea-Bold.ttf"
SERIF_IT = "/usr/share/fonts/truetype/crosextra/Caladea-BoldItalic.ttf"


PADT = 40


def ease_out_expo(x):
    x = clamp01(x)
    return 1.0 if x >= 1 else 1 - 2 ** (-10 * x)


def ease_in_out_pow(x, p=3.0):
    x = clamp01(x)
    return 0.5 * (2 * x) ** p if x < 0.5 else 1 - 0.5 * (2 * (1 - x)) ** p


def rampa(p, v0=0.45, v1=2.4):
    """Speed ramp: arranca lento y acelera (v0 → v1) manteniendo p∈[0,1]."""
    p = clamp01(p)
    a = (v1 - v0) / 2.0
    k = v0 * p + a * p * p
    return clamp01(k / (v0 + a))


# ------------------------------------------------------------------ fotos y cámara virtual
class Foto:
    """Foto preparada con cámara virtual (zoom, paneo, giro) y pirámide para reducir sin aliasing."""
    _cache = {}

    def __new__(cls, nombre):
        if nombre not in cls._cache:
            o = super().__new__(cls)
            im = cv2.cvtColor(cv2.imread(str(PREP / f"{nombre}.jpg")), cv2.COLOR_BGR2RGB)
            o.niv = [im]
            while min(o.niv[-1].shape[:2]) > 700:
                o.niv.append(cv2.pyrDown(o.niv[-1]))
            o.h, o.w = im.shape[:2]
            cls._cache[nombre] = o
        return cls._cache[nombre]

    def ventana(self, w, h, cx=0.5, cy=0.5, zoom=1.0, rot=0.0):
        s0 = max(w / self.w, h / self.h) * zoom           # px de ventana por px de foto
        k = 0
        while k + 1 < len(self.niv) and s0 * 2 ** (k + 1) <= 1.5:
            k += 1
        im = self.niv[k]
        s = s0 * 2 ** k
        hh, hw = h / (2 * s), w / (2 * s)
        ih, iw = im.shape[:2]
        cx_, cy_ = np.clip(cx * iw, hw, max(iw - hw, hw)), np.clip(cy * ih, hh, max(ih - hh, hh))
        th = np.radians(rot)
        c, sn = np.cos(th) / s, np.sin(th) / s
        M = np.array([[c, -sn, 0], [sn, c, 0]], np.float32)
        M[:, 2] = np.array([cx_, cy_]) - M[:, :2] @ np.array([w / 2, h / 2])
        return cv2.warpAffine(im, M, (w, h), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REFLECT)


def camara(p, z0, z1, a, b, ease=ease_in_out):
    e = ease(p)
    return a[0] + (b[0] - a[0]) * e, a[1] + (b[1] - a[1]) * e, z0 + (z1 - z0) * e


# ------------------------------------------------------------------ composición
def comp(f, rgba, x0, y0, alpha=1.0):
    """Compone un sprite RGBA uint8 premultiplicado en el frame (recorta en los bordes)."""
    h, w = rgba.shape[:2]
    X0, Y0, X1, Y1 = max(x0, 0), max(y0, 0), min(x0 + w, W), min(y0 + h, H)
    if X0 >= X1 or Y0 >= Y1 or alpha <= 0.003:
        return
    s = rgba[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0].astype(np.float32)
    a = s[..., 3:4] * (alpha / 255.0)
    roi = f[Y0:Y1, X0:X1]
    roi[:] = np.clip(s[..., :3] * alpha + roi * (1 - a), 0, 255).astype(np.uint8)


def transformar(rgba, cx, cy, esc=1.0, rot=0.0):
    h, w = rgba.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), rot, esc)
    cs, sn = abs(M[0, 0]), abs(M[0, 1])
    bw, bh = int(h * sn + w * cs) + 2, int(h * cs + w * sn) + 2
    M[0, 2] += bw / 2 - w / 2
    M[1, 2] += bh / 2 - h / 2
    out = cv2.warpAffine(rgba, M, (bw, bh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    return out, int(cx - bw / 2), int(cy - bh / 2)


@lru_cache(maxsize=64)
def mascara_redonda(w, h, r):
    ss = 3
    m = Image.new("L", (w * ss, h * ss), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w * ss - 1, h * ss - 1), r * ss, fill=255)
    return np.asarray(m.resize((w, h), Image.LANCZOS))


@lru_cache(maxsize=64)
def sombra_rgba(w, h, r, pad=60, op=0.55, sigma=24):
    m = np.zeros((h + 2 * pad, w + 2 * pad), np.float32)
    m[pad:pad + h, pad:pad + w] = mascara_redonda(w, h, r) / 255.0
    m = cv2.GaussianBlur(m, (0, 0), sigma) * op
    out = np.zeros((m.shape[0], m.shape[1], 4), np.uint8)
    out[..., 3] = (m * 255).astype(np.uint8)
    return out


def tarjeta_rgba(img, r=48, borde=0, color_borde=CREMA):
    h, w = img.shape[:2]
    m = mascara_redonda(w, h, r)
    out = np.dstack([(img.astype(np.float32) * m[..., None] / 255).astype(np.uint8), m])
    if borde:
        b = mascara_redonda(w + 2 * borde, h + 2 * borde, r + borde)
        base = np.zeros((h + 2 * borde, w + 2 * borde, 4), np.uint8)
        for i in range(3):
            base[..., i] = (float(color_borde[i]) * b / 255).astype(np.uint8)
        base[..., 3] = b
        s = out
        a = s[..., 3:4].astype(np.float32) / 255
        roi = base[borde:borde + h, borde:borde + w].astype(np.float32)
        base[borde:borde + h, borde:borde + w] = np.clip(s.astype(np.float32) + roi * (1 - a), 0, 255).astype(np.uint8)
        return base
    return out


def poner_tarjeta(f, img, cx, cy, esc=1.0, rot=0.0, alpha=1.0, r=48, borde=10, sombra=True):
    t = tarjeta_rgba(img, r, borde)
    h, w = img.shape[:2]
    if sombra:
        sh = sombra_rgba(w + 2 * borde, h + 2 * borde, r + borde)
        s2, x, y = transformar(sh, cx + 6 * esc, cy + 26 * esc, esc, rot)
        comp(f, s2, x, y, alpha * 0.9)
    t2, x, y = transformar(t, cx, cy, esc, rot)
    comp(f, t2, x, y, alpha)


# ------------------------------------------------------------------ texto
@lru_cache(maxsize=512)
def spr_texto(txt, tam, color=BLANCO, ruta=NEGRA, trazo=0, color_trazo=VERDE_OSC, sombra=True):
    """Sprite float32 premultiplicado (RGB 0-255, alfa 0-1) con trazo y sombra suave opcionales."""
    fnt = ImageFont.truetype(ruta, tam)
    pad = PADT
    w = int(fnt.getlength(txt)) + 2 * pad
    h = int(tam * 1.35) + 2 * pad
    base = Image.new("L", (w, h), 0)
    ImageDraw.Draw(base).text((pad, pad), txt, font=fnt, fill=255)
    cuerpo = np.asarray(base, np.float32) / 255
    P = np.zeros((h, w, 3), np.float32)
    A = np.zeros((h, w), np.float32)

    def encima(col, a):
        nonlocal P, A
        P = np.array(col, np.float32) * a[..., None] + P * (1 - a[..., None])
        A = a + A * (1 - a)
    sil = cuerpo
    if trazo:
        t2 = Image.new("L", (w, h), 0)
        ImageDraw.Draw(t2).text((pad, pad), txt, font=fnt, fill=255, stroke_width=trazo, stroke_fill=255)
        sil = np.asarray(t2, np.float32) / 255
    if sombra:
        sh = np.roll(cv2.GaussianBlur(sil, (0, 0), 8) * 0.55, 9, axis=0)
        encima((0, 0, 0), sh)
    if trazo:
        encima(color_trazo, sil)
    encima(color, cuerpo)
    return np.dstack([P, A])


def ancho(txt, tam, ruta=NEGRA):
    return ImageFont.truetype(ruta, tam).getlength(txt)




class Cinetico:
    """Texto palabra por palabra con rebote. Palabras entre * se resaltan con un marcador dorado que se pinta."""

    def __init__(self, marcado, tam, max_w=940, ruta=NEGRA, color=BLANCO, color_res=VERDE_OSC, marcador=ORO,
                 trazo=0, color_trazo=VERDE_OSC, interlinea=1.12, sombra=True, alinea="c"):
        pal = [(p.strip("*"), p.startswith("*")) for p in marcado.split()]
        while True:
            gap = tam * 0.26
            lineas, cur, wcur = [], [], 0.0
            for p, d in pal:
                wp = ancho(p, tam, ruta)
                if cur and wcur + gap + wp > max_w:
                    lineas.append(cur)
                    cur, wcur = [], 0.0
                cur.append((p, d, wp))
                wcur += wp + (gap if len(cur) > 1 else 0)
            lineas.append(cur)
            if max(sum(x[2] for x in ln) + gap * (len(ln) - 1) for ln in lineas) <= max_w or tam <= 34:
                break
            tam -= 4
        self.tam, self.items, self.alto = tam, [], len(lineas) * tam * interlinea
        for li, ln in enumerate(lineas):
            tot = sum(x[2] for x in ln) + gap * (len(ln) - 1)
            x = (W - tot) / 2 if alinea == "c" else 60
            for p, d, wp in ln:
                spr = spr_texto(p, tam, color_res if d else color, ruta, trazo if not d else 0, color_trazo, sombra)
                mk = None
                if d:
                    mk = np.zeros((int(tam * 1.12), int(wp + 34), 4), np.float32)
                    cv2.rectangle(mk, (0, 0), (mk.shape[1] - 1, mk.shape[0] - 1), (*marcador, 1), -1)
                    m = mascara_redonda(mk.shape[1], mk.shape[0], 16) / 255.0
                    mk = np.dstack([np.array(marcador, np.float32) * m[..., None], m])
                self.items.append((spr, mk, x, li * tam * interlinea, wp))
                x += wp + gap

    def draw(self, f, y, t, t0, paso=0.1, desde="abajo"):
        for i, (spr, mk, x, dy, wp) in enumerate(self.items):
            if mk is not None:
                q = ease_out_expo(prog(t, t0 + 0.22 + paso * i, 0.42))
                blit(f, mk, x - 17, y + dy + self.tam * 0.04, wipe=q)
            q = prog(t, t0 + paso * i, 0.45)
            e = ease_out_cubic(q)
            off = {"abajo": (0, 70), "izq": (-120, 0), "der": (120, 0), "arriba": (0, -70)}[desde]
            blit(f, spr, x + wp / 2 + (1 - e) * off[0], y + dy + self.tam * 0.62 + (1 - e) * off[1], alpha=clamp01(q * 2.4),
                 escala=0.8 + 0.2 * ease_out_back(q, 1.5), centro=True)


class Letras:
    """Título grande letra por letra (cae, escala y se asienta) con barrido de luz opcional."""

    def __init__(self, txt, tam, ruta=NEGRA, color=BLANCO, trazo=0, color_trazo=VERDE_OSC, esp=0, sombra=True):
        self.txt, self.tam = txt, tam
        self.sp = [spr_texto(c, tam, color, ruta, trazo, color_trazo, sombra) for c in txt]
        self.ws = [ancho(c, tam, ruta) + esp for c in txt]
        self.total = sum(self.ws)

    def draw(self, f, cx, cy, t, t0, paso=0.06, caida=140, escala0=1.6):
        x = cx - self.total / 2
        for sp, w in zip(self.sp, self.ws):
            q = prog(t, t0, 0.42)
            e = ease_out_back(q, 1.7)
            blit(f, sp, x + w / 2, cy - (1 - ease_out_cubic(q)) * caida,
                 alpha=clamp01(q * 2.5), escala=escala0 - (escala0 - 1) * e, centro=True)
            x += w
            t0 += paso


def barrido_luz(f, p, ancho_b=260, angulo=-18, intensidad=0.55, caja_=None):
    """Banda de luz diagonal que cruza el frame (p: 0 → 1); dentro de `caja_` se desvanece en los bordes."""
    if p <= 0 or p >= 1:
        return
    x0, y0, x1, y1 = caja_ or (0, 0, W, H)
    x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, W), min(y1, H)
    cx = x0 + (x1 - x0 + 2 * ancho_b) * p - ancho_b
    ys = np.arange(y0, y1, dtype=np.float32)[:, None]
    xs = np.arange(x0, x1, dtype=np.float32)[None, :]
    d = (xs - cx) + (ys - (y0 + y1) / 2) * np.tan(np.radians(angulo))
    mk = np.exp(-(d / (ancho_b / 2.2)) ** 2) * intensidad
    if caja_:
        fe = 70.0
        mk = mk * np.clip(np.minimum(xs - x0, x1 - 1 - xs) / fe, 0, 1) * np.clip(np.minimum(ys - y0, y1 - 1 - ys) / fe, 0, 1)
    roi = f[y0:y1, x0:x1].astype(np.float32)
    f[y0:y1, x0:x1] = np.clip(roi + (255 - roi) * mk[..., None], 0, 255).astype(np.uint8)


# ------------------------------------------------------------------ subtítulos por palabra
class Subtitulos:
    """Subtítulos dinámicos: frases cortas que aparecen con rebote y resaltan la palabra que se dice."""

    def __init__(self, palabras, y=1425, tam=66, color=BLANCO, activo=ORO_CLARO, trazo=7, color_trazo=VERDE_OSC):
        # palabras: [(texto, t_inicio, t_fin)] en tiempo global
        self.y, self.tam = y, tam
        self.grupos = []
        cur = []
        for w in palabras:
            cur.append(w)
            fin = w[0][-1] in ".!?,;:" or len(cur) >= 4 or sum(len(x[0]) for x in cur) > 20
            if fin:
                self.grupos.append(cur)
                cur = []
        if cur:
            self.grupos.append(cur)
        self.spr = {}
        for g in self.grupos:
            for pal, _, _ in g:
                for c, col in ((0, color), (1, activo)):
                    self.spr[(pal, c)] = spr_texto(pal.upper(), tam, col, NEGRA, trazo, color_trazo, True)

    def draw(self, f, t):
        for gi, g in enumerate(self.grupos):
            t0, t1 = g[0][1], g[-1][2]
            nxt = self.grupos[gi + 1][0][1] if gi + 1 < len(self.grupos) else t1 + 0.3
            if not (t0 - 0.02 <= t < min(nxt, t1 + 0.3)):
                continue
            gap = self.tam * 0.24 + 14
            ws = [ancho(p.upper(), self.tam, NEGRA) for p, _, _ in g]
            tot = sum(ws) + gap * (len(g) - 1)
            esc = 1.0
            if tot > 960:
                esc = 960 / tot
                tot = 960
            q = prog(t, t0, 0.14)
            x = (W - tot) / 2
            for (p, a, b), w in zip(g, ws):
                activa = a <= t < b + 0.04
                sp = self.spr[(p, 1 if activa else 0)]
                pulso = 1.06 if activa else 1.0
                blit(f, sp, x + w * esc / 2, self.y + (1 - ease_out_cubic(q)) * 26,
                     alpha=clamp01(q * 3), escala=esc * (0.88 + 0.12 * ease_out_back(q, 1.8)) * pulso, centro=True)
                x += (w + gap) * esc


# ------------------------------------------------------------------ fondos, partículas y color
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
_r = np.hypot(_xx - W / 2, _yy - H / 2) / np.hypot(W / 2, H / 2)
VIGNETA = np.clip(1 - 0.34 * _r ** 2.2, 0, 1)
_VIG3 = (VIGNETA[..., None] * 255).astype(np.uint8).repeat(3, axis=2)


def degradado(c0, c1, cx=0.5, cy=0.4, radio=0.9):
    d = np.clip(np.hypot((_xx / W - cx) * 0.62, (_yy / H - cy) * 0.5 * 1.0) / (radio * 0.5), 0, 1)[..., None]
    return (np.array(c0, np.float32) * (1 - d) + np.array(c1, np.float32) * d).astype(np.uint8)


def particulas(f, t, semilla=1, n=26, color=ORO_CLARO, tam=(3, 9), vel=(18, 60), intensidad=0.55, desenfoque=True):
    r = np.random.default_rng(semilla)
    lienzo = np.zeros((H // 4, W // 4, 3), np.uint8)
    for _ in range(n):
        x0, y0 = r.uniform(0, W), r.uniform(0, H)
        v, tm, fase, sw = r.uniform(*vel), r.uniform(*tam), r.uniform(0, 6.28), r.uniform(10, 38)
        x = x0 + sw * np.sin(t * 0.9 + fase)
        y = (y0 - v * t) % (H + 80) - 40
        br = 0.5 + 0.5 * np.sin(t * 2.2 + fase)
        col = tuple(int(c * (0.45 + 0.55 * br)) for c in color)
        cv2.circle(lienzo, (int(x / 4), int(y / 4)), max(1, int(tm / 4 * 1.0)), col, -1, cv2.LINE_AA)
    if desenfoque:
        lienzo = cv2.GaussianBlur(lienzo, (0, 0), 1.6)
    g = cv2.resize(lienzo, (W, H), interpolation=cv2.INTER_LINEAR)
    cv2.addWeighted(f, 1.0, g, intensidad * 1.6, 0, f)


def _lut(contraste, calido):
    x = np.arange(256, dtype=np.float32) / 255
    s = x + contraste * (x - 0.5) * (1 - np.abs(2 * x - 1)) * 1.4
    s = np.clip(s, 0, 1)
    lut = np.zeros((256, 1, 3), np.uint8)
    for i, g in enumerate((1.0 + calido, 1.0, 1.0 - calido)):
        lut[:, 0, i] = np.clip(s * g * 255, 0, 255).astype(np.uint8)
    return lut


GRADOS = {"cine": _lut(0.45, 0.035), "vivo": _lut(0.35, 0.05), "limpio": _lut(0.28, 0.02)}


def grade(f, nombre="cine", viñeta=True):
    f = cv2.LUT(f, GRADOS[nombre])
    if viñeta:
        f = cv2.multiply(f, _VIG3, scale=1 / 255)
    return f


# ------------------------------------------------------------------ transiciones
def _blur_mov(img, k, horizontal=True):
    k = int(k)
    if k < 3:
        return img
    return cv2.blur(img, (k, 1) if horizontal else (1, k))


def tr_whip(a, b, p, direccion="izq"):
    """Whip pan: las dos escenas se desplazan con aceleración fuerte y desenfoque de movimiento."""
    e = ease_in_out_pow(p, 3.2)
    vel = abs(ease_in_out_pow(min(p + 0.01, 1), 3.2) - ease_in_out_pow(max(p - 0.01, 0), 3.2)) / 0.02
    k = 1 + vel * 70
    if direccion == "izq":                      # la nueva entra por la derecha
        c, x0 = np.concatenate([a, b], 1), int(e * W)
        return _blur_mov(np.ascontiguousarray(c[:, x0:x0 + W]), k, True)
    if direccion == "der":                      # la nueva entra por la izquierda
        c, x0 = np.concatenate([b, a], 1), W - int(e * W)
        return _blur_mov(np.ascontiguousarray(c[:, x0:x0 + W]), k, True)
    if direccion == "arriba":                   # la nueva sube desde abajo
        c, y0 = np.concatenate([a, b], 0), int(e * H)
        return _blur_mov(np.ascontiguousarray(c[y0:y0 + H]), k, False)
    c, y0 = np.concatenate([b, a], 0), H - int(e * H)     # la nueva baja desde arriba
    return _blur_mov(np.ascontiguousarray(c[y0:y0 + H]), k, False)


def tr_zoom(a, b, p):
    """Zoom-through: la escena saliente se agranda y se desenfoca, la entrante llega desde cerca."""
    e = ease_in_out_pow(p, 2.6)
    if p < 0.5:
        s = 1 + 0.9 * (e * 2) ** 1.5
        img = cv2.resize(a, None, fx=s, fy=s, interpolation=cv2.INTER_LINEAR)
        y0, x0 = (img.shape[0] - H) // 2, (img.shape[1] - W) // 2
        img = img[y0:y0 + H, x0:x0 + W]
        k = int(3 + 40 * (p * 2) ** 2)
        img = cv2.GaussianBlur(img, (k | 1, k | 1), 0)
        fl = (p * 2) ** 3 * 0.55
    else:
        s = 1 + 0.5 * (1 - (e - 0.5) * 2) ** 1.5
        img = cv2.resize(b, None, fx=s, fy=s, interpolation=cv2.INTER_LINEAR)
        y0, x0 = (img.shape[0] - H) // 2, (img.shape[1] - W) // 2
        img = img[y0:y0 + H, x0:x0 + W]
        k = int(3 + 36 * (1 - (p - 0.5) * 2) ** 2)
        img = cv2.GaussianBlur(img, (k | 1, k | 1), 0)
        fl = (1 - (p - 0.5) * 2) ** 3 * 0.55
    return cv2.addWeighted(img, 1 - fl, np.full_like(img, 255), fl, 0)


def tr_circulo(a, b, p, cx=W / 2, cy=H / 2, color=ORO):
    """Revelado con círculo creciente y aro dorado."""
    e = ease_in_out_pow(p, 2.2)
    rmax = np.hypot(max(cx, W - cx), max(cy, H - cy)) + 20
    r = int(e * rmax)
    m = np.zeros((H, W), np.uint8)
    cv2.circle(m, (int(cx), int(cy)), r, 255, -1, cv2.LINE_AA)
    out = np.where(m[..., None] > 127, b, a)
    if 0 < r < rmax:
        cv2.circle(out, (int(cx), int(cy)), r, color, 14, cv2.LINE_AA)
        cv2.circle(out, (int(cx), int(cy)), r + 16, ORO_CLARO, 3, cv2.LINE_AA)
    return out


def tr_flash(a, b, p):
    e = abs(p - 0.5) * 2
    img = a if p < 0.5 else b
    fl = (1 - e) ** 2.2
    img = cv2.addWeighted(img, 1 - fl, np.full_like(img, 255), fl, 0)
    return img


def tr_diagonal(a, b, p, color=ORO, color2=VERDE_OSC):
    """Dos franjas de color cruzan en diagonal y dejan ver la escena siguiente."""
    e = ease_in_out_pow(p, 2.4)
    d = (_xx * 0.5 + _yy * 0.866) / (W * 0.5 + H * 0.866)
    borde = e * 1.35 - 0.2
    m = (d < borde - 0.08).astype(np.uint8)
    banda1 = (d >= borde - 0.08) & (d < borde)
    banda2 = (d >= borde) & (d < borde + 0.07)
    out = np.where(m[..., None] > 0, b, a)
    out[banda1] = color
    out[banda2] = color2
    return out


def tr_persianas(a, b, p, n=9):
    """Tiras verticales que giran en cadena para revelar la siguiente escena."""
    out = a.copy()
    ancho_t = W / n
    for i in range(n):
        q = clamp01(p * 1.7 - i * 0.075)
        e = ease_in_out(q)
        x0, x1 = int(i * ancho_t), int((i + 1) * ancho_t)
        sh = int(e * H)
        if sh <= 0:
            continue
        franja = np.concatenate([a[:, x0:x1], b[:, x0:x1]], 0)
        out[:, x0:x1] = franja[sh:sh + H]
    return out


# ------------------------------------------------------------------ línea de tiempo
class Linea:
    """Escenas con duración en segundos; las transiciones superponen TR segundos centrados en cada corte."""

    def __init__(self, escenas, transiciones, tr=0.42):
        # escenas: [(dur, fn(t))], transiciones: [fn(a, b, p)] (len = n-1)
        self.esc, self.trs, self.tr = escenas, transiciones, tr
        self.ini, t = [], 0.0
        for d, _ in escenas:
            self.ini.append(t)
            t += d
        self.total = t

    def frame(self, t):
        t = min(max(t, 0), self.total - 1e-3)
        n = len(self.esc)
        for i in range(n - 1):
            corte = self.ini[i + 1]
            if corte - self.tr / 2 <= t < corte + self.tr / 2:
                p = (t - (corte - self.tr / 2)) / self.tr
                a = self.esc[i][1](t - self.ini[i])
                b = self.esc[i + 1][1](max(t - self.ini[i + 1], 0.0))
                return self.trs[i](a, b, p)
        for i in range(n):
            if self.ini[i] <= t < self.ini[i] + self.esc[i][0] or i == n - 1:
                return self.esc[i][1](t - self.ini[i])


# ------------------------------------------------------------------ datos comerciales verificados (crear_video.CONFIG)
def datos():
    import crear_video as cv
    c = cv.CONFIG
    return {
        "tel": list(c["telefonos"]),                          # ('381 526 9004', '381 633 4344')
        "horario": ["Lunes a viernes 8:00 a 19:00", "Sábados 8:30 a 19:00"],
        "lugar": ["Ruta 305 km 7,5", "Las Talitas, Tucumán"],
        "servicios": list(c["servicios"]),
        "pagos": list(c["pagos"]),
    }
