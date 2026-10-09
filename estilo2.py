"""Estilo "campo": papel crema, tarjetas con tres diseños, transiciones de formas y música tranquila.

Uso:
    python estilo2.py                  # genera videos_salida/forralitas_campo.mp4
    python estilo2.py --frames 2 6 12  # guarda esos segundos como PNG (vista previa)

Fotos de productos en ./fotos_presentacion, fotos aéreas en assets/dron.
Datos de contacto, horarios y pagos: CONFIG en crear_video.py.
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from moviepy import AudioFileClip, VideoClip
from PIL import Image, ImageEnhance

import audio_campo
import crear_video as cv
from efectos import (H, W, ancho_texto, blit, caja, clamp01, ease_in_out, ease_out_back,
                     ease_out_cubic, icono, logo_redondo, prog, sobre, texto)

FPS = 30
TR = 0.75
SALIDA = "videos_salida/forralitas_campo.mp4"

CREMA, VERDE, VERDE_OSC = (247, 240, 224), (24, 88, 50), (11, 52, 28)
TRIGO, TIERRA, TINTA = (226, 168, 48), (128, 86, 50), (30, 48, 36)
SERIF = "/usr/share/fonts/truetype/crosextra/Caladea-Bold.ttf"
SERIF_IT = "/usr/share/fonts/truetype/crosextra/Caladea-BoldItalic.ttf"
SANS = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
SANS_SEMI = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
PAD = cv.PAD

D_A, D_B, D_PROD, D_MOS = 4.8, 4.6, 2.7, 3.8
# instantes (s, locales a cada escena) de las animaciones clave; estilo_voz.py los ajusta a la locución
TM = {"a_top": 0.5, "a_l1": 1.6, "a_l2": 2.2, "b_pin": 1.9, "b_est": 2.2, "b_ruta": 2.5, "b_tal": 3.1,
      "firma": 6.3, "prod": 0.55}
CAMARAS = [(1.00, 1.22, (0.5, 0.7), (0.5, 0.3)), (1.22, 1.02, (0.35, 0.4), (0.6, 0.6)),
           (1.05, 1.24, (0.1, 0.5), (0.9, 0.5)), (1.24, 1.04, (0.9, 0.5), (0.15, 0.5)),
           (1.00, 1.26, (0.5, 0.2), (0.5, 0.75)), (1.25, 1.00, (0.6, 0.6), (0.4, 0.3))]

PRODUCTOS = [
    ("*Alfa*", ""),
    ("Engorde de *cerdo*", "Bolsa x 30 kg y suelto"),
    ("Mezcla de *caballo*", "Bolsa x 35 kg y suelto"),
    ("Pellet de *alfa*", ""),
    ("Maíz *entero*", ""),
    ("Maíz *quebrado*", "Bolsa x 40 kg y suelto"),
    ("Pellet de *trigo*", "Bolsa x 30 kg y suelto"),
    ("Afrecho de *trigo*", ""),
    ("Afrecho de *maíz*", "Por bolsa y suelto"),
    ("Ponedora para *gallinas*", "Por bolsa y suelto"),
    ("Iniciador *parrillero*", ""),
    ("Engorde *terminador*", ""),
    ("Alimentos para *perro* y *gato*", ""),
    ("*Virutas*", ""),
]


def T(txt, tam, color=TINTA, ruta=SERIF, sombra=False):
    return texto(txt, tam, color, sombra, ruta)


# ------------------------------------------------------------ fondo de papel
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
_r = np.hypot(_xx - W / 2, _yy - H / 2) / np.hypot(W / 2, H / 2)
_grano = np.random.default_rng(5).normal(0, 1, (H, W)).astype(np.float32)
PAPEL = np.clip((np.array(CREMA, np.float32) * (1 - 0.11 * _r ** 2)[..., None]
                 + _grano[..., None] * 3.2 + (1 - _yy / H)[..., None] * 3), 0, 255).astype(np.uint8)
_rng = np.random.default_rng(21)
_PART = [(_rng.uniform(0, W), _rng.uniform(0, H), _rng.uniform(0.6, 1.5), _rng.uniform(25, 70),
          _rng.uniform(-60, 60), _rng.uniform(0, 6.28), _rng.integers(0, 3)) for _ in range(26)]
_COLOR_PART = [(214, 160, 44), (96, 140, 70), (150, 104, 62)]


def fondo_papel(gt):
    """Papel con granos de trigo y hojas flotando suavemente."""
    f = PAPEL.copy()
    ov = f.copy()
    for x, y, esc, vel, giro, fase, tipo in _PART:
        cx = x + 34 * np.sin(gt * 0.7 + fase)
        cy = (y - vel * gt) % (H + 80) - 40
        a, b = (9, 4) if tipo == 0 else (17, 7)
        cv2.ellipse(ov, (int(cx), int(cy)), (int(a * esc), int(b * esc)),
                    (gt * giro + fase * 40) % 360, 0, 360, _COLOR_PART[tipo], -1, cv2.LINE_AA)
    return cv2.addWeighted(ov, 0.34, f, 0.66, 0)


# ------------------------------------------------------------ elementos comunes
def texto_espaciado(txt, tam, color, ruta, esp):
    letras = [T(c, tam, color, ruta) for c in txt]
    ws = [ancho_texto(c, tam, ruta) for c in txt]
    total = int(sum(ws) + esp * (len(txt) - 1)) + 2 * PAD
    base = np.zeros((letras[0].shape[0], total, 4), np.float32)
    x = PAD
    for s, w in zip(letras, ws):
        base = sobre(base, s, int(x - PAD), 0)
        x += w + esp
    return base


class Titulo:
    """Título centrado; las palabras entre * llevan marcador dorado que se "pinta" de izquierda a derecha."""

    def __init__(self, marcado, tam, max_w, color=TINTA, ruta=SERIF):
        pal = [(p.strip("*"), p.startswith("*")) for p in marcado.split()]
        while True:
            gap = tam * 0.28
            anchos = [ancho_texto(p, tam, ruta) for p, _ in pal]
            total = sum(anchos) + gap * (len(pal) - 1)
            if total <= max_w or tam <= 36:
                break
            tam -= 4
        self.tam = tam
        self.sprites = [T(p, tam, VERDE_OSC if d else color, ruta) for p, d in pal]
        x, self.xs, self.marc = (W - total) / 2, [], []
        for (p, d), a in zip(pal, anchos):
            self.xs.append(x - PAD)
            self.marc.append(caja(int(a + 30), int(tam * 1.08), 16, TRIGO) if d else None)
            x += a + gap

    def draw(self, f, y, t, t0, paso=0.1):
        for i, (m, x) in enumerate(zip(self.marc, self.xs)):
            if m is not None:
                q = ease_out_cubic(prog(t, t0 + 0.28 + paso * i, 0.5))
                blit(f, m, x + PAD - 15, y + PAD + self.tam * 0.12, wipe=q)
        for i, (s, x) in enumerate(zip(self.sprites, self.xs)):
            q = prog(t, t0 + paso * i, 0.5)
            e = ease_out_cubic(q)
            blit(f, s, x, y + (1 - e) * 60, alpha=clamp01(q * 2.2), escala=0.82 + 0.18 * ease_out_back(q, 1.4))


def sprite_cabecera():
    logo = logo_redondo(92)
    n = T("FORRALITAS", 40, VERDE_OSC, SERIF)
    r = T("Forrajería y Semillería", 24, TIERRA, SANS_SEMI)
    base = np.zeros((100, 560, 4), np.float32)
    base = sobre(base, logo, 0, 4)
    base = sobre(base, n, 100 - PAD, -2)
    base = sobre(base, r, 100 - PAD, 44)
    return base


CABECERA = sprite_cabecera()
_TXT_TICKER = "RUTA 305 KM 7,5   •   LAS TALITAS   •   381 526 9004   •   381 633 4344   •   VENTA POR MAYOR Y MENOR   •   "
TICKER = T(_TXT_TICKER, 34, CREMA, SANS)
CICLO = TICKER.shape[1] - 2 * PAD


def dibujar_ticker(f, gt, q=1.0):
    y0 = 1604 + int((1 - ease_out_cubic(q)) * 90)
    reg = f[y0:y0 + 66].astype(np.float32)
    f[y0:y0 + 66] = (reg * 0.06 + np.array(VERDE_OSC, np.float32) * 0.94).astype(np.uint8)
    cv2.line(f, (0, y0), (W, y0), TRIGO, 4, cv2.LINE_AA)
    off = (gt * 95) % CICLO
    for k in range(3):
        blit(f, TICKER, k * CICLO - off - PAD, y0 - 4)


def cabecera(f, t, q0=0.1):
    q = ease_out_cubic(prog(t, q0, 0.6))
    blit(f, CABECERA, 56 - (1 - q) * 260, 96, alpha=q)


class Visor:
    """Foto con cámara (zoom + paneo) en una ventana de w x h."""

    def __init__(self, ruta, w, h, sat=1.14, con=1.07):
        im = Image.open(ruta).convert("RGB")
        s0 = max(w / im.width, h / im.height)
        im = im.resize((max(w, int(im.width * s0 + .5)), max(h, int(im.height * s0 + .5))), Image.LANCZOS)
        im = ImageEnhance.Contrast(ImageEnhance.Color(im).enhance(sat)).enhance(con)
        self.img = np.asarray(im)
        self.ph, self.pw = self.img.shape[:2]
        self.w, self.h = w, h

    def frame(self, p, z0, z1, a, b, roll=0.0):
        e = ease_in_out(p)
        z = z0 + (z1 - z0) * e
        hw, hh = self.w / (2 * z), self.h / (2 * z)
        cx = np.clip((a[0] + (b[0] - a[0]) * e) * self.pw, hw, self.pw - hw)
        cy = np.clip((a[1] + (b[1] - a[1]) * e) * self.ph, hh, self.ph - hh)
        th = np.radians(roll)
        c, s = np.cos(th) / z, np.sin(th) / z
        M = np.array([[c, -s, 0], [s, c, 0]], np.float32)
        M[:, 2] = np.array([cx, cy]) - M[:, :2] @ np.array([self.w / 2, self.h / 2])
        return cv2.warpAffine(self.img, M, (self.w, self.h), flags=cv2.INTER_CUBIC | cv2.WARP_INVERSE_MAP,
                              borderMode=cv2.BORDER_REFLECT)


def recortar(img, mascara):
    s = np.empty(img.shape[:2] + (4,), np.float32)
    s[..., :3] = img * mascara[..., None]
    s[..., 3] = mascara
    return s


def transformar(spr, esc=1.0, ang=0.0):
    if abs(esc - 1) < 1e-3 and abs(ang) < 1e-3:
        return spr
    h, w = spr.shape[:2]
    c, s = abs(np.cos(np.radians(ang))), abs(np.sin(np.radians(ang)))
    nw, nh = int((w * c + h * s) * esc) + 2, int((w * s + h * c) * esc) + 2
    M = cv2.getRotationMatrix2D((w / 2, h / 2), ang, esc)
    M[0, 2] += nw / 2 - w / 2
    M[1, 2] += nh / 2 - h / 2
    return cv2.warpAffine(spr, M, (nw, nh), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))


def sombra_de(mascara, pad=70, op=0.38, sigma=24):
    h, w = mascara.shape
    s = np.zeros((h + 2 * pad, w + 2 * pad), np.float32)
    s[pad:pad + h, pad:pad + w] = mascara
    s = cv2.GaussianBlur(s, (0, 0), sigma) * op
    return np.dstack([np.zeros_like(s)] * 3 + [s])


def mascara_redonda(w, h, r):
    return caja(w, h, r, (255, 255, 255))[:, :, 3]


def insignia(num):
    base = caja(112, 112, 56, TRIGO)
    base = sobre(base, caja(96, 96, 48, (255, 255, 255), 0.0), 8, 8)
    t = T(num, 50, VERDE_OSC, SERIF)
    return sobre(base, t, (112 - t.shape[1]) // 2, (112 - t.shape[0]) // 2)


def bloque_texto(f, titulo, pastilla, kicker, t, t0):
    """Etiqueta "TENEMOS", título con marcador y subtítulo."""
    k = ease_out_cubic(prog(t, t0, 0.5))
    if k > 0:
        ancho = kicker.shape[1] - 2 * PAD
        x0 = (W - ancho) / 2
        blit(f, kicker, x0 - PAD, 1244, alpha=k)
        L = int(150 * k)
        cv2.line(f, (int(x0 - 30), 1286), (int(x0 - 30 - L), 1286), TIERRA, 3, cv2.LINE_AA)
        cv2.line(f, (int(x0 + ancho + 30), 1286), (int(x0 + ancho + 30 + L), 1286), TIERRA, 3, cv2.LINE_AA)
    titulo.draw(f, 1290, t, t0 + 0.12)
    if pastilla is not None:
        q = prog(t, t0 + 0.12 * len(titulo.sprites) + 0.45, 0.55)
        blit(f, pastilla, (W - pastilla.shape[1]) / 2, 1478 + (1 - ease_out_cubic(q)) * 30,
             alpha=ease_out_cubic(q * 2), escala=0.9 + 0.1 * ease_out_back(q, 1.6))


# ------------------------------------------------------------ escena de producto
def escena_producto(ruta, idx, titulo_m, sub, dur, g0, variante, cam):
    z0, z1, a, b = cam
    titulo = Titulo(titulo_m, 100, W - 110)
    kicker = texto_espaciado("TENEMOS", 32, TIERRA, SANS, 9)
    pastilla = None
    if sub:
        s = T(sub, 44, CREMA, SANS_SEMI)
        pastilla = sobre(caja(s.shape[1] + 30, s.shape[0] - 10, 46, VERDE_OSC, 0.96), s, 15, -5)
    ins = insignia(f"{idx + 1:02d}")
    n_tot = len(PRODUCTOS)
    mini = T(f"{idx + 1} / {n_tot}", 26, TIERRA, SANS_SEMI)

    if variante == "tarjeta":
        pw, ph = 940, 1000
        visor = Visor(ruta, pw, ph)
        masc = mascara_redonda(pw, ph, 46)
        sombra = sombra_de(masc)
        fondo1 = transformar(caja(pw + 30, ph + 30, 54, TRIGO), 1.0, -3.2)
        fondo2 = transformar(caja(pw + 26, ph + 26, 52, (255, 252, 244)), 1.0, 1.6)
        cx, cy = W / 2, 715
    elif variante == "circulo":
        d = 880
        visor = Visor(ruta, d, d)
        masc = mascara_redonda(d, d, d // 2)
        sombra = sombra_de(masc)
        cx, cy = W / 2, 705
    else:   # diagonal
        visor = Visor(ruta, W, 1000)
        poly = np.zeros((1000, W), np.uint8)
        cv2.fillPoly(poly, [np.array([[0, 0], [W, 0], [W, 800], [0, 980]])], 255, cv2.LINE_AA)
        masc = poly.astype(np.float32) / 255
        cx, cy = W / 2, 210 + 500

    def fn(t):
        gt = g0 + t
        f = fondo_papel(gt)
        p = t / dur
        foto = visor.frame(p, z0, z1, a, b, roll=0.0)
        if variante == "tarjeta":
            for k, (capa, dl) in enumerate(((fondo1, 0.0), (fondo2, 0.1))):
                q = prog(t, dl, 0.7)
                blit(f, capa, cx, cy, alpha=clamp01(q * 3), escala=0.8 + 0.2 * ease_out_back(q, 1.5), centro=True)
            q = prog(t, 0.2, 0.8)
            e = ease_out_back(q, 1.4)
            sp = recortar(foto, masc)
            blit(f, sombra, cx, cy + 20, alpha=clamp01(q * 2), escala=0.86 + 0.14 * e, centro=True)
            blit(f, sp, cx, cy, alpha=clamp01(q * 3), escala=0.86 + 0.14 * e, centro=True)
            qi = prog(t, 0.55, 0.6)
            blit(f, transformar(ins, 1.0, -12 * (1 - ease_out_cubic(qi))), 112, 262, alpha=clamp01(qi * 3),
                 escala=max(ease_out_back(qi, 2.2), 0.01), centro=True)
        elif variante == "circulo":
            q = prog(t, 0.0, 0.85)
            e = ease_out_back(q, 1.3)
            esc = 0.5 + 0.5 * e
            r0 = 450 * esc
            rot = gt * 24
            for k in range(28):
                a0 = k * (360 / 28) + rot
                cv2.ellipse(f, (int(cx), int(cy)), (int(r0 + 24), int(r0 + 24)), 0, a0, a0 + 7, TRIGO, 7, cv2.LINE_AA)
            cv2.circle(f, (int(cx), int(cy)), int(r0 + 52), TIERRA, 2, cv2.LINE_AA)
            for k in range(3):
                a0 = -rot * 1.4 + k * 120
                cv2.ellipse(f, (int(cx), int(cy)), (int(r0 + 52), int(r0 + 52)), 0, a0, a0 + 38, VERDE, 6, cv2.LINE_AA)
            blit(f, sombra, cx, cy + 18, alpha=clamp01(q * 2), escala=esc, centro=True)
            blit(f, recortar(foto, masc), cx, cy, alpha=clamp01(q * 3), escala=esc, centro=True)
            qi = prog(t, 0.5, 0.6)
            blit(f, transformar(ins, 1.0, 14 * (1 - ease_out_cubic(qi))), W - 150, 330, alpha=clamp01(qi * 3),
                 escala=max(ease_out_back(qi, 2.2), 0.01), centro=True)
        else:
            q = prog(t, 0.0, 0.8)
            e = ease_out_cubic(q)
            sp = recortar(foto, masc)
            blit(f, sp, 0, 210 - (1 - e) * 420, alpha=clamp01(q * 3))
            ql = ease_out_cubic(prog(t, 0.35, 0.6))
            xe = W * ql
            cv2.line(f, (0, 210 + 980), (int(xe), int(210 + 980 - 180 * ql)), TRIGO, 16, cv2.LINE_AA)
            cv2.line(f, (0, 210 + 1006), (int(xe), int(210 + 1006 - 180 * ql)), VERDE_OSC, 8, cv2.LINE_AA)
            qi = prog(t, 0.55, 0.6)
            blit(f, transformar(ins, 1.0, -10 * (1 - ease_out_cubic(qi))), 140, 360, alpha=clamp01(qi * 3),
                 escala=max(ease_out_back(qi, 2.2), 0.01), centro=True)
        cabecera(f, t)
        qm = ease_out_cubic(prog(t, 0.3, 0.5))
        blit(f, mini, W - 56 - (mini.shape[1] - 2 * PAD) - PAD, 118 + (1 - qm) * -40, alpha=qm)
        bloque_texto(f, titulo, pastilla, kicker, t, TM["prod"])
        dibujar_ticker(f, gt, prog(t, 0.2, 0.6))
        return f
    return fn


# ------------------------------------------------------------ aéreas (arranque tipo dron)
class VentanaDron:
    def __init__(self, ruta, w, h):
        self.visor = Visor(ruta, w, h, 1.1, 1.05)
        self.w, self.h = w, h
        self.masc = mascara_redonda(w, h, 40)
        self.sombra = sombra_de(self.masc)

    def sprite(self, t, dur, z0, z1, a, b, roll0, roll1):
        e = ease_in_out(t / dur)
        fr = self.visor.frame(t / dur, z0, z1, a, b, roll0 + (roll1 - roll0) * e + 0.5 * np.sin(t * 1.9))
        self._hud(fr, t, dur)
        return recortar(fr, self.masc)

    @staticmethod
    def _hud(f, t, dur):
        h, w = f.shape[:2]
        x0, x1, y0, y1, L = 26, w - 26, 26, h - 26, 50
        for (x, y, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
            cv2.line(f, (x, y), (x + dx * L, y), (255, 255, 255), 4, cv2.LINE_AA)
            cv2.line(f, (x, y), (x, y + dy * L), (255, 255, 255), 4, cv2.LINE_AA)
        if np.sin(t * 5) > -0.2:
            cv2.circle(f, (x0 + 38, y0 + 40), 10, (235, 40, 40), -1, cv2.LINE_AA)
        cv2.putText(f, "REC", (x0 + 60, y0 + 51), cv2.FONT_HERSHEY_DUPLEX, 0.95, (255, 255, 255), 2, cv2.LINE_AA)
        txt = f"ALT {int(118 - 70 * ease_in_out(t / dur))} m"
        (tw, _), _ = cv2.getTextSize(txt, cv2.FONT_HERSHEY_DUPLEX, 0.95, 2)
        cv2.putText(f, txt, (x1 - 36 - tw, y0 + 51), cv2.FONT_HERSHEY_DUPLEX, 0.95, (255, 255, 255), 2, cv2.LINE_AA)


def pajaro(f, x, y, escala, fase, color=TIERRA):
    ala = np.sin(fase) * 0.9
    p = lambda dx, dy: (int(x + dx * escala), int(y + dy * escala))
    cv2.polylines(f, [np.array([p(-30, ala * 14 - 6), p(-14, ala * 6 - 14), p(0, 0), p(14, ala * 6 - 14), p(30, ala * 14 - 6)])],
                  False, color, max(2, int(3 * escala)), cv2.LINE_AA)


def escena_dron(ruta, dur, g0, win, cfg, textos, esc_a):
    ventana = VentanaDron(ruta, *win[2:])
    wx, wy, ww, wh = win
    z0, z1, a, b, r0, r1 = cfg

    def fn(t):
        gt = g0 + t
        f = fondo_papel(gt)
        q = prog(t, 0.0, 0.9)
        e = ease_out_cubic(q)
        sp = ventana.sprite(t, dur, z0, z1, a, b, r0, r1)
        ang = 1.1 * np.sin(t * 1.15)
        cx, cy = wx + ww / 2, wy + wh / 2 + 7 * np.sin(t * 1.7) + (1 - e) * 220
        sh = transformar(ventana.sombra, 1.0, ang)
        blit(f, sh, cx, cy + 24, alpha=clamp01(q * 3), centro=True)
        blit(f, transformar(sp, 0.9 + 0.1 * e, ang), cx, cy, alpha=clamp01(q * 3), centro=True)
        esc_a(f, t, gt)
        if g0 == 0 and t < 0.5:                       # entrada desde crema
            k = ease_out_cubic(t / 0.5)
            f = (f.astype(np.float32) * k + 255 * (1 - k)).astype(np.uint8)
        return f
    return fn


def decorado_a():
    top = Titulo("¿Sos de *Las* *Talitas*", 100, W - 80)
    l1 = T("y no sabés dónde comprar", 54, TINTA, SANS_SEMI)
    l2 = Titulo("*alimentos* para tus *animales?*", 76, W - 60)

    def fn(f, t, gt):
        top.draw(f, 295, t, TM["a_top"], paso=0.16)
        for i in range(3):          # bandada cruzando el cielo
            xx = -80 + ((t * (150 + 40 * i) + i * 260) % (W + 160))
            pajaro(f, xx, 235 + i * 38 + 12 * np.sin(t * 2 + i), 0.8 + 0.2 * i, t * 9 + i)
        q = ease_out_cubic(prog(t, TM["a_l1"], 0.55))
        blit(f, l1, (W - l1.shape[1]) / 2, 1355 + (1 - q) * 30, alpha=q)
        l2.draw(f, 1425, t, TM["a_l2"], paso=0.13)
    return fn


def decorado_b():
    logo = logo_redondo(210)
    pres = T("Te presento", 70, TIERRA, SERIF_IT)
    nombre = "FORRALITAS"
    tam = 126
    xs = []
    x0 = (W - ancho_texto(nombre, tam, SERIF)) / 2
    letras = [T(c, tam, VERDE_OSC, SERIF) for c in nombre]
    xs = [x0 + ancho_texto(nombre[:i], tam, SERIF) - PAD for i in range(len(nombre))]
    pin = icono("ubicacion", 96, TRIGO, VERDE_OSC)
    est = T("Estamos ubicados en", 44, TIERRA, SANS_SEMI)
    ruta = Titulo("*Ruta 305 km 7,5*", 92, W - 80)
    tal = T("Las Talitas", 58, TINTA, SERIF)

    def fn(f, t, gt):
        p = prog(t, 0.35, 0.8)
        cx, cy = W // 2, 215
        rot = gt * 40
        for k in range(18):
            a0 = k * 20 + rot
            cv2.ellipse(f, (cx, cy), (int(128 * ease_out_back(p)), int(128 * ease_out_back(p))), 0, a0, a0 + 9, TRIGO, 5, cv2.LINE_AA)
        blit(f, logo, cx, cy, alpha=clamp01(p * 3), escala=ease_out_back(p), centro=True)
        qp = ease_out_cubic(prog(t, 0.8, 0.5))
        blit(f, pres, (W - pres.shape[1]) / 2, 330 + (1 - qp) * 30, alpha=qp)
        for i, (s, x) in enumerate(zip(letras, xs)):
            q = prog(t, 1.05 + 0.06 * i, 0.5)
            blit(f, s, x, 395 + (1 - ease_out_cubic(q)) * 90, alpha=clamp01(q * 2), escala=0.7 + 0.3 * ease_out_back(q, 1.6))
        qpin = prog(t, TM["b_pin"], 0.7)
        blit(f, pin, W / 2, 1330 - (1 - ease_out_back(qpin, 1.7)) * 260, alpha=clamp01(qpin * 4), centro=True)
        q = ease_out_cubic(prog(t, TM["b_est"], 0.5))
        blit(f, est, (W - est.shape[1]) / 2, 1370 + (1 - q) * 25, alpha=q)
        ruta.draw(f, 1430, t, TM["b_ruta"], paso=0.12)
        q = ease_out_cubic(prog(t, TM["b_tal"], 0.5))
        blit(f, tal, (W - tal.shape[1]) / 2, 1560 + (1 - q) * 25, alpha=q)
    return fn


# ------------------------------------------------------------ "Y mucho más"
def escena_mosaico(rutas, nombres, dur, g0):
    titulo = Titulo("¡Y *mucho* *más!*", 112, W - 80)
    fotos = []
    rng = np.random.default_rng(3)
    for r, nom in zip(rutas, nombres):
        im = Image.open(r).convert("RGB")
        s0 = 236 / min(im.size)
        im = im.resize((int(im.width * s0 + .5), int(im.height * s0 + .5)), Image.LANCZOS)
        l, tp = (im.width - 236) // 2, (im.height - 236) // 2
        im = im.crop((l, tp, l + 236, tp + 236))
        base = caja(270, 322, 16, (255, 252, 244))
        sh = sombra_de(base[:, :, 3], 40, 0.35, 12)
        inte = np.dstack([np.asarray(im, np.float32), np.ones((236, 236), np.float32)])
        base = sobre(base, inte, 17, 17)
        fotos.append((base, sh, nom, float(rng.uniform(-8, 8))))
    caps = [T(n, 30 if len(n) < 14 else 24, TINTA, SERIF) for n in nombres]

    def fn(t):
        gt = g0 + t
        f = fondo_papel(gt)
        titulo.draw(f, 150, t, 0.2, paso=0.16)
        for i, ((base, sh, nom, ang), cap) in enumerate(zip(fotos, caps)):
            col, fila = i % 3, i // 3
            cx = 195 + col * 345 + (20 if fila % 2 else -10)
            cy = 478 + fila * 315
            q = prog(t, 0.6 + 0.13 * i, 0.7)
            e = ease_out_back(q, 1.9)
            wob = ang + 1.6 * np.sin(gt * 1.4 + i) * (q >= 1)
            tarjeta = sobre(base, cap, (270 - cap.shape[1]) // 2, 244)
            esc = 0.4 + 0.6 * e
            drop = (1 - ease_out_cubic(q)) * -300
            blit(f, transformar(sh, esc, wob), cx, cy + 14 + drop, alpha=clamp01(q * 2), centro=True)
            blit(f, transformar(tarjeta, esc, wob), cx, cy + drop, alpha=clamp01(q * 3), centro=True)
        dibujar_ticker(f, gt, 1.0)
        return f
    return fn


# ------------------------------------------------------------ cierre
def escena_cierre(g0):
    c = cv.CONFIG
    logo = logo_redondo(200)
    titulo = Titulo("¡TE *ESPERAMOS!*", 100, W - 100)

    def tarjeta(h):
        return caja(940, h, 38, VERDE_OSC, 0.96)
    n1 = cv.texto_ajustado(c["telefonos"][0], 64, 700, TRIGO, True)
    n2 = cv.texto_ajustado(c["telefonos"][1], 64, 700, TRIGO, True)
    card_tel = sobre(sobre(tarjeta(180), n1, 190 - PAD, 2), n2, 190 - PAD, 84)
    ic_tel = icono("telefono", 124)
    h1 = cv.texto_ajustado(c["horarios"][0], 46, 690, CREMA)
    h2 = cv.texto_ajustado(c["horarios"][1], 46, 690, (205, 235, 205))
    card_hora = sobre(sobre(tarjeta(180), h1, 190 - PAD, 14), h2, 190 - PAD, 86)
    u1 = cv.texto_ajustado(c["direccion"][0], 46, 690, CREMA)
    u2 = cv.texto_ajustado(c["direccion"][1], 42, 690, (205, 235, 205))
    card_ubic = sobre(sobre(sobre(tarjeta(140), icono("ubicacion", 96), 32, 22), u1, 170 - PAD, 2), u2, 170 - PAD, 66)
    e1 = cv.texto_ajustado(c["servicios"][0], 50, 700, CREMA)
    card_env = sobre(sobre(tarjeta(140), icono("camion", 96), 32, 22), e1, 170 - PAD, 8)
    banner = caja(940, 112, 56, TRIGO)
    tb = cv.texto_ajustado("VENTA POR MAYOR Y MENOR", 52, 860, VERDE_OSC)
    banner = sobre(banner, tb, (940 - tb.shape[1]) // 2, (112 - tb.shape[0]) // 2)
    tp = cv.texto_ajustado("Aceptamos todos los medios de pago", 42, 940, VERDE_OSC)
    chips = []
    for nom, etq in zip(("efectivo", "transferencia", "debito", "credito"), c["pagos"]):
        ch = sobre(caja(450, 112, 30, VERDE_OSC, 0.96), icono(nom, 80), 22, 16)
        t_ = cv.texto_ajustado(etq, 42, 300, CREMA)
        chips.append(sobre(ch, t_, 118 - PAD, (112 - t_.shape[0]) // 2))
    y_tel, y_hora, y_ubic, y_env, y_may, y_pago, y_chip = 410, 606, 802, 958, 1114, 1236, 1352
    firma1 = T("Forralitas", 84, VERDE_OSC, SERIF)
    firma2 = T("Todo para tus animales", 44, TIERRA, SERIF_IT)
    DIAG = cv.DIAGONAL

    def entra(t, t0, dur=0.65):
        q = prog(t, t0, dur)
        return q, ease_out_cubic(q)

    def fn(t):
        gt = g0 + t
        f = fondo_papel(gt)
        p = prog(t, 0.2, 0.8)
        blit(f, logo, W / 2, 170, alpha=clamp01(p * 3), escala=ease_out_back(p), centro=True)
        titulo.draw(f, 245, t, 0.7, paso=0.12)

        q, e = entra(t, cv.T_TEL)
        x = 70 + (1 - e) * W
        blit(f, card_tel, x, y_tel, alpha=clamp01(q * 2.5))
        if q > 0:
            cx, cy = x + 94, y_tel + 90
            fase = (t - cv.T_TIMBRE0) % cv.PERIODO_TIMBRE if t >= cv.T_TIMBRE0 else 99
            env = max(0.0, 1 - fase / 0.62)
            if env > 0:
                for k in range(3):
                    ov = f.copy()
                    cv2.circle(ov, (int(cx), int(cy)), int(74 + 30 * k + fase * 90), TRIGO, 4, cv2.LINE_AA)
                    a_ = env * (1 - k * 0.28) * 0.7
                    f[:] = cv2.addWeighted(ov, a_, f, 1 - a_, 0)
            ang = 20 * np.sin(fase * 52) * env if env > 0 else 0
            blit(f, cv.rotar_sprite(ic_tel, ang), cx, cy, alpha=clamp01(q * 2.5), escala=1 + 0.08 * env, centro=True)

        q, e = entra(t, cv.T_HORA)
        x = 70 + (1 - e) * W
        blit(f, card_hora, x, y_hora, alpha=clamp01(q * 2.5))
        if q > 0.05:
            cv.dibujar_reloj(f, int(x + 94), y_hora + 90, 58, t, cv.T_HORA)

        for card, t0, y in ((card_ubic, cv.T_UBIC, y_ubic), (card_env, cv.T_ENVIO, y_env)):
            q, e = entra(t, t0)
            blit(f, card, 70 - (1 - e) * W, y, alpha=clamp01(q * 2.5))

        q = prog(t, cv.T_MAYOR, 0.7)
        blit(f, banner, 70 + (1 - ease_out_back(q, 1.4)) * (-W), y_may, alpha=clamp01(q * 3))
        if q >= 1:
            pos = ((t - cv.T_MAYOR - 0.7) % 2.2) * 1700 - 400
            reg = f[y_may:y_may + 112, 70:70 + 940].astype(np.float32)
            reg += (np.exp(-(((DIAG[y_may:y_may + 112, 70:70 + 940] - pos) / 45) ** 2)) * banner[:, :, 3])[..., None] * 120
            f[y_may:y_may + 112, 70:70 + 940] = np.clip(reg, 0, 255).astype(np.uint8)

        qt = prog(t, cv.T_PAGOS, 0.6)
        blit(f, tp, (W - tp.shape[1]) / 2, y_pago + (1 - ease_out_cubic(qt)) * 25, alpha=ease_out_cubic(qt))
        for i, (ch, t0) in enumerate(zip(chips, cv.T_CHIPS)):
            q = prog(t, t0, 0.55)
            idle = 1 + 0.015 * np.sin(t * 3 + i) if q >= 1 else 1
            blit(f, ch, 70 + (i % 2) * 490 + 225, y_chip + (i // 2) * 128 + 56, alpha=clamp01(q * 3),
                 escala=max(ease_out_back(q, 2.4), 0.01) * idle, centro=True)

        T_FIRMA = TM["firma"]
        qf = prog(t, T_FIRMA, 0.7)
        if qf > 0:
            cv2.line(f, (int(W / 2 - 230 * ease_out_cubic(qf)), 1668), (int(W / 2 + 230 * ease_out_cubic(qf)), 1668),
                     TRIGO, 4, cv2.LINE_AA)
            blit(f, firma1, W / 2, 1735, alpha=ease_out_cubic(qf * 1.5), escala=0.8 + 0.2 * ease_out_back(qf, 1.5), centro=True)
            q2 = prog(t, T_FIRMA + 0.35, 0.6)
            blit(f, firma2, W / 2, 1812 + (1 - ease_out_cubic(q2)) * 20, alpha=ease_out_cubic(q2), centro=True)
        return f
    return fn


# ------------------------------------------------------------ transiciones
_BARRA = (_xx // (W / 9)).astype(np.int32)
_FILA = (_yy // (H / 14)).astype(np.int32)
_ANG = (np.arctan2(_xx - W / 2, -(_yy - H / 2)) % (2 * np.pi)) / (2 * np.pi)
_D_ESQ = np.hypot(_xx, H - _yy)
_ROMBO = np.abs(_xx - W / 2) + np.abs(_yy - H / 2) * (W / H) * 1.0


def _mezcla_mascara(a, b, m, borde=None, color=TRIGO):
    m = m[..., None]
    out = a.astype(np.float32) * (1 - m) + b.astype(np.float32) * m
    if borde is not None:
        out += borde[..., None] * np.array(color, np.float32)
    return np.clip(out, 0, 255).astype(np.uint8)


def tr_barras(a, b, p):
    e = ease_in_out(p)
    n = 9
    q = np.clip((e * 1.6 - np.arange(n) * 0.075) / 0.6, 0, 1)
    qm = q[_BARRA]
    par = (_BARRA % 2 == 0)
    pos = np.where(par, qm * H, H - qm * H)
    m = np.where(par, _yy < pos, _yy > pos).astype(np.float32)
    borde = np.clip(1 - np.abs(_yy - pos) / 7, 0, 1) * ((qm > 0) & (qm < 1))
    return _mezcla_mascara(a, b, m, borde)


def tr_persianas(a, b, p):
    e = ease_in_out(p)
    n = 14
    q = np.clip((e * 1.5 - np.arange(n) * 0.04) / 0.6, 0, 1)
    qm = q[_FILA]
    par = (_FILA % 2 == 0)
    pos = np.where(par, qm * W, W - qm * W)
    m = np.where(par, _xx < pos, _xx > pos).astype(np.float32)
    borde = np.clip(1 - np.abs(_xx - pos) / 7, 0, 1) * ((qm > 0) & (qm < 1))
    return _mezcla_mascara(a, b, m, borde)


def tr_reloj(a, b, p):
    e = ease_in_out(p)
    m = (_ANG < e).astype(np.float32)
    m = cv2.GaussianBlur(m, (0, 0), 1.2)
    borde = np.clip(1 - np.abs(_ANG - e) * 260, 0, 1) * (0 < e < 1)
    return _mezcla_mascara(a, b, m, borde)


def tr_circulo(a, b, p):
    r = ease_in_out(p) * float(_D_ESQ.max()) * 1.02
    m = np.clip((r - _D_ESQ) / 4 + 0.5, 0, 1)
    borde = np.clip(1 - np.abs(_D_ESQ - r) / 16, 0, 1) * (p < 0.99)
    out = _mezcla_mascara(a, b, m, borde)
    anillo = np.clip(1 - np.abs(_D_ESQ - (r - 46)) / 8, 0, 1)[..., None] * (p < 0.97)
    return np.clip(out.astype(np.float32) * (1 - anillo * 0.7) + anillo * np.array(VERDE_OSC, np.float32) * 0.7, 0, 255).astype(np.uint8)


def tr_rombo(a, b, p):
    r = ease_in_out(p) * float(_ROMBO.max()) * 1.02
    m = np.clip((r - _ROMBO) / 4 + 0.5, 0, 1)
    borde = np.clip(1 - np.abs(_ROMBO - r) / 14, 0, 1) * (p < 0.99)
    return _mezcla_mascara(a, b, m, borde)


_LOGO_TR = logo_redondo(220)


def tr_cortina(a, b, p):
    e1, e2 = ease_in_out(clamp01(p * 2)), ease_in_out(clamp01(p * 2 - 1))
    out = a if p < 0.5 else b
    out = np.ascontiguousarray(out).copy()
    cubierto = e1 if p < 0.5 else 1 - e2
    ancho = int(cubierto * W / 2)
    if ancho > 0:
        out[:, :ancho] = np.array(VERDE_OSC, np.uint8)
        out[:, W - ancho:] = np.array(VERDE_OSC, np.uint8)
        cv2.line(out, (ancho, 0), (ancho, H), TRIGO, 8, cv2.LINE_AA)
        cv2.line(out, (W - ancho, 0), (W - ancho, H), TRIGO, 8, cv2.LINE_AA)
        if cubierto > 0.97:
            s = 0.8 + 0.4 * np.sin(np.pi * clamp01((p - 0.42) / 0.16))
            blit(out, _LOGO_TR, W / 2, H / 2, escala=s, centro=True)
    return out


def tr_zoom_desenfoque(a, b, p):
    e = ease_in_out(p)
    def radial(img, amt):
        acc = np.zeros(img.shape, np.float32)
        n = 7
        for i in range(n):
            s = 1 + amt * i / (n - 1)
            M = np.array([[s, 0, (1 - s) * W / 2], [0, s, (1 - s) * H / 2]], np.float32)
            acc += cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        return (acc / n).astype(np.uint8)
    sb = 1.15 - 0.15 * e
    Mb = np.array([[sb, 0, (1 - sb) * W / 2], [0, sb, (1 - sb) * H / 2]], np.float32)
    A = radial(a, 0.22 * e)
    B = radial(cv2.warpAffine(b, Mb, (W, H), borderMode=cv2.BORDER_REPLICATE), 0.12 * (1 - e))
    return cv2.addWeighted(A, 1 - e, B, e, 0)


def tr_empuje(a, b, p):
    off = int(ease_in_out(p) * W)
    out = np.empty_like(a)
    out[:, :W - off] = a[:, off:]
    out[:, W - off:] = b[:, :off]
    if 0 < off < W:                              # sombra del "papel" que entra
        x = W - off
        g = np.clip(1 - (np.arange(W) - x) / 120.0, 0, 1)
        g[: x] = 0
        out = (out.astype(np.float32) * (1 - 0.35 * g)[None, :, None]).astype(np.uint8)
        cv2.line(out, (x, 0), (x, H), TRIGO, 6, cv2.LINE_AA)
    k = int(1 + 70 * np.sin(np.pi * p))
    k += (k % 2 == 0)
    return cv2.blur(out, (k, 1)) if k > 1 else out


CICLO_TR = [tr_barras, tr_circulo, tr_cortina, tr_reloj, tr_persianas, tr_rombo, tr_empuje, tr_zoom_desenfoque]


def transiciones(n):
    lista = [tr_zoom_desenfoque]
    i = 0
    while len(lista) < n - 1:
        lista.append(CICLO_TR[i % len(CICLO_TR)])
        i += 1
    lista.append(tr_cortina)
    return lista


# ------------------------------------------------------------ línea de tiempo
def construir():
    fotos = sorted(Path("fotos_presentacion").glob("*.jp*g"), key=lambda p: p.name)
    assert len(fotos) == len(PRODUCTOS)
    durs = [D_A, D_B] + [D_PROD] * len(fotos) + [D_MOS, cv.D_CIERRE]
    inicios, t = [], 0.0
    for d in durs:
        inicios.append(t)
        t += d - TR
    total = inicios[-1] + durs[-1]

    segs = [(D_A, escena_dron("assets/dron/dron1.jpg", D_A, inicios[0], (60, 590, 960, 700),
                              (1.0, 1.7, (0.5, 0.5), (0.2, 0.5), -1.5, 1.0), None, decorado_a())),
            (D_B, escena_dron("assets/dron/dron2.jpg", D_B, inicios[1], (60, 650, 960, 600),
                              (1.0, 1.75, (0.5, 0.5), (0.42, 0.58), 1.2, -0.8), None, decorado_b()))]
    variantes = ["tarjeta", "circulo", "diagonal"]
    for i, (ruta, (tit, sub)) in enumerate(zip(fotos, PRODUCTOS)):
        segs.append((D_PROD, escena_producto(ruta, i, tit, sub, D_PROD, inicios[2 + i],
                                             variantes[i % 3], CAMARAS[i % len(CAMARAS)])))
    elegidas = [fotos[i] for i in (0, 1, 2, 3, 4, 5, 6, 7, 9, 10, 12, 13)]
    nombres = ["Alfa", "Engorde de cerdo", "Mezcla de caballo", "Pellet de alfa", "Maíz entero", "Maíz quebrado",
               "Pellet de trigo", "Afrecho de trigo", "Ponedora", "Parrillero", "Perro y gato", "Virutas"]
    segs.append((D_MOS, escena_mosaico(elegidas, nombres, D_MOS, inicios[-2])))
    segs.append((cv.D_CIERRE, escena_cierre(inicios[-1])))
    return segs, inicios, total


def hacer_frame_fn(segs, inicios, total):
    trans = transiciones(len(segs))
    n = len(PRODUCTOS)
    b0, b1 = inicios[2] + TR, inicios[2 + n]

    def make_frame(t):
        t = min(t, total - 1e-3)
        act = [i for i, (s, (d, _)) in enumerate(zip(inicios, segs)) if s <= t < s + d]
        if len(act) == 1:
            f = segs[act[0]][1](t - inicios[act[0]])
        else:
            a, b = act[0], act[-1]
            f = trans[a](segs[a][1](t - inicios[a]), segs[b][1](t - inicios[b]), (t - inicios[b]) / TR)
        if b0 - 0.2 <= t <= b1 + 0.2:
            f = np.ascontiguousarray(f)
            x0, x1, y = 60, W - 60, 58
            q = clamp01((t - b0) / (b1 - b0))
            ov = f.copy()
            cv2.line(ov, (x0, y), (x1, y), TIERRA, 8, cv2.LINE_AA)
            f = cv2.addWeighted(ov, 0.22, f, 0.78, 0)
            cv2.line(f, (x0, y), (int(x0 + (x1 - x0) * q), y), TRIGO, 8, cv2.LINE_AA)
        return f
    return make_frame


def main():
    segs, inicios, total = construir()
    make_frame = hacer_frame_fn(segs, inicios, total)
    if "--frames" in sys.argv:
        Path("videos_salida").mkdir(exist_ok=True)
        for s in [float(x) for x in sys.argv[sys.argv.index("--frames") + 1:]]:
            Image.fromarray(make_frame(s)).save(f"videos_salida/prev_{s:05.1f}.png")
        print("duración total:", round(total, 2), "s | inicios:", [round(x, 1) for x in inicios])
        return
    Path(SALIDA).parent.mkdir(exist_ok=True)
    out = inicios[-1]
    musica = audio_campo.generar(
        total,
        t_transiciones=[inicios[i] + 0.0 for i in range(1, len(segs))],
        t_dings=[out + o + 0.1 for o in (cv.T_HORA, cv.T_UBIC, cv.T_ENVIO, cv.T_MAYOR, cv.T_PAGOS, *cv.T_CHIPS)],
        t_campanas=[out + cv.T_TIMBRE0 + k * cv.PERIODO_TIMBRE for k in range(3)] + [inicios[1] + 1.2],
        t_melodia=inicios[1] + 0.5)
    video = VideoClip(make_frame, duration=total).with_audio(AudioFileClip(musica).subclipped(0, total))
    video.write_videofile(SALIDA, fps=FPS, codec="libx264", audio_codec="aac", audio_bitrate="192k",
                          preset="medium", ffmpeg_params=["-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart"])
    print("Listo:", SALIDA, f"({total:.1f} s)")


if __name__ == "__main__":
    main()
