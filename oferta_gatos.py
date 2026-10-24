"""Video de oferta (10 s, vertical 1080x1920): dos combos Sabrositos gato + piedras sanitarias.

Uso:
    python oferta_gatos.py                 # genera videos_salida/oferta_gatos.mp4
    python oferta_gatos.py --frames 1 3 8  # vistas previas
"""
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from moviepy import AudioFileClip, VideoClip
from PIL import Image, ImageDraw, ImageFont
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

import audio as au
from efectos import (H, W, ancho_texto, blit, caja, clamp01, desde_pil, ease_in_out, ease_out_back,
                     ease_out_cubic, icono, logo_redondo, prog, rotar_sprite, sobre, texto)

FPS, DUR = 30, 10.0
SALIDA = "videos_salida/oferta_gatos.mp4"
INTER = "/usr/share/fonts/opentype/inter/"
BLK, XB, SB = INTER + "Inter-Black.otf", INTER + "Inter-ExtraBold.otf", INTER + "Inter-SemiBold.otf"
ORO, ORO2, BLANCO, OSC = (255, 205, 60), (255, 160, 20), (255, 255, 255), (20, 14, 10)

COMBOS = [
    dict(n=1, bolsa="assets/oferta/sabrositos_mix_bolsa.png", l1="SABROSITOS", l2="GATO MIX", precio="$25.000",
         c1=(150, 14, 44), c2=(28, 2, 10), acento=(255, 90, 120)),
    dict(n=2, bolsa="assets/oferta/sabrositos_pescado_bolsa.png", l1="SABROSITOS", l2="GATO PESCADO", precio="$28.000",
         c1=(10, 92, 170), c2=(2, 12, 34), acento=(90, 200, 255)),
]
# línea de tiempo (s): intro, combo 1, combo 2, cierre
T_INTRO, T_C1, T_C2, T_FIN = (0.0, 1.15), (1.0, 4.25), (4.1, 7.35), (7.2, 10.0)
OV = 0.15          # solapamiento de transición
STAMP = 1.3        # instante (local) en que cae el precio


def T(txt, tam, color=BLANCO, ruta=BLK, sombra=True):
    return texto(txt, tam, color, sombra, ruta)


def ajustar(txt, tam, ruta, max_w):
    while ancho_texto(txt, tam, ruta) > max_w and tam > 18:
        tam -= 2
    return tam


def pad(spr, p=0.18):
    h, w = spr.shape[:2]
    py, px = int(h * p), int(w * p)
    out = np.zeros((h + 2 * py, w + 2 * px, 4), np.float32)
    out[py:py + h, px:px + w] = spr
    return out


def cargar(ruta, alto):
    im = Image.open(ruta).convert("RGBA")
    im = im.resize((int(im.width * alto / im.height), alto), Image.LANCZOS)
    return pad(desde_pil(im))


