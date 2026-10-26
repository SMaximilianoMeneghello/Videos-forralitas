"""Promo "¡Llegó maíz!" (vertical 1080x1920, ~47 s) a partir del video real de la tolva.

Sin música ni efectos ni audio original: solo voz en off y subtítulos sincronizados.

Uso:
    python maiz_promo.py                   # genera videos_salida/maiz_promo.mp4
    python maiz_promo.py --frames 1 9 30   # vistas previas
"""
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from moviepy import AudioFileClip, VideoClip
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

import voz_tts
from efectos import (blit, caja, clamp01, desde_pil, ease_in_out, ease_out_back, ease_out_cubic, icono,
                     logo_redondo, prog, sobre)

W, H, FPS = 1080, 1920, 30
SALIDA = "videos_salida/maiz_promo.mp4"
SRC = "assets/maiz/estabilizado.mp4"
INTER = "/usr/share/fonts/opentype/inter/"
BLK, XB = INTER + "Inter-Black.otf", INTER + "Inter-ExtraBold.otf"
MAIZ, ORO = (255, 200, 20), (232, 170, 30)
VERDE, VERDE_OSC, BLANCO, NEGRO = (28, 110, 52), (14, 64, 32), (255, 255, 255), (0, 0, 0)
VOZ, RATE, RATE_FINAL = "es-AR-TomasNeural", "-4%", "-4%"
SR = voz_tts.SR

# ------------------------------------------------------------ guion (la voz dice exactamente esto)
# Cada línea: (inicio, texto para la voz, [(subtítulo, cantidad de palabras de la voz que cubre)])
# En los subtítulos, *palabra* = resaltada en amarillo.
GUION = {
    "L1": (1.2, "¡Llegó maíz de primera calidad a nuestra forrajería, Forralitas!",
           [("¡Llegó *maíz*", 2), ("de *primera calidad*", 3), ("a nuestra forrajería,", 3), ("*Forralitas!*", 1)]),
    "L2": (9.6, "Tenemos bolsas de cuarenta y de cincuenta kilos.",
           [("Tenemos bolsas", 2), ("de *40* y de *50 kilos*.", 6)]),
    "L3a": (17.0, "Te esperamos con los mejores productos al mejor precio.",
            [("Te esperamos", 2), ("con los *mejores productos*", 4), ("al *mejor precio*.", 3)]),
    "L3b": (21.0, "¡Visitanos!", [("*¡Visitanos!*", 1)]),
    "F1": (26.8, "Estamos en Ruta trescientos cinco, kilómetro siete coma cinco, Las Talitas.",
           [("Estamos en *Ruta 305*,", 5), ("kilómetro *7,5*,", 4), ("*Las Talitas*.", 2)]),
    "F2": (None, "Llamanos al tres ocho uno, cinco dos seis, nueve cero cero cuatro, "
                 "o al tres ocho uno, seis tres tres, cuatro tres cuatro cuatro.",
           [("Llamanos al", 2), ("*381 526 9004*", 10), ("o al", 2), ("*381 633 4344*.", 10)]),
    "F7": (None, "Forralitas, Forrajería y Semillería.", [("*Forralitas*,", 1), ("Forrajería y Semillería.", 3)]),
}
# tramos de imagen (inicio, fin) y tomas del original (segundo inicial, duración, factor de cámara lenta)
T_INTRO, T_PRES, T_TOLVA, T_MANOS, T_PLACA = (0, 8), (8, 16), (16, 22), (22, 26), (26, None)
TOMAS = {"A1": (0.0, 4.0, 2.0), "C": (18.3, 4.0, 2.0), "B": (12.0, 4.0, 1.5), "A2": (4.0, 2.0, 2.0)}
TR = 0.4


