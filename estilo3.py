"""Video Forralitas, estilo "afiche nocturno": fondo oscuro, tipografía gigante y una lista que se marca
al nombrar cada producto. Una escena por animal (caballos, cerdos, gallinas, perros y gatos).

Uso:
    python estilo3.py                  # genera videos_salida/forralitas_afiche.mp4
    python estilo3.py --frames 2 6 12  # vistas previas
    python estilo3.py --audio          # solo el audio mezclado

Fotos: ver ANIMALES (abajo). Datos de contacto, horarios y pagos: CONFIG en crear_video.py.
La voz va rápida (VELOCIDAD) y cada ítem se ilumina justo cuando se lo nombra.
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from moviepy import AudioFileClip, VideoClip
from PIL import Image

import audio
import audio_suave
import crear_video as cv
import estilo2 as e2
import estilo_voz as ev
import voz_tts
from efectos import (DIAGONAL, H, W, ancho_texto, blit, caja, clamp01, ease_in_out, ease_out_back,
                     ease_out_cubic, icono, logo_redondo, prog, rotar_sprite, sobre, texto)

FPS = 30
TR = 0.5
SR = voz_tts.SR
VELOCIDAD = "+32%"
SALIDA = "videos_salida/forralitas_afiche.mp4"
PAD = cv.PAD
N, P = "assets/nuevas/", "fotos_presentacion/"
BLACK = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
XB = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
SB = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
BLANCO, OSCURO, TARJ = (255, 255, 255), (10, 26, 18), (8, 30, 20)
AMARILLO = (255, 213, 64)
NOCHE1, NOCHE2 = (16, 46, 31), (4, 14, 9)

# nombre, línea 1, línea 2, foto del animal, acento, texto dicho, ítems (título, subtítulo, foto)
ANIMALES = [
    ("caballos", "¿PARA", "CABALLOS?", N + "n03.png", (255, 176, 46), "¿Para caballos?",
     [("Alfa", "", "alfa", N + "n08.jpg"),
      ("Pellet de trigo", "Bolsa x 30 kg y suelto", "pélet de trigo, bolsa por treinta kilos y suelto", N + "n12.jpg"),
      ("Mezcla de caballo preparada", "Bolsa x 35 kg y suelto",
       "mezcla de caballo preparada, bolsa por treinta y cinco kilos y suelto", N + "n10.jpg"),
      ("Maíz quebrado", "Bolsa x 40 kg y suelto", "maíz quebrado, bolsa por cuarenta kilos y suelto", N + "n11.jpg"),
      ("Maíz entero", "", "maíz entero", P + "05_maiz_entero.jpg")]),
    ("cerdos", "¿PARA", "CERDOS?", N + "n02.png", (255, 120, 160), "¿Para cerdos?",
     [("Mezcla para cerdo preparada", "", "mezcla para cerdo preparada", P + "02_engorde_cerdo.jpg"),
      ("Pellet con maíz", "Bolsa x 30 kg y suelto", "pélet con maíz, bolsa por treinta kilos y suelto", N + "n09.jpg"),
      ("Engorde con harina de carne", "", "engorde con harina de carne", N + "harina_carne.jpg")]),
    ("gallinas", "¿PARA", "GALLINAS?", N + "n01.png", (255, 118, 84), "¿Para gallinas?",
     [("Ponedora", "Por bolsa y suelto", "ponedora, por bolsa y suelto", N + "n13.jpg"),
      ("Afrecho de maíz", "Por bolsa y suelto", "afrecho de maíz, por bolsa y suelto", N + "n14.jpg"),
      ("Recría", "", "recría", P + "11_iniciador_parrillero.jpg"),
      ("Terminador engorde", "", "terminador, engorde", P + "12_engorde_terminador.jpg")]),
    ("perros y gatos", "¿PARA", "PERROS Y GATOS?", "fotos/02_perros_gatos.jpg", (84, 196, 255), "¿Para perros y gatos?",
     [("Wenuy", "", "güenuy", N + "n05.png"),
      ("Sabrositos", "", "sabrositos", "fotos/01_perros_sabrositos.jpg"),
      ("Manada", "", "manada", "fotos/02_perros_gatos.jpg")]),
]
TXT_TODO = "Todo lo que buscás en un solo lugar y al mejor precio."
TXT_VISITA = "¿Qué esperás para visitarnos?"
TXT_SOMOS = "Somos Forralitas. Estamos ubicados en ruta trescientos cinco, kilómetro siete coma cinco, Las Talitas."
TXT_CIERRE = ("¡Te esperamos! Llamanos al tres ocho uno, cinco dos seis, nueve cero cero cuatro, "
              "o al tres ocho uno, seis tres tres, cuatro tres cuatro cuatro. "
              "De lunes a viernes de ocho a diecinueve horas, y sábados de ocho y media a diecinueve horas. "
              "Hacemos envíos según la zona. Venta por mayor y menor. "
              "Aceptamos todos los medios de pago: efectivo, transferencia, débito y crédito. "
              "Forralitas, todo para tus animales.")
FOCO_X = {"caballos": 0.92, "cerdos": 0.72, "gallinas": 0.7, "perros y gatos": 0.5}
SEC = []                         # (inicio, fin) de cada animal, para la barra superior


def T(txt, tam, color=BLANCO, ruta=XB, sombra=True):
    return texto(txt, tam, color, sombra, ruta)


def ajustar(txt, tam, ruta, max_w):
    while ancho_texto(txt, tam, ruta) > max_w and tam > 20:
        tam -= 2
    return tam


# ------------------------------------------------------------ fondo
def _degradado():
    t = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    return np.repeat(np.array(NOCHE1, np.float32) * (1 - t) + np.array(NOCHE2, np.float32) * t, W, axis=1)


_BASE = _degradado()
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
_R = np.hypot(_xx - W / 2, _yy - H / 2) / np.hypot(W / 2, H / 2)
_BASE = _BASE * (1 - 0.45 * _R ** 2)[..., None]
_DIAG4 = DIAGONAL[::4, ::4].copy()
_PUNTOS = np.random.default_rng(8).uniform(0, 1, (46, 4))


def fondo_noche(gt, acento):
    """Degradé oscuro con haces de luz diagonales y puntitos (luciérnagas) que suben."""
    f = _BASE.copy()
    luz = np.zeros(_DIAG4.shape, np.float32)
    span = float(_DIAG4.max()) + 900
    for k in range(3):
        pos = (gt * 85 + k * span / 3) % span - 450
        luz += np.exp(-(((_DIAG4 - pos) / 150) ** 2))
    luz = cv2.resize(luz, (W, H), interpolation=cv2.INTER_LINEAR)
    f += luz[..., None] * np.array(acento, np.float32) * 0.07
    f = np.clip(f, 0, 255).astype(np.uint8)
    ov = f.copy()
    for x, y, v, ph in _PUNTOS[:, :4]:
        cx = x * W + 30 * np.sin(gt * 0.8 + ph * 6)
        cy = (y * (H + 60) - gt * (40 + 70 * v)) % (H + 60) - 30
        cv2.circle(ov, (int(cx), int(cy)), int(3 + 6 * v), acento, -1, cv2.LINE_AA)
    return cv2.addWeighted(ov, 0.20, f, 0.80, 0)


def _mapa_oscuro():
    y = _yy / H
    base = np.clip(0.88 - 0.7 * np.clip((y - 0.18) / 0.45, 0, 1), 0.18, 1)
    return (base * (1 - 0.35 * _R ** 2))[..., None].astype(np.float32)


OSC_MAP = _mapa_oscuro()


# ------------------------------------------------------------ piezas
class Letras:
    """Texto gigante que entra letra por letra con rebote."""

    def __init__(self, txt, tam, color, ruta=BLACK, max_w=W - 70):
        self.tam = ajustar(txt, tam, ruta, max_w)
        self.sp = [T(c, self.tam, color, ruta) for c in txt]
        x0 = (W - ancho_texto(txt, self.tam, ruta)) / 2
        self.cx = [x0 + ancho_texto(txt[:i], self.tam, ruta) + ancho_texto(c, self.tam, ruta) / 2
                   for i, c in enumerate(txt)]
        self.vis = [c != " " for c in txt]
        self.alto = int(self.tam * 1.32 + 2 * PAD)

    def draw(self, f, y, t, t0, paso=0.035):
        for i, (s, cx) in enumerate(zip(self.sp, self.cx)):
            if not self.vis[i]:
                continue
            q = prog(t, t0 + paso * i, 0.45)
            blit(f, s, cx, y + self.alto / 2 - (1 - ease_out_cubic(q)) * 110, alpha=clamp01(q * 2.5),
                 escala=0.45 + 0.55 * ease_out_back(q, 2.0), centro=True)


def etiqueta(txt, tam, fondo, tinta, ruta=BLACK, padx=30):
    s = T(txt, tam, tinta, ruta, sombra=False)
    w = s.shape[1] - 2 * PAD + 2 * padx
    base = caja(w, int(tam * 1.25), int(tam * 0.3), fondo)
    return sobre(base, s, padx - PAD, int((tam * 1.25 - tam * 1.32) / 2) - PAD + 4)


def sprite_cabecera():
    logo = logo_redondo(84)
    n = T("FORRALITAS", 38, BLANCO, BLACK, sombra=False)
    r = T("Forrajería y Semillería", 22, (190, 220, 200), SB, sombra=False)
    base = np.zeros((96, 520, 4), np.float32)
    base = sobre(base, logo, 0, 6)
    base = sobre(base, n, 98 - PAD, -4)
    return sobre(base, r, 98 - PAD, 40)


CABECERA = sprite_cabecera()


def cabecera(f, t):
    q = ease_out_cubic(prog(t, 0.1, 0.5))
    blit(f, CABECERA, 56 - (1 - q) * 280, 84, alpha=q)


def tilde(f, cx, cy, r, p, color):
    """Tilde (check) que se dibuja progresivamente dentro de un círculo de radio r."""
    pts = np.array([(cx - 0.42 * r, cy + 0.02 * r), (cx - 0.1 * r, cy + 0.34 * r), (cx + 0.46 * r, cy - 0.32 * r)])
    if p <= 0:
        return
    seg = [np.linalg.norm(pts[1] - pts[0]), np.linalg.norm(pts[2] - pts[1])]
    rec = p * (seg[0] + seg[1])
    a = pts[0]
    if rec <= seg[0]:
        b = pts[0] + (pts[1] - pts[0]) * rec / seg[0]
        cv2.line(f, tuple(map(int, a)), tuple(map(int, b)), color, max(4, int(r * 0.2)), cv2.LINE_AA)
    else:
        cv2.line(f, tuple(map(int, pts[0])), tuple(map(int, pts[1])), color, max(4, int(r * 0.2)), cv2.LINE_AA)
        b = pts[1] + (pts[2] - pts[1]) * (rec - seg[0]) / seg[1]
        cv2.line(f, tuple(map(int, pts[1])), tuple(map(int, b)), color, max(4, int(r * 0.2)), cv2.LINE_AA)


FILA_H, FILA_GAP = 104, 8


def sprite_fila(nombre, sub, acento, activa):
    w = 960
    fondo = acento if activa else TARJ
    base = caja(w, FILA_H, 30, fondo, 1.0 if activa else 0.86)
    tinta = OSCURO if activa else BLANCO
    tinta_sub = (40, 55, 45) if activa else acento
    tam = ajustar(nombre, 46, XB, w - 190)
    ytxt = 5 if sub else int((FILA_H - tam * 1.32) / 2) + 2
    base = sobre(base, T(nombre, tam, tinta, XB, sombra=False), 112 - PAD, ytxt - PAD + 2)
    if sub:
        base = sobre(base, T(sub, 27, tinta_sub, SB, sombra=False), 112 - PAD, 58 - PAD + 4)
    # insignia circular
    ins = caja(60, 60, 30, OSCURO if activa else acento)
    return sobre(base, ins, 26, (FILA_H - 60) // 2)


class Ventana:
    """Ventana de foto del producto: cambia de foto con un deslizamiento cuando se nombra el siguiente."""

    def __init__(self, fotos, w, h, acento, inicios, fin):
        self.w, self.h, self.acento = w, h, acento
        self.vis = [e2.Visor(r, w, h, 1.12, 1.06) for r in fotos]
        self.ini = inicios
        self.fin = fin
        self.masc = e2.mascara_redonda(w, h, 42)
        self.aro = e2.caja(w + 20, h + 20, 50, acento)
        self.sombra = e2.sombra_de(self.masc, 60, 0.5, 20)
        rng = np.random.default_rng(len(fotos))
        self.cams = [(1.0 + 0.1 * rng.random(), 1.14 + 0.12 * rng.random(), (rng.random(), rng.random()),
                      (rng.random(), rng.random())) for _ in fotos]

    def _frame(self, k, t):
        fin = self.ini[k + 1] if k + 1 < len(self.ini) else self.fin
        p = clamp01((t - self.ini[k]) / max(fin - self.ini[k], 0.1))
        z0, z1, a, b = self.cams[k]
        return self.vis[k].frame(p, z0, z1, a, b)

    def dibujar(self, f, t, cy, entra):
        q = prog(t, entra, 0.7)
        if q <= 0:
            return
        k = max([i for i, s in enumerate(self.ini) if t >= s - 0.12] or [0])
        img = self._frame(k, t)
        if k > 0 and t < self.ini[k] + 0.4:
            e = ease_in_out(clamp01((t - (self.ini[k] - 0.12)) / 0.5))
            off = int(e * self.w)
            prev = self._frame(k - 1, self.ini[k] - 0.12)
            out = np.empty_like(img)
            out[:, :self.w - off] = prev[:, off:]
            out[:, self.w - off:] = img[:, :off]
            if 0 < off < self.w:
                x = self.w - off
                cv2.rectangle(out, (max(x - 7, 0), 0), (min(x + 7, self.w - 1), self.h), self.acento, -1)
            img = out
        e = ease_out_back(q, 1.25)
        esc, dy = 0.86 + 0.14 * e, (1 - ease_out_cubic(q)) * 260
        blit(f, self.sombra, W / 2, cy + 24 + dy, alpha=clamp01(q * 2), escala=esc, centro=True)
        blit(f, self.aro, W / 2, cy + dy, alpha=clamp01(q * 3), escala=esc, centro=True)
        blit(f, e2.recortar(img, self.masc), W / 2, cy + dy, alpha=clamp01(q * 3), escala=esc, centro=True)


# ------------------------------------------------------------ escenas
def escena_animal(idx, dur, g0, tiempos_items, fin_voz):
    nombre, l1, l2, foto, acento, _, items = ANIMALES[idx]
    fondo = e2.Visor(foto, W, H, 1.05, 1.04)
    kicker = T(l1, 62, acento, XB)
    animal = Letras(l2, 168, BLANCO, BLACK, max_w=W - 60)
    n = len(items)
    top_lista = 1580 - n * (FILA_H + FILA_GAP)
    h_win = int(min(top_lista - 30 - 470, 640))
    cy_win = top_lista - 30 - h_win / 2
    win = Ventana([it[3] for it in items], 900, h_win, acento, tiempos_items, fin_voz)
    normal = [sprite_fila(it[0], it[1], acento, False) for it in items]
    activa = [sprite_fila(it[0], it[1], acento, True) for it in items]
    ini = tiempos_items
    fin_item = ini[1:] + [fin_voz]
    ejes = np.linspace(0, 1, n)

    def fn(t):
        gt = g0 + t
        f = fondo_noche(gt, acento)
        fx = FOCO_X[nombre]
        foto_f = fondo.frame(t / dur, 1.0, 1.22, (fx, 0.5), (fx, 0.3)).astype(np.float32)
        base = foto_f * OSC_MAP
        q = ease_out_cubic(prog(t, 0.0, 0.55))
        f = (f.astype(np.float32) * (1 - 0.88 * q) + base * 0.88 * q).astype(np.uint8)
        cabecera(f, t)
        # título
        qk = ease_out_cubic(prog(t, 0.15, 0.5))
        blit(f, kicker, 56 - (1 - qk) * 420, 215, alpha=qk)
        animal.draw(f, 262, t, 0.3)
        ql = ease_out_cubic(prog(t, 0.55, 0.6))
        cv2.rectangle(f, (60, 448), (60 + int(300 * ql), 458), acento, -1)
        # ventana de producto
        win.dibujar(f, t, cy_win, 0.45)
        # lista
        for i in range(n):
            y = top_lista + i * (FILA_H + FILA_GAP)
            qi = prog(t, ini[i] - 0.28, 0.5)
            if qi <= 0:
                continue
            e = ease_out_cubic(qi)
            x = 60 + (1 - e) * 1100
            blit(f, normal[i], x, y, alpha=clamp01(qi * 3))
            act = clamp01((t - (ini[i] - 0.05)) / 0.12) * (1 - clamp01((t - (fin_item[i] - 0.1)) / 0.2))
            if act > 0.01:
                blit(f, activa[i], x, y, alpha=act)
            tilde(f, x + 26 + 30, y + FILA_H / 2, 30, clamp01((t - (ini[i] + 0.05)) / 0.3),
                  OSCURO if act > 0.5 else (14, 30, 22))
        return f
    return fn


def escena_todo(dur, g0, tm):
    acento = AMARILLO
    fotos = [N + "n06.png", N + "n05.png", N + "n07.png"]
    ancho = W // 3
    tiras = [e2.Visor(r, ancho, H, 1.1, 1.05) for r in fotos]
    lineas = [Letras("TODO LO QUE", 112, BLANCO, BLACK), Letras("BUSCÁS", 190, acento, BLACK),
              Letras("EN UN SOLO LUGAR", 96, BLANCO, BLACK), Letras("Y AL MEJOR PRECIO", 80, acento, BLACK)]
    idx = [0, 3, 4, 8]
    ys = [610, 720, 960, 1090]
    sombra = np.zeros((H, W, 1), np.float32)
    sombra[:] = 0.4 + 0.45 * np.clip(1 - np.abs(_yy - 900) / 700, 0, 1)[..., None]

    def fn(t):
        gt = g0 + t
        f = fondo_noche(gt, acento)
        for i, v in enumerate(tiras):
            q = ease_out_cubic(prog(t, 0.05 + 0.12 * i, 0.7))
            tira = v.frame(t / dur, 1.0 + 0.1 * (i % 2), 1.25, (0.5, 0.2 + 0.3 * i), (0.5, 0.8 - 0.3 * i)).astype(np.float32)
            tira = (tira * (1 - 0.62 * sombra[:, :ancho])).astype(np.uint8)
            dy = int((1 - q) * H * (1 if i % 2 == 0 else -1))
            x0 = i * ancho
            if dy >= 0:
                f[dy:, x0 + 3:x0 + ancho - 3] = tira[:H - dy, 3:-3]
            else:
                f[:H + dy, x0 + 3:x0 + ancho - 3] = tira[-dy:, 3:-3]
        cabecera(f, t)
        for ln, y, ti in zip(lineas, ys, idx):
            ln.draw(f, y, t, tm[ti] - 0.05)
        return f
    return fn


def escena_visita(dur, g0, tm):
    acento = AMARILLO
    ancho_f = 1080
    visor = e2.Visor(N + "n04.png", ancho_f, 810, 1.1, 1.05)
    l1 = Letras("¿QUÉ ESPERÁS", 118, BLANCO, BLACK)
    l2 = Letras("PARA VISITARNOS?", 100, acento, BLACK)

    def fn(t):
        gt = g0 + t
        f = fondo_noche(gt, acento)
        q = ease_out_cubic(prog(t, 0.0, 0.7))
        img = visor.frame(t / dur, 1.0, 1.3, (0.35, 0.5), (0.6, 0.5))
        x0 = int((1 - q) * -W)
        y0 = 330
        if x0 < 0:
            f[y0:y0 + 810, :W + x0] = img[:, -x0:]
        else:
            f[y0:y0 + 810] = img
        edge = int(W + x0)
        cv2.rectangle(f, (max(edge - 12, 0), y0), (min(edge, W), y0 + 810), acento, -1)
        cv2.rectangle(f, (0, y0 - 10), (min(edge, W), y0), acento, -1)
        cv2.rectangle(f, (0, y0 + 810), (min(edge, W), y0 + 820), acento, -1)
        cabecera(f, t)
        l1.draw(f, 1210, t, tm[0] - 0.05)
        l2.draw(f, 1360, t, tm[2] - 0.05)
        return f
    return fn


def escena_somos(dur, g0, tm):
    acento = AMARILLO
    logo = logo_redondo(190)
    ventana = e2.VentanaDron("assets/dron/dron2.jpg", 960, 620)
    somos = etiqueta("SOMOS", 58, acento, OSCURO)
    nombre = Letras("FORRALITAS", 150, BLANCO, BLACK)
    pin = icono("ubicacion", 92, acento, OSCURO)
    est = T("ESTAMOS UBICADOS EN", 38, (200, 225, 210), XB, sombra=False)
    ruta = Letras("RUTA 305 KM 7,5", 100, acento, BLACK)
    tal = Letras("LAS TALITAS", 84, BLANCO, BLACK)

    def fn(t):
        gt = g0 + t
        f = fondo_noche(gt, acento)
        p = prog(t, tm[0], 0.7)
        blit(f, logo, W / 2, 190, alpha=clamp01(p * 3), escala=ease_out_back(p), centro=True)
        qs = prog(t, tm[0] - 0.05, 0.5)
        blit(f, somos, W / 2, 380 - (1 - ease_out_cubic(qs)) * 60, alpha=clamp01(qs * 3),
             escala=max(ease_out_back(qs, 2.0), 0.01), centro=True)
        nombre.draw(f, 430, t, tm[1] - 0.05, paso=0.05)
        qv = prog(t, tm[1] + 0.2, 0.9)
        sp = ventana.sprite(t, dur, 1.0, 1.7, (0.5, 0.5), (0.42, 0.58), 1.2, -0.8)
        e = ease_out_cubic(qv)
        ang = 1.1 * np.sin(t * 1.15)
        blit(f, e2.transformar(ventana.sombra, 1.0, ang), W / 2, 1000 + 24 + (1 - e) * 600, alpha=clamp01(qv * 3), centro=True)
        blit(f, e2.transformar(sp, 0.9 + 0.1 * e, ang), W / 2, 1000 + 7 * np.sin(t * 1.7) + (1 - e) * 600,
             alpha=clamp01(qv * 3), centro=True)
        qp = prog(t, tm[2] - 0.35, 0.7)
        blit(f, pin, W / 2, 1330 - (1 - ease_out_back(qp, 1.7)) * 240, alpha=clamp01(qp * 4), centro=True)
        qe = ease_out_cubic(prog(t, tm[2], 0.45))
        blit(f, est, (W - est.shape[1]) / 2, 1372 + (1 - qe) * 25, alpha=qe)
        ruta.draw(f, 1425, t, tm[5] - 0.05, paso=0.04)
        tal.draw(f, 1555, t, tm[12] - 0.05, paso=0.04)
        return f
    return fn


def escena_cierre(dur, g0, tm, cue):
    c = cv.CONFIG
    acento = AMARILLO
    logo = logo_redondo(170)
    tit = Letras("¡TE ESPERAMOS!", 112, BLANCO, BLACK, max_w=W - 80)
    fondo_t = lambda w, h: caja(w, h, 36, TARJ, 0.9)

    def lineas_tel():
        card = fondo_t(960, 250)
        card = sobre(card, T("LLAMANOS", 28, acento, XB, sombra=False), 190 - PAD, 14 - PAD)
        for k, num in enumerate(c["telefonos"]):
            tam = ajustar(num, 78, BLACK, 700)
            card = sobre(card, T(num, tam, BLANCO, BLACK, sombra=False), 190 - PAD, 56 + k * 90 - PAD)
        return card
    card_tel, ic_tel = lineas_tel(), icono("telefono", 124)

    card_hora = fondo_t(960, 200)
    for k, (lab, hor) in enumerate((("LUNES A VIERNES", "8:00 a 19:00"), ("SÁBADOS", "8:30 a 19:00"))):
        x = 180 + k * 400
        card_hora = sobre(card_hora, T(lab, 26, acento, XB, sombra=False), x - PAD, 32 - PAD)
        tam = ajustar(hor, 54, BLACK, 360)
        card_hora = sobre(card_hora, T(hor, tam, BLANCO, BLACK, sombra=False), x - PAD, 76 - PAD)

    def media(ic, l1, l2=None):
        card = fondo_t(470, 190)
        card = sobre(card, icono(ic, 84), 24, 53)
        tam = ajustar(l1, 42, BLACK, 330)
        card = sobre(card, T(l1, tam, BLANCO, BLACK, sombra=False), 126 - PAD, (36 if l2 else 62) - PAD)
        if l2:
            tam2 = ajustar(l2, 40, XB, 330)
            card = sobre(card, T(l2, tam2, (200, 225, 210), XB, sombra=False), 126 - PAD, 96 - PAD)
        return card
    card_ubic = media("ubicacion", c["direccion"][0].upper(), c["direccion"][1].upper())
    card_env = media("camion", "ENVÍOS", "SEGÚN LA ZONA")
    banner = etiqueta("VENTA POR MAYOR Y MENOR", 54, acento, OSCURO)
    titulo_pago = T("ACEPTAMOS TODOS LOS MEDIOS DE PAGO", 34, BLANCO, XB, sombra=False)
    tiles = []
    for nom, etq in zip(("efectivo", "transferencia", "debito", "credito"), c["pagos"]):
        card = fondo_t(225, 175)
        card = sobre(card, icono(nom, 82), (225 - 82) // 2, 18)
        tam = ajustar(etq.upper(), 26, XB, 205)
        t_ = T(etq.upper(), tam, BLANCO, XB, sombra=False)
        tiles.append(sobre(card, t_, (225 - (t_.shape[1] - 2 * PAD)) // 2 - PAD, 112 - PAD))
    firma1 = T("FORRALITAS", 76, BLANCO, BLACK)
    firma2 = T("Todo para tus animales", 36, acento, SB, sombra=False)
    y_tel, y_hora, y_med, y_ban, y_pago, y_tile = 470, 740, 960, 1176, 1310, 1380
    DIAG = DIAGONAL

    def entra(t, t0, d=0.6):
        q = prog(t, t0, d)
        return q, ease_out_cubic(q)

    def fn(t):
        gt = g0 + t
        f = fondo_noche(gt, acento)
        p = prog(t, 0.1, 0.8)
        blit(f, logo, W / 2, 175, alpha=clamp01(p * 3), escala=ease_out_back(p), centro=True)
        tit.draw(f, 285, t, cue["tit"], paso=0.04)
        # teléfonos
        q, e = entra(t, cue["tel"])
        x = 60 + (1 - e) * W
        blit(f, card_tel, x, y_tel, alpha=clamp01(q * 2.5))
        if q > 0:
            cx, cy = x + 100, y_tel + 125
            fase = (t - cue["tel"] - 0.4) % 1.7 if t >= cue["tel"] + 0.4 else 99
            env = max(0.0, 1 - fase / 0.6)
            for k in range(3 if env > 0 else 0):
                ov = f.copy()
                cv2.circle(ov, (int(cx), int(cy)), int(76 + 30 * k + fase * 100), acento, 4, cv2.LINE_AA)
                a_ = env * (1 - k * 0.28) * 0.7
                f[:] = cv2.addWeighted(ov, a_, f, 1 - a_, 0)
            ang = 20 * np.sin(fase * 52) * env if env > 0 else 0
            blit(f, rotar_sprite(ic_tel, ang), cx, cy, alpha=clamp01(q * 2.5), escala=1 + 0.08 * env, centro=True)
        # horarios con reloj
        q, e = entra(t, cue["hora"])
        x = 60 - (1 - e) * W
        blit(f, card_hora, x, y_hora, alpha=clamp01(q * 2.5))
        if q > 0.05:
            cv.dibujar_reloj(f, int(x + 100), y_hora + 100, 58, t, cue["hora"])
        # ubicación y envíos lado a lado
        for card, k0, xx in ((card_ubic, cue["ubic"], 60), (card_env, cue["envio"], 550)):
            q = prog(t, k0, 0.6)
            blit(f, card, xx + 235, y_med + 95, alpha=clamp01(q * 3), escala=max(ease_out_back(q, 1.8), 0.01), centro=True)
        # banner con destello
        q = prog(t, cue["mayor"], 0.6)
        bx = (W - banner.shape[1] + 2 * PAD) / 2 - PAD
        blit(f, banner, bx + (1 - ease_out_back(q, 1.4)) * -W, y_ban, alpha=clamp01(q * 3))
        if q >= 1:
            h0, w0 = banner.shape[:2]
            x0 = int(bx)
            y0 = y_ban
            pos = ((t - cue["mayor"] - 0.6) % 2.2) * 1700 - 400
            reg = f[y0:y0 + h0, x0:x0 + w0].astype(np.float32)
            reg += (np.exp(-(((DIAG[y0:y0 + h0, x0:x0 + w0] - pos) / 45) ** 2)) * banner[:, :, 3])[..., None] * 110
            f[y0:y0 + h0, x0:x0 + w0] = np.clip(reg, 0, 255).astype(np.uint8)
        # medios de pago
        qt = prog(t, cue["pagos"], 0.5)
        blit(f, titulo_pago, (W - titulo_pago.shape[1]) / 2, y_pago + (1 - ease_out_cubic(qt)) * 25, alpha=ease_out_cubic(qt))
        for i, (ti, k0) in enumerate(zip(tiles, cue["chips"])):
            q = prog(t, k0, 0.5)
            idle = 1 + 0.02 * np.sin(t * 3 + i) if q >= 1 else 1
            blit(f, ti, 60 + 112 + i * 245, y_tile + 87, alpha=clamp01(q * 3),
                 escala=max(ease_out_back(q, 2.4), 0.01) * idle, centro=True)
        # firma final
        qf = prog(t, cue["firma"], 0.6)
        if qf > 0:
            cv2.line(f, (int(W / 2 - 240 * ease_out_cubic(qf)), 1610), (int(W / 2 + 240 * ease_out_cubic(qf)), 1610),
                     acento, 5, cv2.LINE_AA)
            blit(f, firma1, W / 2, 1690, alpha=ease_out_cubic(qf * 1.5), escala=0.8 + 0.2 * ease_out_back(qf, 1.5), centro=True)
            q2 = prog(t, cue["firma"] + 0.3, 0.5)
            blit(f, firma2, W / 2, 1768 + (1 - ease_out_cubic(q2)) * 20, alpha=ease_out_cubic(q2), centro=True)
        return f
    return fn


# ------------------------------------------------------------ transiciones
def tr_losa(acento):
    def tr(a, b, p):
        u = ease_in_out(p) * (float(DIAGONAL.max()) + 420) - 100
        m = np.clip((u - 330 - DIAGONAL) / 4 + 0.5, 0, 1)[..., None]
        losa = (np.clip((u - DIAGONAL) / 4 + 0.5, 0, 1) * (1 - m[..., 0]))[..., None]
        out = a.astype(np.float32) * (1 - m) + b.astype(np.float32) * m
        out = out * (1 - losa) + np.array(acento, np.float32) * losa
        linea = np.clip(1 - np.abs(DIAGONAL - (u - 330)) / 7, 0, 1)[..., None]
        out = out * (1 - 0.5 * linea) + 0.5 * linea * np.array(OSCURO, np.float32)
        return np.clip(out, 0, 255).astype(np.uint8)
    return tr


def tr_puertas(acento):
    def tr(a, b, p):
        off = int(ease_in_out(p) * H / 2)
        out = b.copy()
        if off < H // 2:
            out[:H // 2 - off] = a[off:H // 2]
            out[H // 2 + off:] = a[H // 2:H - off]
            cv2.rectangle(out, (0, H // 2 - off - 8), (W, H // 2 - off), acento, -1)
            cv2.rectangle(out, (0, H // 2 + off), (W, H // 2 + off + 8), acento, -1)
        return out
    return tr


def tr_cuadricula(acento):
    cols, filas = 6, 10
    cx, cy = (_xx // (W / cols)).astype(np.int32), (_yy // (H / filas)).astype(np.int32)
    orden = ((cx + cy) / (cols + filas - 2)).astype(np.float32)

    def tr(a, b, p):
        q = np.clip((ease_in_out(p) * 1.5 - orden) / 0.5, 0, 1)
        m = (q > 0.5).astype(np.float32)[..., None]
        borde = (np.clip(1 - np.abs(q - 0.5) * 6, 0, 1))[..., None]
        out = a.astype(np.float32) * (1 - m) + b.astype(np.float32) * m
        out = out * (1 - 0.75 * borde) + np.array(acento, np.float32) * 0.75 * borde
        return np.clip(out, 0, 255).astype(np.uint8)
    return tr


# ------------------------------------------------------------ línea de tiempo
def construir():
    voz_tts.RATE = VELOCIDAD
    cl = voz_tts.clip_palabras
    esc = []                                   # (dur, constructor(g0, dur) -> fn, voces [(offset, audio)], tipo, acento)
    V0 = 0.3

    for ai, (nombre, l1, l2, foto, acento, dicho, items) in enumerate(ANIMALES):
        texto_voz = dicho + " " + ", ".join(it[2] for it in items) + "."
        audio_c, tiempos = cl(texto_voz)
        cuenta = len(dicho.split())
        ini, k = [], cuenta
        for it in items:
            ini.append(V0 + tiempos[k])
            k += len(it[2].split())
        fin_voz = V0 + len(audio_c) / SR
        d = max(3.2, fin_voz + TR + 0.05)
        esc.append((d, (lambda g0, d_, i=ai, ini_=ini, fv=fin_voz: escena_animal(i, d_, g0, ini_, fv)),
                    [(V0, audio_c)], "animal", acento))

    a, tm = cl(TXT_TODO)
    d = max(3.0, V0 + len(a) / SR + TR + 0.2)
    esc.append((d, (lambda g0, d_, tm_=[V0 + x for x in tm]: escena_todo(d_, g0, tm_)), [(V0, a)], "todo", AMARILLO))
    a, tm = cl(TXT_VISITA)
    d = max(2.6, V0 + len(a) / SR + TR + 0.2)
    esc.append((d, (lambda g0, d_, tm_=[V0 + x for x in tm]: escena_visita(d_, g0, tm_)), [(V0, a)], "visita", AMARILLO))
    a, tm = cl(TXT_SOMOS)
    v0 = 0.6
    d = v0 + len(a) / SR + TR + 0.5
    esc.append((d, (lambda g0, d_, tm_=[v0 + x for x in tm]: escena_somos(d_, g0, tm_)), [(v0, a)], "somos", AMARILLO))

    a, tm = cl(TXT_CIERRE)
    pal = [w.lower().strip(",.:¿?¡!") for w in TXT_CIERRE.split()]
    donde = lambda w, desde=0: pal.index(w, desde)
    t_ = lambda w, desde=0: 0.55 + tm[donde(w, desde)]
    i_f = len(pal) - 1 - pal[::-1].index("forralitas")
    cue = {"tit": 0.55 - 0.05, "tel": t_("llamanos") - 0.15, "hora": t_("lunes") - 0.4, "ubic": t_("hacemos") - 0.55,
           "envio": t_("hacemos") - 0.15, "mayor": t_("venta") - 0.15, "pagos": t_("aceptamos") - 0.15,
           "chips": [t_(w) - 0.2 for w in ("efectivo", "transferencia", "débito", "crédito")],
           "firma": 0.55 + tm[i_f] - 0.25}
    d = 0.55 + len(a) / SR + 1.5
    esc.append((d, (lambda g0, d_, c_=cue, tm_=tm: escena_cierre(d_, g0, tm_, c_)), [(0.55, a)], "cierre", AMARILLO))
    cv.T_TIMBRE0, cv.PERIODO_TIMBRE = cue["tel"] + 0.4, 1.7

    inicios, t = [], 0.0
    for d, *_ in esc:
        inicios.append(t)
        t += d - TR
    total = inicios[-1] + esc[-1][0]
    SEC.clear()
    for i, e in enumerate(esc):
        if e[3] == "animal":
            SEC.append((inicios[i], inicios[i] + e[0] - TR))
    segs, voces, tipos, acentos = [], [], [], []
    for (d, ctor, vs, tipo, acento), t0 in zip(esc, inicios):
        segs.append((d, ctor(t0, d)))
        voces += [(t0 + off, x) for off, x in vs]
        tipos.append(tipo)
        acentos.append(acento)
    return segs, inicios, total, voces, tipos, acentos, cue


def transiciones(tipos, acentos):
    out = []
    for i in range(len(tipos) - 1):
        ac = acentos[i + 1]
        if tipos[i + 1] == "somos":
            out.append(e2.tr_zoom_desenfoque)
        elif tipos[i + 1] == "cierre":
            out.append(tr_cuadricula(ac))
        else:
            out.append([tr_losa, tr_puertas, tr_losa, tr_cuadricula][i % 4](ac))
    return out


def hacer_frame_fn(segs, inicios, total, tipos, acentos):
    trans = transiciones(tipos, acentos)
    fin_barra = inicios[-1] + 0.2
    ancho_seg = (W - 120 - 12 * (len(ANIMALES) - 1)) / len(ANIMALES)

    def barra(f, t):
        f = np.ascontiguousarray(f)
        ov = f.copy()
        for i, (a0, a1) in enumerate(SEC):
            x0 = int(60 + i * (ancho_seg + 12))
            cv2.line(ov, (x0, 58), (int(x0 + ancho_seg), 58), (255, 255, 255), 8, cv2.LINE_AA)
        f = cv2.addWeighted(ov, 0.2, f, 0.8, 0)
        for i, (a0, a1) in enumerate(SEC):
            q = clamp01((t - a0) / (a1 - a0))
            if q > 0:
                x0 = int(60 + i * (ancho_seg + 12))
                cv2.line(f, (x0, 58), (int(x0 + ancho_seg * q), 58), ANIMALES[i][4], 8, cv2.LINE_AA)
        return f

    def make_frame(t):
        t = min(t, total - 1e-3)
        act = [i for i, (s, (d, _)) in enumerate(zip(inicios, segs)) if s <= t < s + d]
        if len(act) == 1:
            f = segs[act[0]][1](t - inicios[act[0]])
        else:
            a, b = act[0], act[-1]
            f = trans[a](segs[a][1](t - inicios[a]), segs[b][1](t - inicios[b]), (t - inicios[b]) / TR)
        if t < fin_barra:
            f = barra(f, t)
        return f
    return make_frame


def musica_viva(total):
    audio_suave.BEAT, audio_suave.TRANSP = 60 / 94, 3        # más rápida y un poco más alta que la anterior
    return audio_suave.musica(total)


def main():
    segs, inicios, total, voces, tipos, acentos, cue = construir()
    Path("videos_salida").mkdir(exist_ok=True)
    mf = hacer_frame_fn(segs, inicios, total, tipos, acentos)
    if "--frames" in sys.argv:
        for s in [float(x) for x in sys.argv[sys.argv.index("--frames") + 1:]]:
            Image.fromarray(mf(s)).save(f"videos_salida/prev_{s:05.1f}.png")
        print("duración total:", round(total, 2), "s | inicios:", [round(x, 1) for x in inicios])
        return
    wav = ev.mezclar(total, inicios, voces, musica_fn=musica_viva, sfx_fn=audio.whoosh, sfx_gain=0.07)
    print("audio listo:", wav, f"({total:.1f} s)")
    if "--audio" in sys.argv:
        return
    pista = AudioFileClip(wav)
    video = VideoClip(mf, duration=total).with_audio(pista.subclipped(0, min(total, pista.duration)))
    video.write_videofile(SALIDA, fps=FPS, codec="libx264", audio_codec="aac", audio_bitrate="192k", preset="medium",
                          ffmpeg_params=["-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart"])
    print("Listo:", SALIDA, f"({total:.1f} s)")


if __name__ == "__main__":
    main()