# ------------------------------------------------------------ fondos
_yy, _xx = np.mgrid[0:H // 3, 0:W // 3].astype(np.float32) * 3
_ANG = np.arctan2(_yy - 980, _xx - W / 2)
_DIST = np.hypot(_xx - W / 2, _yy - 980)
_R = _DIST / np.hypot(W / 2, H / 2)


def fondo(t, c1, c2, rayos=1.0, cy=980):
    base = np.array(c1, np.float32) * np.clip(1 - _R * 1.15, 0, 1)[..., None] + \
        np.array(c2, np.float32) * np.clip(_R * 1.15, 0, 1)[..., None]
    if rayos > 0:
        r = (0.5 + 0.5 * np.cos(18 * (_ANG - t * 0.35))) ** 6 * np.clip(1 - _DIST / 1300, 0, 1)
        base += r[..., None] * np.array(c1, np.float32) * 0.55 * rayos + r[..., None] * 22 * rayos
    f = cv2.resize(np.clip(base, 0, 255).astype(np.uint8), (W, H), interpolation=cv2.INTER_LINEAR)
    return f


_PART = np.random.default_rng(3).uniform(0, 1, (60, 4))


def chispas(f, t, color, n=60, op=0.6):
    ov = f.copy()
    for x, y, v, ph in _PART[:n]:
        cx = x * W + 25 * np.sin(t * 1.3 + ph * 7)
        cy = (y * (H + 80) - t * (90 + 220 * v)) % (H + 80) - 40
        r = 2 + 5 * v
        brillo = 0.5 + 0.5 * np.sin(t * 9 + ph * 20)
        cv2.circle(ov, (int(cx), int(cy)), int(r * (0.6 + 0.6 * brillo)), color, -1, cv2.LINE_AA)
    return cv2.addWeighted(ov, op, f, 1 - op, 0)


def brillo_suelo(f, cx, cy, rx, ry, color, op):
    ov = np.zeros_like(f)
    cv2.ellipse(ov, (int(cx), int(cy)), (int(rx), int(ry)), 0, 0, 360, color, -1, cv2.LINE_AA)
    ov = cv2.GaussianBlur(ov, (0, 0), 40)
    return cv2.add(f, (ov * op).astype(np.uint8))


def camara(f, zoom=1.0, dx=0.0, dy=0.0, ang=0.0):
    if zoom == 1.0 and dx == 0 and dy == 0 and ang == 0:
        return f
    M = cv2.getRotationMatrix2D((W / 2, H / 2), ang, zoom)
    M[0, 2] += dx
    M[1, 2] += dy
    return cv2.warpAffine(f, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def temblor(t, t0, amp=22, dur=0.4):
    if t < t0 or t > t0 + dur:
        return 0.0, 0.0
    k = (1 - (t - t0) / dur) ** 2
    return amp * k * np.sin(t * 95), amp * k * np.cos(t * 81)


def destello(f, t, t0, dur=0.16, op=0.85):
    q = (t - t0) / dur
    if 0 <= q <= 1:
        a = op * (1 - q) ** 2
        f = cv2.addWeighted(f, 1 - a, np.full_like(f, 255), a, 0)
    return f


# ------------------------------------------------------------ piezas gráficas
def estallido(diam, color1, color2, puntas=22):
    ss = 3
    L = diam * ss
    im = Image.new("RGBA", (L, L), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pts = []
    for k in range(puntas * 2):
        a = np.pi * k / puntas
        r = L / 2 * (1.0 if k % 2 == 0 else 0.80)
        pts.append((L / 2 + r * np.cos(a), L / 2 + r * np.sin(a)))
    d.polygon(pts, fill=color2 + (255,))
    pts2 = [(L / 2 + (x - L / 2) * 0.93, L / 2 + (y - L / 2) * 0.93) for x, y in pts]
    d.polygon(pts2, fill=color1 + (255,))
    return desde_pil(im.resize((diam, diam), Image.LANCZOS))


def tarjeta_precio(precio, acento):
    w, h = 820, 250
    base = caja(w + 16, h + 16, 60, (255, 255, 255))
    oro = Image.new("RGB", (w, h))
    g = np.linspace(0, 1, h)[:, None, None]
    arr = np.array(ORO, np.float32) * (1 - g) + np.array(ORO2, np.float32) * g
    oro = desde_pil(Image.fromarray(np.repeat(arr, w, axis=1).astype(np.uint8)).convert("RGBA"))
    m = caja(w, h, 54, (255, 255, 255))[:, :, 3:4]
    oro = oro * m
    base = sobre(base, oro, 8, 8)
    tam = ajustar(precio, 196, BLK, w - 60)
    tp = T(precio, tam, OSC, BLK, sombra=False)
    base = sobre(base, tp, (w + 16 - tp.shape[1]) // 2, (h + 16 - tp.shape[0]) // 2 + 4)
    etq_t = T("LLEVÁS LAS 2 POR", 40, BLANCO, BLK, sombra=False)
    etq = caja(etq_t.shape[1] - 52 + 56, 72, 36, (210, 20, 40))
    etq = sobre(etq, etq_t, 28 - 26, (72 - etq_t.shape[0]) // 2 + 2)
    return pad(base, 0.0), pad(etq, 0.0)


def signo_mas(diam=130):
    s = caja(diam, diam, diam // 2, ORO)
    t = T("+", 120, OSC, BLK, sombra=False)
    return sobre(s, t, (diam - t.shape[1]) // 2, (diam - t.shape[0]) // 2 - 6)


def barra_marca():
    logo = logo_redondo(70)
    n = T("FORRALITAS", 36, BLANCO, BLK, sombra=False)
    l = T("Las Talitas", 28, (220, 220, 220), SB, sombra=False)
    base = np.zeros((90, 560, 4), np.float32)
    base = sobre(base, logo, 0, 10)
    base = sobre(base, n, 84 - 26, -2)
    return sobre(base, l, 84 - 26, 36)


MARCA = barra_marca()


# ------------------------------------------------------------ escenas
def escena_intro():
    letras = "OFERTA"
    tam = 250
    sp = [T(c, tam, BLANCO, BLK) for c in letras]
    x0 = (W - ancho_texto(letras, tam, BLK)) / 2
    cx = [x0 + ancho_texto(letras[:i], tam, BLK) + ancho_texto(c, tam, BLK) / 2 for i, c in enumerate(letras)]
    sub = T("COMBOS PARA TU GATO", 70, ORO, BLK)
    imper = T("¡IMPERDIBLE!", 54, BLANCO, XB)

    def fn(t):
        f = fondo(t, (90, 16, 90), (8, 2, 14), rayos=clamp01(t / 0.3))
        f = chispas(f, t, ORO, 40, 0.5)
        # haz de luz que cruza
        q = prog(t, 0.0, 0.5)
        if 0 < q < 1:
            x = int(-300 + q * (W + 600))
            ov = np.zeros_like(f)
            cv2.line(ov, (x - 500, 1300), (x + 500, 500), (255, 230, 170), 70, cv2.LINE_AA)
            f = cv2.add(f, (cv2.GaussianBlur(ov, (0, 0), 30) * 0.7).astype(np.uint8))
        for i, (s, c) in enumerate(zip(sp, cx)):
            qi = prog(t, 0.12 + 0.045 * i, 0.22)
            if qi <= 0:
                continue
            esc = 3.0 - 2.0 * ease_out_cubic(qi)
            blit(f, s, c, 860, alpha=clamp01(qi * 3), escala=esc, centro=True)
        qs = prog(t, 0.5, 0.35)
        blit(f, sub, W / 2 - (1 - ease_out_cubic(qs)) * 700, 1040, alpha=clamp01(qs * 3), centro=True)
        qi2 = prog(t, 0.65, 0.3)
        blit(f, imper, W / 2, 1150, alpha=clamp01(qi2 * 3), escala=max(ease_out_back(qi2, 2.4), 0.01), centro=True)
        dx, dy = temblor(t, 0.36, 26, 0.45)
        f = destello(f, t, 0.36, 0.14, 0.6)
        return camara(f, 1.0 + 0.04 * t, dx, dy)
    return fn


def escena_combo(c, dur):
    bolsa = cargar(c["bolsa"], 720)
    piedras = cargar("assets/oferta/piedras_rec.png", 530)
    kick = T(f"COMBO {c['n']}", 44, OSC, BLK, sombra=False)
    pill = sobre(caja(kick.shape[1] - 52 + 60, 76, 38, ORO), kick, 30 - 26, (76 - kick.shape[0]) // 2 + 2)
    l1 = T(c["l1"], ajustar(c["l1"], 140, BLK, W - 80), BLANCO, BLK)
    l2 = T(c["l2"], ajustar(c["l2"], 100, BLK, W - 80), ORO, BLK)
    l3t = T("+ PIEDRAS SANITARIAS 1 KG", 50, BLANCO, XB, sombra=False)
    l3 = sobre(caja(l3t.shape[1] - 52 + 64, 82, 41, (0, 0, 0), 0.45), l3t, 32 - 26, (82 - l3t.shape[0]) // 2 + 2)
    mas = signo_mas()
    burst = estallido(760, ORO, ORO2)
    card, etq = tarjeta_precio(c["precio"], c["acento"])

    def fn(t):
        f = fondo(t, c["c1"], c["c2"], rayos=1.0)
        f = brillo_suelo(f, W / 2, 1330, 460, 70, c["acento"], 0.55)
        f = chispas(f, t, c["acento"], 50, 0.45)
        # textos superiores
        qp = prog(t, 0.05, 0.4)
        blit(f, pill, W / 2, 150 - (1 - ease_out_cubic(qp)) * 80, alpha=clamp01(qp * 3), centro=True)
        q1 = prog(t, 0.12, 0.4)
        blit(f, l1, W / 2, 280, alpha=clamp01(q1 * 3), escala=2.2 - 1.2 * ease_out_cubic(q1), centro=True)
        q2 = prog(t, 0.3, 0.4)
        blit(f, l2, W / 2 + (1 - ease_out_cubic(q2)) * 900, 405, alpha=clamp01(q2 * 3), centro=True)
        q3 = prog(t, 0.55, 0.4)
        blit(f, l3, W / 2, 520, alpha=clamp01(q3 * 3), escala=max(ease_out_back(q3, 2.0), 0.01), centro=True)
        # productos
        flot = 10 * np.sin(t * 2.6)
        qb = prog(t, 0.0, 0.55)
        if qb > 0:
            e = ease_out_back(qb, 1.3)
            sp = rotar_sprite(bolsa, -28 * (1 - ease_out_cubic(qb)) + 3 * np.sin(t * 1.7))
            blit(f, sp, 375 - (1 - e) * 900, 960 + flot, alpha=clamp01(qb * 4), escala=0.75 + 0.25 * e, centro=True)
        qd = prog(t, 0.18, 0.55)
        if qd > 0:
            e = ease_out_back(qd, 1.3)
            sp = rotar_sprite(piedras, 24 * (1 - ease_out_cubic(qd)) - 3 * np.sin(t * 1.5))
            blit(f, sp, 770 + (1 - e) * 900, 1040 - flot, alpha=clamp01(qd * 4), escala=0.75 + 0.25 * e, centro=True)
        qm = prog(t, 0.5, 0.35)
        blit(f, mas, 610, 1010, alpha=clamp01(qm * 3), escala=max(ease_out_back(qm, 2.6), 0.01) * (1 + 0.05 * np.sin(t * 6)),
             centro=True)
        # precio
        qs = prog(t, STAMP, 0.28)
        if qs > 0:
            blit(f, rotar_sprite(burst, t * 25), W / 2, 1530, alpha=0.9 * clamp01(qs * 3),
                 escala=0.4 + 0.6 * ease_out_back(qs, 1.6), centro=True)
            esc = 2.4 - 1.4 * ease_out_cubic(qs)
            pul = 1 + 0.025 * np.sin((t - STAMP) * 7) * clamp01((t - STAMP - 0.4) * 3)
            blit(f, card, W / 2, 1560, alpha=clamp01(qs * 4), escala=esc * pul, centro=True)
            qe = prog(t, STAMP + 0.22, 0.3)
            blit(f, etq, W / 2, 1405, alpha=clamp01(qe * 3), escala=max(ease_out_back(qe, 2.4), 0.01), centro=True)
        # marca abajo
        qm2 = ease_out_cubic(prog(t, 0.3, 0.4))
        blit(f, MARCA, 40, 1800 + (1 - qm2) * 100, alpha=qm2)
        f = destello(f, t, STAMP + 0.05, 0.16, 0.75)
        dx, dy = temblor(t, STAMP + 0.05, 24, 0.4)
        return camara(f, 1.0 + 0.035 * t / dur, dx, dy)
    return fn


def escena_final(dur):
    logo = logo_redondo(250)
    nombre = T("FORRALITAS", 112, BLANCO, BLK)
    lema = T("¡VENÍ A BUSCAR TU COMBO!", 50, ORO, BLK)
    verde1, verde2 = (20, 96, 48), (3, 22, 10)

    def fila(ic, l1, l2=None, tam1=58, tam2=40, col1=BLANCO):
        w, h = 960, 150 if l2 else 116
        base = caja(w, h, 32, (0, 0, 0), 0.38)
        base = sobre(base, icono(ic, 88), 26, (h - 88) // 2)
        t1 = T(l1, ajustar(l1, tam1, BLK, 790), col1, BLK, sombra=False)
        base = sobre(base, t1, 136 - 26, (14 if l2 else (h - t1.shape[0]) // 2 + 2) - (26 if l2 else 0))
        if l2:
            t2 = T(l2, ajustar(l2, tam2, XB, 790), (210, 235, 215), XB, sombra=False)
            base = sobre(base, t2, 136 - 26, 82 - 26)
        return base
    filas = [fila("telefono", "381 526 9004", None, 66),
             fila("telefono", "381 633 4344", None, 66),
             fila("ubicacion", "Ruta 305 km 7,5", "Las Talitas"),
             fila("reloj", "Lun a Vie 8:00 a 19:00", "Sábados 8:30 a 19:00", 52, 44),
             fila("camion", "Envíos según la zona", "Venta por mayor y menor", 50, 44)]
    espera = T("¡TE ESPERAMOS!", 96, ORO, BLK)
    pagos_t = T("ACEPTAMOS TODOS LOS MEDIOS DE PAGO", 36, ORO, BLK, sombra=False)
    chips = []
    for nom, etq in (("efectivo", "Efectivo"), ("transferencia", "Transferencia"), ("debito", "Débito"),
                     ("credito", "Crédito")):
        ch = caja(225, 150, 26, (0, 0, 0), 0.38)
        ch = sobre(ch, icono(nom, 72), (225 - 72) // 2, 12)
        tt = T(etq, ajustar(etq, 30, XB, 210), BLANCO, XB, sombra=False)
        chips.append(sobre(ch, tt, (225 - (tt.shape[1] - 52)) // 2 - 26, 96 - 26))
    ys = [560, 690, 820, 990, 1160]

    def fn(t):
        f = fondo(t, verde1, verde2, rayos=0.7)
        f = chispas(f, t, ORO, 40, 0.4)
        p = prog(t, 0.0, 0.45)
        blit(f, rotar_sprite(pad(logo, 0.1), -30 * (1 - ease_out_cubic(p))), W / 2, 200, alpha=clamp01(p * 3),
             escala=max(ease_out_back(p, 1.8), 0.01), centro=True)
        qn = prog(t, 0.12, 0.35)
        blit(f, nombre, W / 2, 395, alpha=clamp01(qn * 3), escala=1.8 - 0.8 * ease_out_cubic(qn), centro=True)
        ql = prog(t, 0.25, 0.3)
        blit(f, lema, W / 2, 485, alpha=clamp01(ql * 3), wipe=ease_out_cubic(ql), centro=True)
        for i, (fl, y) in enumerate(zip(filas, ys)):
            q = prog(t, 0.32 + 0.09 * i, 0.32)
            e = ease_out_cubic(q)
            x = 60 + (1 - e) * (W if i % 2 == 0 else -W)
            blit(f, fl, x, y, alpha=clamp01(q * 3))
        qp2 = prog(t, 0.8, 0.3)
        blit(f, pagos_t, W / 2, 1360, alpha=clamp01(qp2 * 3), centro=True)
        for i, ch in enumerate(chips):
            q = prog(t, 0.88 + 0.07 * i, 0.3)
            blit(f, ch, 60 + 112 + i * 245, 1500, alpha=clamp01(q * 3), escala=max(ease_out_back(q, 2.4), 0.01),
                 centro=True)
        qw = prog(t, 1.25, 0.35)
        blit(f, espera, W / 2, 1730, alpha=clamp01(qw * 3), escala=max(ease_out_back(qw, 2.0), 0.01)
             * (1 + 0.03 * np.sin(t * 6) * clamp01((t - 1.6) * 3)), centro=True)
        dx, dy = temblor(t, 0.05, 18, 0.35)
        f = destello(f, t, 0.02, 0.14, 0.7)
        return camara(f, 1.0 + 0.025 * t / dur, dx, dy)
    return fn


# ------------------------------------------------------------ montaje
def zoom_blur(img, amt, n=5):
    if amt < 0.004:
        return img
    acc = np.zeros(img.shape, np.float32)
    for i in range(n):
        s = 1 + amt * i / (n - 1)
        M = np.array([[s, 0, (1 - s) * W / 2], [0, s, (1 - s) * H / 2]], np.float32)
        acc += cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REPLICATE)
    return (acc / n).astype(np.uint8)


def transicion(a, b, p):
    e = ease_in_out(p)
    A, B = zoom_blur(a, 0.25 * e), zoom_blur(b, 0.25 * (1 - e))
    out = cv2.addWeighted(A, 1 - e, B, e, 0)
    fl = 0.7 * np.sin(np.pi * p)
    return cv2.addWeighted(out, 1 - fl, np.full_like(out, 255), fl, 0)


ESCENAS = None


def armar():
    return [(T_INTRO, escena_intro()),
            (T_C1, escena_combo(COMBOS[0], T_C1[1] - T_C1[0])),
            (T_C2, escena_combo(COMBOS[1], T_C2[1] - T_C2[0])),
            (T_FIN, escena_final(T_FIN[1] - T_FIN[0]))]


def make_frame(t):
    t = min(t, DUR - 1e-3)
    act = [(r, fn) for r, fn in ESCENAS if r[0] <= t < r[1]]
    if len(act) == 1:
        (r, fn), = act
        return fn(t - r[0])
    (ra, fa), (rb, fb) = act[0], act[-1]
    return transicion(fa(t - ra[0]), fb(t - rb[0]), (t - rb[0]) / (ra[1] - rb[0]))


# ------------------------------------------------------------ audio épico
SR = au.SR


def riser(dur=1.0):
    n = int(dur * SR)
    tt = np.linspace(0, 1, n)
    ruido = np.random.default_rng(5).standard_normal(n)
    out = np.zeros(n)
    trozo = n // 24
    for k in range(24):
        fc = 400 + 7000 * (k / 23) ** 2
        seg = au._filtro(ruido[k * trozo:(k + 1) * trozo], "bandpass", [fc * 0.7, min(fc * 1.4, 20000)])
        out[k * trozo:k * trozo + len(seg)] = seg
    tono = np.sin(2 * np.pi * np.cumsum(200 + 900 * tt ** 2) / SR) * 0.25
    return (out * 1.6 + tono) * tt ** 2


def braam(dur=1.4, f=55.0):
    t = au._t(dur)
    s = sum(((2 * ((f * k * t) % 1) - 1)) for k in (1, 1.005, 0.997, 2.0))
    s = au._filtro(s, "lowpass", 700)
    return s * np.minimum(t / 0.03, 1) * np.exp(-t * 1.6) * 0.5


def crash(dur=1.6):
    t = au._t(dur)
    r = np.random.default_rng(8).standard_normal(t.size)
    return au._filtro(r, "highpass", 4500) * np.exp(-t * 3.2) * 0.6


def cha_ching():
    return au.ding(2093.0) * 0.8 + np.pad(au.ding(2637.0), (int(0.07 * SR), 0))[:len(au.ding())] * 0.7


def generar_audio(ruta="videos_salida/_oferta_audio.wav"):
    n = int((DUR + 0.5) * SR)
    buf = np.zeros((n, 2))
    P = au._poner
    bpm = 128
    beat = 60 / bpm
    nota = au.nota
    # intro
    P(buf, braam(), 0.30, 0.9)
    P(buf, au.golpe(), 0.36, 1.0)
    P(buf, crash(), 0.36, 0.5)
    P(buf, riser(0.6), 0.42, 0.25)
    # base rítmica desde el combo 1
    t0 = T_C1[0]
    acordes = [(45, (57, 60, 64)), (41, (57, 60, 65)), (48, (55, 60, 64)), (43, (55, 59, 62))]   # Am F C G
    i = 0
    while t0 + i * beat < T_FIN[0] + 2.5:
        t = t0 + i * beat
        bj, ac = acordes[(i // 4) % 4]
        P(buf, au.bombo(), t, 1.0)
        if i % 2 == 1:
            P(buf, au.palmada(), t, 0.55)
        P(buf, au.hihat(), t + beat / 2, 0.30)
        P(buf, au.bajo(nota(bj - 12), beat * 0.45), t, 0.55)
        P(buf, au.bajo(nota(bj - 12), beat * 0.45), t + beat / 2, 0.45)
        if i % 4 == 0:
            P(buf, au.colchon([nota(m) for m in ac], 4 * beat + 0.3), t, 0.16)
        for j, m in enumerate((ac[0], ac[2], ac[1] + 12, ac[2])):
            P(buf, au.pluck(nota(m + 12)), t + j * beat / 4, 0.14, pan=0.35 + 0.3 * (j % 2))
        i += 1
    # transiciones, risers y golpes de precio
    for tr in (T_C1[0], T_C2[0], T_FIN[0]):
        P(buf, au.whoosh(0.5), tr - 0.18, 0.45)
    for c0 in (T_C1[0], T_C2[0]):
        ts = c0 + STAMP + 0.05
        P(buf, riser(0.9), ts - 0.9, 0.35)
        P(buf, au.golpe(), ts, 1.0)
        P(buf, crash(), ts, 0.45)
        P(buf, cha_ching(), ts + 0.08, 0.40)
    P(buf, braam(1.6, 55.0), T_FIN[0] + 0.02, 0.7)
    P(buf, au.golpe(), T_FIN[0] + 0.02, 0.9)
    P(buf, crash(2.0), T_FIN[0] + 0.02, 0.4)
    buf = np.tanh(buf * 0.9)[:int(DUR * SR)]
    fo = int(0.7 * SR)
    buf[-fo:] *= np.linspace(1, 0, fo)[:, None]
    buf *= 0.9 / np.abs(buf).max()
    tmp = "videos_salida/_oferta_crudo.wav"
    wavfile.write(tmp, SR, (buf * 32767).astype(np.int16))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af", "loudnorm=I=-14:TP=-1.2:LRA=8", "-ar", str(SR), ruta],
                   check=True)
    return ruta


def main():
    global ESCENAS
    ESCENAS = armar()
    Path("videos_salida").mkdir(exist_ok=True)
    if "--frames" in sys.argv:
        for s in [float(x) for x in sys.argv[sys.argv.index("--frames") + 1:]]:
            Image.fromarray(make_frame(s)).save(f"videos_salida/prev_{s:05.2f}.png")
        return
    wav = generar_audio()
    pista = AudioFileClip(wav)
    video = VideoClip(make_frame, duration=DUR).with_audio(pista.subclipped(0, min(DUR, pista.duration)))
    video.write_videofile(SALIDA, fps=FPS, codec="libx264", audio_codec="aac", audio_bitrate="192k", preset="medium",
                          ffmpeg_params=["-crf", "19", "-pix_fmt", "yuv420p", "-movflags", "+faststart"])
    print("Listo:", SALIDA)


if __name__ == "__main__":
    main()