# ------------------------------------------------------------ voz
def preparar_voz():
    lineas = {}
    for k, (t0, txt, chunks) in GUION.items():
        voz_tts.VOZ = VOZ
        x, tiempos = voz_tts.clip_palabras(txt, voz=VOZ, rate=RATE_FINAL if k.startswith("F") else RATE)
        assert sum(n for _, n in chunks) == len(txt.split()), k
        lineas[k] = {"audio": x, "tiempos": tiempos, "dur": len(x) / SR, "chunks": chunks, "inicio": t0}
    # la placa: cada dato leído entra cuando se lo nombra
    lineas["F2"]["inicio"] = lineas["F1"]["inicio"] + lineas["F1"]["dur"] + 0.6
    fin_f2 = lineas["F2"]["inicio"] + lineas["F2"]["dur"]
    lineas["F7"]["inicio"] = fin_f2 + 2.4          # antes entran, de a uno, los demás datos de la placa
    return lineas


def subtitulos(lineas):
    subs = []
    for k, L in lineas.items():
        idx = 0
        starts = []
        for txt, n in L["chunks"]:
            starts.append((L["inicio"] + L["tiempos"][idx] - 0.05, txt))
            idx += n
        for i, (s, txt) in enumerate(starts):
            e = starts[i + 1][0] if i + 1 < len(starts) else L["inicio"] + L["dur"] + 0.35
            subs.append((s, e, txt))
    return sorted(subs)


def t_palabra(L, palabra):
    pal = [w.strip("¡!¿?,.:").lower() for w in GUION_TXT(L).split()]
    return L["inicio"] + L["tiempos"][pal.index(palabra)]


def GUION_TXT(L):
    for k, (t0, txt, ch) in GUION.items():
        if ch is L["chunks"]:
            return txt


# ------------------------------------------------------------ material de video
def preparar_tomas():
    tomas = {}
    for k, (ss, dur, lento) in TOMAS.items():
        ruta = f"assets/maiz/toma_{k}.mp4"
        if not Path(ruta).exists():
            fps_mi = int(30 * lento)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(ss), "-t", str(dur), "-i", SRC, "-an", "-vf",
                            f"minterpolate=fps={fps_mi}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,"
                            f"setpts={lento}*PTS", "-r", "30", "-c:v", "libx264", "-crf", "12", ruta], check=True)
        cap = cv2.VideoCapture(ruta)
        fr = []
        while True:
            ok, f = cap.read()
            if not ok:
                break
            fr.append(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))
        tomas[k] = fr
    return tomas


_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
_R = np.hypot(_xx - W / 2, _yy - H / 2) / np.hypot(W / 2, H / 2)
VIGNETA = (1 - 0.38 * _R ** 2.2)[..., None].astype(np.float32)


def corregir_color(img):
    x = img.astype(np.float32) / 255
    x *= np.array([1.07, 1.02, 0.86], np.float32)                     # más cálido
    g = x.mean(2, keepdims=True)
    calido = np.clip((x[..., :1] - x[..., 2:3]) * 3, 0, 1)            # zonas amarillas/naranjas
    x = g + (x - g) * (1.25 + 0.3 * calido)                             # saturación, más en el maíz
    x = np.clip(x, 0, 1)
    x = 0.7 * x + 0.3 * (x * x * (3 - 2 * x))                           # contraste (curva S)
    bl = cv2.GaussianBlur(x, (0, 0), 2.2)
    x = x + 0.7 * (x - bl)                                              # nitidez
    x = x * VIGNETA
    return np.clip(x * 255, 0, 255).astype(np.uint8)


def encuadre(frame, cx, cy, w):
    """Recorta un rectángulo 9:16 de ancho w centrado en (cx, cy) y lo lleva a 1080x1920."""
    h = w * 16 / 9
    x0, y0 = cx - w / 2, cy - h / 2
    s = W / w
    M = np.array([[s, 0, -x0 * s], [0, s, -y0 * s]], np.float32)
    return cv2.warpAffine(frame, M, (W, H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT)


def cuadro(tomas, k, t_local):
    fr = tomas[k]
    return fr[int(np.clip(t_local * FPS, 0, len(fr) - 1))]


def ken_burns(a, b, p):
    e = ease_in_out(p)
    return tuple(a[i] + (b[i] - a[i]) * e for i in range(3))


# ------------------------------------------------------------ texto
def fuente(ruta, tam):
    return ImageFont.truetype(ruta, tam)


def sprite_texto(partes, tam, ruta=BLK, trazo=8, color_trazo=NEGRO, sombra=True):
    """partes: [(texto, color)]. Texto con borde y sombra, como sprite premultiplicado."""
    f = fuente(ruta, tam)
    anchos = [f.getlength(t) for t, _ in partes]
    pad = trazo + 30
    w, h = int(sum(anchos)) + 2 * pad, int(tam * 1.35) + 2 * pad
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = pad
    for (t, c), a in zip(partes, anchos):
        d.text((x, pad), t, font=f, fill=c + (255,), stroke_width=trazo, stroke_fill=color_trazo + (255,))
        x += a
    if sombra:
        a = im.getchannel("A").filter(ImageFilter.GaussianBlur(10))
        s = Image.new("RGBA", im.size, (0, 0, 0, 0))
        s.putalpha(a.point(lambda v: int(v * 0.6)))
        base = Image.new("RGBA", im.size, (0, 0, 0, 0))
        base.alpha_composite(s, (6, 10))
        base.alpha_composite(im)
        im = base
    return desde_pil(im)


def tam_que_entra(txt, tam, ruta, max_w):
    while fuente(ruta, tam).getlength(txt) > max_w and tam > 20:
        tam -= 2
    return tam


def partes_marcadas(txt):
    partes, dentro, buf = [], False, ""
    for ch in txt:
        if ch == "*":
            if buf:
                partes.append((buf, MAIZ if dentro else BLANCO))
            buf, dentro = "", not dentro
        else:
            buf += ch
    if buf:
        partes.append((buf, MAIZ if dentro else BLANCO))
    return partes


_cache_sub = {}


def sprite_sub(txt, tam=66, max_w=980):
    if txt in _cache_sub:
        return _cache_sub[txt]
    f = fuente(BLK, tam)
    plano = txt.replace("*", "")
    if f.getlength(plano) <= max_w:
        spr = sprite_texto(partes_marcadas(txt), tam, BLK, 8)
    else:                                   # dos líneas equilibradas
        pal = txt.split(" ")
        mejor = min(range(1, len(pal)), key=lambda i: abs(f.getlength(" ".join(pal[:i]).replace("*", "")) -
                                                          f.getlength(" ".join(pal[i:]).replace("*", ""))))
        l1, l2 = " ".join(pal[:mejor]), " ".join(pal[mejor:])
        # mantener abiertos/cerrados los asteriscos en cada línea
        if l1.count("*") % 2:
            l1, l2 = l1 + "*", "*" + l2
        s1, s2 = sprite_texto(partes_marcadas(l1), tam, BLK, 8), sprite_texto(partes_marcadas(l2), tam, BLK, 8)
        w = max(s1.shape[1], s2.shape[1])
        out = np.zeros((s1.shape[0] + s2.shape[0] - 70, w, 4), np.float32)
        out = sobre(out, s1, (w - s1.shape[1]) // 2, 0)
        out = sobre(out, s2, (w - s2.shape[1]) // 2, s1.shape[0] - 70)
        spr = out
    _cache_sub[txt] = spr
    return spr


def pastilla(txt, tam, fondo, color, ruta=XB, padx=40, alto=None):
    t = sprite_texto([(txt, color)], tam, ruta, 0, sombra=False)
    tw = t.shape[1] - 2 * 30
    alto = alto or int(tam * 1.6)
    base = caja(tw + 2 * padx, alto, alto // 2, fondo)
    borde = caja(tw + 2 * padx + 8, alto + 8, alto // 2 + 4, MAIZ)
    base = sobre(borde, base, 4, 4)
    return sobre(base, t, padx + 4 - 30, (alto + 8 - t.shape[0]) // 2 + 2)


# ------------------------------------------------------------ brillos dorados
def _estrella(l=110):
    y, x = np.mgrid[0:l, 0:l].astype(np.float32) - l / 2
    r = np.hypot(x, y) + 1e-3
    rayo = np.exp(-np.abs(x) / 1.6) * np.exp(-np.abs(y) / (l * 0.22)) + np.exp(-np.abs(y) / 1.6) * np.exp(-np.abs(x) / (l * 0.22))
    nucleo = np.exp(-(r / 6) ** 2)
    halo = np.exp(-(r / (l * 0.18)) ** 2) * 0.35
    a = np.clip(rayo + nucleo + halo, 0, 1)
    col = np.array([255, 236, 170], np.float32)
    return a[..., None] * col


ESTRELLA = _estrella()


def brillos(f, t, zona, n, semilla, op=1.0):
    """Destellos dorados que titilan dentro de zona=(x0, y0, x1, y1)."""
    if op <= 0:
        return f
    rng = np.random.default_rng(semilla)
    out = f.astype(np.float32)
    x0, y0, x1, y1 = zona
    for _ in range(n):
        cx, cy = rng.uniform(x0, x1), rng.uniform(y0, y1)
        per, fase, esc = rng.uniform(1.2, 2.4), rng.uniform(0, 6.28), rng.uniform(0.6, 1.3)
        a = max(0.0, np.sin(t * 2 * np.pi / per + fase)) ** 3 * op
        if a < 0.02:
            continue
        l = max(8, int(ESTRELLA.shape[0] * esc))
        e = cv2.resize(ESTRELLA, (l, l))
        xa, ya = int(cx - l / 2), int(cy - l / 2)
        xa0, ya0, xa1, ya1 = max(xa, 0), max(ya, 0), min(xa + l, W), min(ya + l, H)
        if xa0 >= xa1 or ya0 >= ya1:
            continue
        out[ya0:ya1, xa0:xa1] += e[ya0 - ya:ya1 - ya, xa0 - xa:xa1 - xa] * a
    return np.clip(out, 0, 255).astype(np.uint8)


def destello(f, t, t0, dur=0.35, op=0.85, color=(255, 240, 200)):
    q = (t - t0) / dur
    if 0 <= q <= 1:
        a = op * (1 - q) ** 1.5 if q > 0.15 else op * q / 0.15
        f = cv2.addWeighted(f, 1 - a, np.full_like(f, color), a, 0)
    return f


# ------------------------------------------------------------ escenas
class Escenas:
    def __init__(self, tomas, lineas):
        self.tomas, self.L = tomas, lineas
        # títulos
        txt = "¡LLEGÓ MAÍZ!"
        tam = tam_que_entra(txt, 168, BLK, 980)
        self.llego = [sprite_texto([(c, MAIZ)], tam, BLK, 12, VERDE_OSC) for c in txt]
        f = fuente(BLK, tam)
        x0 = (W - f.getlength(txt)) / 2
        self.llego_x = [x0 + f.getlength(txt[:i]) + f.getlength(c) / 2 for i, c in enumerate(txt)]
        self.calidad = pastilla("de primera calidad", 60, VERDE, BLANCO)
        self.bolsas = sprite_texto([("Bolsas de", BLANCO)], 104, BLK, 10, VERDE_OSC)
        self.b40 = pastilla("40 kg", 104, VERDE, MAIZ, BLK, 46)
        self.y_ = sprite_texto([("y", BLANCO)], 90, BLK, 10, VERDE_OSC)
        self.b50 = pastilla("50 kg", 104, VERDE, MAIZ, BLK, 46)
        self.mejores = sprite_texto([("LOS MEJORES PRODUCTOS", BLANCO)], tam_que_entra("LOS MEJORES PRODUCTOS", 92, BLK, 980), BLK, 10, VERDE_OSC)
        self.punto = caja(26, 26, 13, MAIZ)
        self.precio = sprite_texto([("AL MEJOR PRECIO", MAIZ)], tam_que_entra("AL MEJOR PRECIO", 112, BLK, 980), BLK, 11, VERDE_OSC)
        self.placa = Placa(lineas)

    # -------- tomas
    def intro(self, t):
        p = t / 8
        cx, cy, w = ken_burns((305, 270, 300), (305, 265, 250), p)
        zoom_rapido = 1 + 0.6 * (1 - ease_out_cubic(clamp01(t / 0.7)))
        img = encuadre(cuadro(self.tomas, "A1", t), cx, cy, w / zoom_rapido)
        f = corregir_color(img)
        f = brillos(f, t, (250, 500, 900, 1300), 9, 1, op=clamp01((t - 0.4) * 2))
        # ¡LLEGÓ MAÍZ! letra por letra con rebote
        for i, (s, x) in enumerate(zip(self.llego, self.llego_x)):
            q = prog(t, 0.45 + 0.05 * i, 0.45)
            if q > 0:
                blit(f, s, x, 330 - (1 - ease_out_cubic(q)) * 140, alpha=clamp01(q * 3),
                     escala=max(ease_out_back(q, 2.2), 0.01), centro=True)
        q = prog(t, 1.35, 0.5)
        blit(f, self.calidad, W / 2, 500 + (1 - ease_out_cubic(q)) * 60, alpha=clamp01(q * 3),
             escala=max(ease_out_back(q, 1.8), 0.01), centro=True)
        return destello(f, t, 0.0, 0.5, 0.9)

    def presentacion(self, t):
        p = t / 8
        cx, cy, w = ken_burns((285, 310, 300), (290, 322, 262), p)
        f = corregir_color(encuadre(cuadro(self.tomas, "C", t), cx, cy, w))
        L2 = self.L["L2"]
        t40, t50 = t_palabra(L2, "cuarenta") - T_PRES[0], t_palabra(L2, "cincuenta") - T_PRES[0]
        q = prog(t, 0.45, 0.5)
        blit(f, self.bolsas, W / 2 - (1 - ease_out_cubic(q)) * 900, 300, alpha=clamp01(q * 3), centro=True)
        for spr, x, t0 in ((self.b40, 300, min(t40, 1.0)), (self.y_, 540, min(t40, 1.0) + 0.2), (self.b50, 780, min(t50, 1.25))):
            q = prog(t, t0, 0.45)
            blit(f, spr, x, 470, alpha=clamp01(q * 3), escala=max(ease_out_back(q, 2.4), 0.01), centro=True)
        f = brillos(f, t, (200, 420, 880, 520), 3, 5, op=clamp01(t - 1.6) * 0.8)
        return f

    def tolva(self, t):
        p = t / 6
        cx, cy, w = ken_burns((300, 268, 232), (302, 272, 168), p)
        f = corregir_color(encuadre(cuadro(self.tomas, "B", t), cx, cy, w))
        f = brillos(f, t, (120, 520, 960, 1500), 16, 11, op=1.0)
        L3 = self.L["L3a"]
        tm, tp = t_palabra(L3, "mejores") - T_TOLVA[0], t_palabra(L3, "precio") - T_TOLVA[0] - 0.35
        q = prog(t, tm - 0.15, 0.5)
        blit(f, self.mejores, W / 2 - (1 - ease_out_cubic(q)) * 1000, 300, alpha=clamp01(q * 3), centro=True)
        q = prog(t, tp - 0.15, 0.3)
        blit(f, self.punto, W / 2, 390, alpha=clamp01(q * 3), escala=max(ease_out_back(q, 2.5), 0.01), centro=True)
        q = prog(t, tp, 0.5)
        blit(f, self.precio, W / 2 + (1 - ease_out_cubic(q)) * 1000, 480, alpha=clamp01(q * 3), centro=True)
        return f

    def manos(self, t):
        p = t / 4
        cx, cy, w = ken_burns((305, 270, 275), (305, 282, 232), p)
        f = corregir_color(encuadre(cuadro(self.tomas, "A2", t), cx, cy, w))
        f = brillos(f, t, (250, 500, 900, 1300), 7, 21, op=0.8)
        blit(f, self.mejores, W / 2, 300, centro=True)
        blit(f, self.punto, W / 2, 390, centro=True)
        blit(f, self.precio, W / 2, 480, centro=True)
        return f

    def placa_final(self, t):
        return self.placa.render(self.tomas, t)


# ------------------------------------------------------------ placa final
class Placa:
    def __init__(self, L):
        self.L = L
        t0 = T_PLACA[0]
        self.t_ruta = L["F1"]["inicio"] - t0 - 0.1
        self.t_tel = L["F2"]["inicio"] - t0 - 0.1
        fin_f2 = L["F2"]["inicio"] + L["F2"]["dur"] - t0
        self.t_otros = [fin_f2 + 0.2 + 0.5 * i for i in range(4)]
        self.t_firma = L["F7"]["inicio"] - t0
        self.logo = logo_redondo(200)
        self.nombre = sprite_texto([("FORRALITAS", VERDE_OSC)], 92, BLK, 0, sombra=False)
        self.rubro = sprite_texto([("Forrajería y Semillería", ORO)], 46, XB, 0, sombra=False)
        filas = [("ubicacion", ["Ruta 305, km 7,5 – Las Talitas"], 46, self.t_ruta),
                 ("telefono", ["381 526 9004", "381 633 4344"], 60, self.t_tel),
                 ("reloj", ["Lunes a viernes 8:00 a 19:00", "Sábados 8:30 a 19:00"], 42, self.t_otros[0]),
                 ("camion", ["Envíos según la zona"], 44, self.t_otros[1]),
                 ("tienda", ["Venta por mayor y menor"], 44, self.t_otros[2]),
                 ("efectivo", ["Todos los medios de pago", "Efectivo · Transferencia · Débito · Crédito"], 40, self.t_otros[3])]
        self.filas = []
        for ic, lineas, tam, t_in in filas:
            h = 112 if len(lineas) == 1 else (170 if ic == "telefono" else 156)
            base = caja(880, h, 30, (246, 242, 228))
            base = sobre(base, icono(ic, 86, MAIZ, VERDE_OSC), 18, (h - 86) // 2)
            y = (h - len(lineas) * int(tam * 1.18)) // 2
            for j, l in enumerate(lineas):
                igual = ic == "telefono"
                tt = tam if (j == 0 or igual) else int(tam * 0.82)
                f = fuente(BLK if (j == 0 or igual) else XB, tt)
                while f.getlength(l) > 740 and tt > 20:
                    tt -= 2
                    f = fuente(BLK if (j == 0 or igual) else XB, tt)
                s = sprite_texto([(l, VERDE_OSC if (j == 0 or igual) else VERDE)], tt, BLK if (j == 0 or igual) else XB, 0, sombra=False)
                base = sobre(base, s, 124 - 30, y - 30 + j * int(tam * 1.18))
            resalte = caja(880, h, 30, MAIZ, 0.55)
            self.filas.append((base, resalte, h, t_in))
        self.card_h = 330 + sum(h for _, _, h, _ in self.filas) + 16 * (len(self.filas) - 1) + 40
        self.card = caja(960, self.card_h, 48, (255, 253, 247), 0.97)

    def fondo(self, tomas, t):
        fr = tomas["B"]
        n = len(fr)
        k = int(t * FPS * 0.5) % (2 * n - 2)
        k = k if k < n else 2 * n - 2 - k                                   # ida y vuelta
        img = encuadre(fr[k], 300, 270, 232 - 10 * np.sin(t * 0.2))
        img = cv2.resize(cv2.GaussianBlur(cv2.resize(img, (270, 480)), (0, 0), 6), (W, H))
        img = corregir_color(img).astype(np.float32) * 0.45
        return img.astype(np.uint8)

    def render(self, tomas, t):
        f = self.fondo(tomas, t)
        f = brillos(f, t, (0, 0, W, H), 14, 33, op=0.45)
        y0 = 310
        q = prog(t, 0.15, 0.6)
        e = ease_out_back(q, 1.3)
        blit(f, self.card, W / 2, y0 + self.card_h / 2 + (1 - e) * 300, alpha=clamp01(q * 3), centro=True)
        if q <= 0:
            return f
        dy = (1 - e) * 300
        firma = clamp01((t - self.t_firma) / 0.3) * (1 - clamp01((t - self.t_firma - 1.6) / 0.6))
        ql = prog(t, 0.35, 0.6)
        pul = 1 + 0.08 * np.sin(np.pi * clamp01((t - self.t_firma) / 0.6)) * (t > self.t_firma)
        blit(f, self.logo, W / 2, y0 + dy, alpha=clamp01(ql * 3), escala=max(ease_out_back(ql, 1.8), 0.01) * pul, centro=True)
        qn = prog(t, 0.5, 0.5)
        blit(f, self.nombre, W / 2, y0 + 160 + dy, alpha=clamp01(qn * 3), escala=(0.8 + 0.2 * ease_out_back(qn, 1.6)) * pul,
             centro=True)
        blit(f, self.rubro, W / 2, y0 + 238 + dy, alpha=clamp01(qn * 3), centro=True)
        if firma > 0:
            f = brillos(f, t, (200, y0 + 100, 880, y0 + 280), 6, 44, op=firma)
        cv2.line(f, (int(W / 2 - 300 * ease_out_cubic(qn)), int(y0 + 290 + dy)),
                 (int(W / 2 + 300 * ease_out_cubic(qn)), int(y0 + 290 + dy)), MAIZ, 4, cv2.LINE_AA)
        y = y0 + 320
        for base, resalte, h, t_in in self.filas:
            qf = prog(t, t_in, 0.55)
            if qf > 0:
                ef = ease_out_back(qf, 1.4)
                x = 100 + (1 - ef) * 1000
                blit(f, base, x, y + dy, alpha=clamp01(qf * 3))
                r = clamp01((t - t_in) / 0.15) * (1 - clamp01((t - t_in - 0.6) / 0.6))
                if r > 0:
                    blit(f, resalte, x, y + dy, alpha=r * 0.6)
            y += h + 16
        return f


# ------------------------------------------------------------ transiciones
def zoom_blur(img, amt, n=6):
    if amt < 0.004:
        return img
    acc = np.zeros(img.shape, np.float32)
    for i in range(n):
        s = 1 + amt * i / (n - 1)
        M = np.array([[s, 0, (1 - s) * W / 2], [0, s, (1 - s) * H / 2]], np.float32)
        acc += cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REPLICATE)
    return (acc / n).astype(np.uint8)


def tr_barrido(a, b, p):
    e = ease_in_out(p)
    off = int(e * W)
    out = np.empty_like(a)
    out[:, :W - off] = a[:, off:]
    out[:, W - off:] = b[:, :off]
    k = int(1 + 140 * np.sin(np.pi * p))
    k += (k % 2 == 0)
    return cv2.blur(out, (k, 1)) if k > 1 else out


def tr_destello(a, b, p):
    e = ease_in_out(p)
    A, B = zoom_blur(a, 0.3 * e), zoom_blur(b, 0.2 * (1 - e))
    out = cv2.addWeighted(A, 1 - e, B, e, 0)
    fl = 0.55 * np.exp(-((p - 0.5) / 0.16) ** 2)
    return cv2.addWeighted(out, 1 - fl, np.full_like(out, (255, 238, 190)), fl, 0)


def tr_deslizar(a, b, p):
    e = ease_in_out(p)
    off = int(e * H)
    out = np.empty_like(a)
    out[:H - off] = a[off:]
    out[H - off:] = b[:off]
    k = int(1 + 60 * np.sin(np.pi * p))
    k += (k % 2 == 0)
    return cv2.blur(out, (1, k)) if k > 1 else out


def tr_zoom_entrada(a, b, p):
    e = ease_in_out(p)
    M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, 1 + 0.8 * e)
    A = zoom_blur(cv2.warpAffine(a, M, (W, H), borderMode=cv2.BORDER_REFLECT), 0.35 * e)
    return cv2.addWeighted(A, 1 - e, b, e, 0)


# ------------------------------------------------------------ montaje
class Video:
    def __init__(self):
        self.L = preparar_voz()
        fin_voz = self.L["F7"]["inicio"] + self.L["F7"]["dur"]
        self.dur = round(fin_voz + 2.0, 2)
        self.tramos = [(T_INTRO, "intro"), (T_PRES, "presentacion"), (T_TOLVA, "tolva"), (T_MANOS, "manos"),
                       ((T_PLACA[0], self.dur), "placa_final")]
        self.trans = [tr_barrido, tr_destello, tr_deslizar, tr_zoom_entrada]
        self.tomas = preparar_tomas()
        self.esc = Escenas(self.tomas, self.L)
        self.subs = subtitulos(self.L)

    def escena(self, i, t):
        (a, b), nombre = self.tramos[i]
        return getattr(self.esc, nombre)(t - a)

    def frame(self, t):
        t = min(t, self.dur - 1e-3)
        f = None
        for i, ((a, b), _) in enumerate(self.tramos[:-1]):
            if b - TR / 2 <= t < b + TR / 2:                                  # transición
                ta = min(t, b - 1e-3)
                f = self.trans[i](self.escena(i, ta), self.escena(i + 1, max(t, b)), (t - (b - TR / 2)) / TR)
                break
        if f is None:
            i = max(k for k, ((a, b), _) in enumerate(self.tramos) if t >= a)
            f = self.escena(i, t)
        # subtítulos
        en_placa = t >= T_PLACA[0]
        y_sub = 1690 if en_placa else 1500
        for s, e, txt in self.subs:
            if s <= t < e:
                q = prog(t, s, 0.18)
                sale = clamp01((e - t) / 0.12)
                blit(f, sprite_sub(txt, 60 if en_placa else 70), W / 2, y_sub, alpha=clamp01(q * 3) * sale,
                     escala=0.85 + 0.15 * ease_out_back(q, 2.0), centro=True)
        return f

    def audio(self, ruta="videos_salida/_maiz_voz.wav"):
        n = int(self.dur * SR)
        voz = np.zeros(n, np.float32)
        for L in self.L.values():
            x = L["audio"] * (10 ** (-18 / 20) / (np.sqrt((L["audio"] ** 2).mean()) + 1e-9))
            i = int(L["inicio"] * SR)
            voz[i:i + x.size] += x[:max(0, n - i)]
        voz = sosfilt(butter(2, 70, btype="highpass", fs=SR, output="sos"), voz)
        voz *= 0.9 / np.abs(voz).max()
        tmp = "videos_salida/_maiz_voz_crudo.wav"
        wavfile.write(tmp, SR, (voz * 32767).astype(np.int16))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af", "loudnorm=I=-16:TP=-1.5:LRA=7", "-ac", "2",
                        "-ar", str(SR), ruta], check=True)
        return ruta


def main():
    v = Video()
    Path("videos_salida").mkdir(exist_ok=True)
    print("duración:", v.dur, "| voz:", {k: (round(L["inicio"], 2), round(L["dur"], 2)) for k, L in v.L.items()})
    if "--frames" in sys.argv:
        for s in [float(x) for x in sys.argv[sys.argv.index("--frames") + 1:]]:
            Image.fromarray(v.frame(s)).save(f"videos_salida/prev_{s:05.2f}.png")
        return
    wav = v.audio()
    pista = AudioFileClip(wav)
    clip = VideoClip(v.frame, duration=v.dur).with_audio(pista.subclipped(0, min(v.dur, pista.duration)))
    clip.write_videofile(SALIDA, fps=FPS, codec="libx264", audio_codec="aac", audio_bitrate="160k", preset="medium",
                         ffmpeg_params=["-crf", "19", "-pix_fmt", "yuv420p", "-movflags", "+faststart"])
    print("Listo:", SALIDA)


if __name__ == "__main__":
    main()
