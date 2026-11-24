"""Intro 18 de Ignacio + voz de azafata (anuncio de cabina).

Re-arma la línea de tiempo del video original (fuente/intro.mp4) para que cada frase caiga sobre su texto:
alarga escenas (sostiene el texto y repite compases de la música), acorta otras, agrega dos escenas nuevas
("UN APLAUSO PARA MAMI Y PAPI" y "MENSAJES AL EX: PROHIBIDOS") con el mismo estilo neón, y mezcla:
música y efectos originales (con ducking) + ding-dong de cabina + voz es-AR-ElenaNeural con efecto de altavoz.

python intro18.py                 → salida/intro_18_ignacio_azafata.mp4
python intro18.py --cuadros 24.5 41.6 → previas/
python intro18.py --plan          → imprime la línea de tiempo y dónde cae cada palabra clave
"""
import json
import math
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image
from scipy.io import wavfile

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "forralitas_video_final", "proyecto"))
import forralitas_promo as fp  # noqa: E402  (texto y dibujo; cambia el cwd)
import voz_tts                 # noqa: E402

W, H, FPS, SR = 1080, 1920, 30, 44100
FUENTE = os.path.join(AQUI, "fuente", "intro.mp4")
ANTON = os.path.join(RAIZ, "forralitas_video_final", "proyecto", fp.F_ANTON)
MONT = os.path.join(RAIZ, "forralitas_video_final", "proyecto", fp.F_MONT)
SALIDA = os.path.join(AQUI, "salida")
VOZ, VEL = "es-AR-ElenaNeural", "-6%"
e_out, clamp01 = fp.e_out, fp.clamp01

# ------------------------------------------------------------------ línea de tiempo (segundos del original)
# ("src", a, b)            tramo del original (video + audio)
# ("sost", t, dur, a, l)   sostiene el cuadro t (ida y vuelta muy corta) y repite el compás [a, a+l) de la música
# ("nueva", nombre, blk, dur)  escena nueva sobre el fondo del bloque blk (3 s del original) y su música
PLAN = [
    ("src", 0.0, 11.5),                        # intro, ATENCIÓN PASAJEROS, BIENVENIDOS AL VUELO IG-18
    ("sost", 11.5, 0.5, 10.5, 0.5),
    ("src", 11.5, 18.0),                       # tarjeta de embarque
    ("src", 19.0, 20.5),                       # ESTA NOCHE IGNACIO (más corta)
    ("src", 22.0, 24.5),                       # CUMPLE 18 AÑOS
    ("sost", 24.5, 1.0, 23.5, 1.0),
    ("src", 24.5, 25.0),
    ("nueva", "aplauso", 25.0, 6.5),           # UN APLAUSO PARA MAMI Y PAPI
    ("src", 25.0, 27.5),                       # LA PISTA ESTÁ LISTA
    ("sost", 27.5, 0.5, 26.5, 0.5),
    ("src", 27.5, 31.0),                       # LA MÚSICA A FULL
    ("src", 31.0, 33.5),                       # CÁMARAS LISTAS
    ("sost", 33.5, 1.0, 32.5, 1.0),
    ("src", 33.5, 34.0),
    ("nueva", "ex", 31.0, 4.0),                # MENSAJES AL EX: PROHIBIDOS
    ("src", 34.0, 36.5),                       # SIN ESCALAS HASTA EL AMANECER
    ("sost", 36.5, 1.5, 35.5, 0.5),
    ("src", 36.5, 38.0),                       # PREPARADOS PARA DESPEGAR
    ("sost", 38.0, 1.5, 37.5, 0.5),
    ("src", 38.0, 58.0),                       # 3 2 1, despegando, final
]

# avisos: (clave, texto, palabra ancla, segundo NUEVO en que cae esa palabra, con ding-dong)
AVISOS = [
    ("a1", "Señoras y señores pasajeros, bienvenidos a bordo del vuelo i ge dieciocho.", 4, 9.10, True),
    ("a2", "Esta noche Ignacio cumple dieciocho años, y ustedes son sus invitados de honor.", 0, 18.70, True),
    ("a3", "Antes de despegar, un fuerte aplauso para mami y papi, que hicieron posible este vuelo.", 0, 25.00, True),
    ("a4", "Les informamos que la pista ya está lista y la música está a todo volumen.", 10, 34.05, True),
    ("a5", "Pueden usar sus celulares, pero solo para grabar. Los mensajes al ex quedan prohibidos durante todo "
           "el vuelo.", 8, 41.40, True),
    ("a6", "Este vuelo no tiene escalas hasta el amanecer. Tripulación, prepararse para el despegue.", 8, 49.65, True),
    ("tres", "Tres.", 0, 54.06, True),
    ("dos", "Dos.", 0, 55.06, False),
    ("uno", "Uno.", 0, 56.06, False),
    ("a8", "¡Feliz cumpleaños, Ignacio! Bienvenido a los dieciocho.", 0, 62.60, True),
]
DING_ANTES = 1.30          # el ding-dong empieza 1,3 s antes de la voz


def duracion(p):
    return p[2] - p[1] if p[0] == "src" else (p[2] if p[0] == "sost" else p[3])


def inicios():
    t, out = 0.0, []
    for p in PLAN:
        out.append(t)
        t += duracion(p)
    return out, t


# ------------------------------------------------------------------ fuente
class Fuente:
    def __init__(self):
        cap = cv2.VideoCapture(FUENTE)
        self.cuadros = []
        while True:
            ok, f = cap.read()
            if not ok:
                break
            self.cuadros.append(cv2.imencode(".jpg", f, [cv2.IMWRITE_JPEG_QUALITY, 97])[1])
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", FUENTE, "-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                             capture_output=True, check=True).stdout
        self.audio = np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
        self._cache = {}

    def cuadro(self, t):
        i = int(np.clip(round(t * FPS), 0, len(self.cuadros) - 1))
        if i not in self._cache:
            if len(self._cache) > 40:
                self._cache.clear()
            self._cache[i] = cv2.cvtColor(cv2.imdecode(self.cuadros[i], cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
        return self._cache[i]

    def tramo_audio(self, a, b):
        return self.audio[int(round(a * SR)):int(round(b * SR))]


def limpiar(f):
    """Saca el texto del centro del cuadro (el fondo es muy difuso): inpaint a baja resolución + mezcla suave."""
    s = 8
    sm = cv2.resize(f, (W // s, H // s), interpolation=cv2.INTER_AREA)
    m = np.zeros(sm.shape[:2], np.uint8)
    m[690 // s:1250 // s, 20 // s:1060 // s] = 255
    inp = cv2.GaussianBlur(cv2.inpaint(sm, m, 6, cv2.INPAINT_TELEA), (0, 0), 2.5)
    up = cv2.resize(inp, (W, H), interpolation=cv2.INTER_CUBIC).astype(np.float32)
    M = np.zeros((H, W), np.float32)
    M[690:1250, 20:1060] = 1
    M = cv2.GaussianBlur(M, (0, 0), 25)[..., None]
    return (f * (1 - M) + up * M).astype(np.uint8)


# ------------------------------------------------------------------ texto neón
def texto(txt, fuente, tam, esp=0, max_w=None):
    """Máscara (float 0..1) del texto (achica la letra si supera max_w)."""
    while max_w and fp.fuente(fuente, tam).getlength(txt) + esp * len(txt) > max_w and tam > 20:
        tam -= 4
    s = fp.sprite([(txt, (255, 255, 255))], fuente, tam, 0, (0, 0, 0), 0.0, esp)
    return s[..., 3]


def neon(mask, relleno, glow, fuerza=1.0):
    """Sprite RGBA premultiplicado: relleno (color o imagen) + resplandor de color."""
    pad = 70
    m = np.pad(mask, pad)
    g1 = cv2.GaussianBlur(m, (0, 0), 10)
    g2 = cv2.GaussianBlur(m, (0, 0), 34)
    gl = np.clip(g1 * 1.3 + g2 * 1.1, 0, 1) * fuerza
    if isinstance(relleno, np.ndarray):
        rel = np.pad(relleno, ((pad, pad), (pad, pad), (0, 0)))
    else:
        rel = np.empty(m.shape + (3,), np.float32)
        rel[:] = relleno
    a = np.clip(m + gl * (1 - m), 0, 1)
    rgb = rel * m[..., None] + np.array(glow, np.float32) * (gl * (1 - m))[..., None]
    return np.dstack([rgb, a]).astype(np.float32)


def degradado_oro(h, w):
    y = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    a = np.array((255, 244, 200), np.float32)
    b = np.array((255, 196, 60), np.float32)
    c = np.array((214, 120, 20), np.float32)
    g = np.where(y < 0.5, a + (b - a) * (y / 0.5), b + (c - b) * ((y - 0.5) / 0.5))
    return np.broadcast_to(g, (h, w, 3)).copy()


def subrayado(ancho, color):
    h = 40
    m = np.zeros((h, ancho + 40), np.float32)
    cv2.line(m, (20, h // 2), (ancho + 20, h // 2), 1.0, 5, cv2.LINE_AA)
    for x in (12, ancho + 28):
        cv2.circle(m, (x, h // 2), 6, 1.0, -1, cv2.LINE_AA)
    return neon(m, color, color, 0.8)


def corazon(lado, color):
    L = lado * 4
    m = np.zeros((L, L), np.uint8)
    t = np.linspace(0, 2 * np.pi, 200)
    x = 16 * np.sin(t) ** 3
    y = -(13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t))
    pts = np.stack([L / 2 + x * L / 38, L / 2 + y * L / 38 - L * 0.02], 1).astype(np.int32)
    cv2.polylines(m, [pts], True, 255, int(L * 0.07), cv2.LINE_AA)
    m = cv2.resize(m, (lado, lado), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    return neon(m, (255, 240, 250), color, 0.9)


def icono_prohibido(lado):
    """Globito de chat con '...' tachado con el círculo de prohibido."""
    L = lado * 3
    burb = np.zeros((L, L), np.uint8)
    cv2.rectangle(burb, (int(L * .26), int(L * .32)), (int(L * .74), int(L * .62)), 255, -1)
    cv2.ellipse(burb, (int(L * .30), int(L * .47)), (int(L * .06), int(L * .15)), 0, 0, 360, 255, -1)
    cv2.ellipse(burb, (int(L * .70), int(L * .47)), (int(L * .06), int(L * .15)), 0, 0, 360, 255, -1)
    pts = np.array([[L * .36, L * .60], [L * .30, L * .74], [L * .48, L * .61]], np.int32)
    cv2.fillPoly(burb, [pts], 255)
    for x in (.38, .5, .62):
        cv2.circle(burb, (int(L * x), int(L * .47)), int(L * .035), 0, -1, cv2.LINE_AA)
    rojo = np.zeros((L, L), np.uint8)
    cv2.circle(rojo, (L // 2, L // 2), int(L * .42), 255, int(L * .07), cv2.LINE_AA)
    c, r = L / 2, L * .42
    d = r / math.sqrt(2)
    cv2.line(rojo, (int(c - d), int(c - d)), (int(c + d), int(c + d)), 255, int(L * .07), cv2.LINE_AA)
    burb = cv2.resize(burb, (lado, lado), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    rojo = cv2.resize(rojo, (lado, lado), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    a = neon(burb, (255, 255, 255), (120, 200, 255), 0.6)
    b = neon(rojo, (255, 70, 70), (255, 30, 50), 1.0)
    return fp.sobre(a, b, 0, 0)


def glitch(f, fuerza, semilla):
    """Corrimiento de franjas horizontales + separación RGB (como en las transiciones del original)."""
    if fuerza <= 0.01:
        return f
    rng = np.random.default_rng(semilla)
    out = f.copy()
    for _ in range(int(6 * fuerza) + 2):
        y = rng.integers(0, H - 60)
        h = rng.integers(10, 70)
        dx = int(rng.integers(-60, 60) * fuerza)
        out[y:y + h] = np.roll(out[y:y + h], dx, axis=1)
    d = int(14 * fuerza)
    if d:
        out[..., 0] = np.roll(out[..., 0], d, axis=1)
        out[..., 2] = np.roll(out[..., 2], -d, axis=1)
    return out


class EscenaNueva:
    """Escena de texto neón al estilo del original: destello, aro que se expande, golpe del texto, subrayado."""

    def __init__(self, nombre, fuente, blk, dur):
        self.nombre, self.dur = nombre, dur
        # fondo: los cuadros "quietos" del bloque, sin el texto, en ida y vuelta
        self.fondo = [limpiar(fuente.cuadro(blk + 0.8 + i / FPS)) for i in range(int(2.0 * FPS))]
        if nombre == "aplauso":
            self.color = (255, 60, 200)
            lab = "UN APLAUSO PARA"
            m = texto("MAMI Y PAPI", ANTON, 250, max_w=880)
            self.grande = neon(m, degradado_oro(*m.shape), self.color, 1.0)
            self.extra = [corazon(int(s), c) for s, c in ((70, (255, 60, 200)), (54, (255, 120, 220)),
                                                          (86, (255, 40, 150)), (60, (200, 90, 255)))]
            self.ang = 0.0
        else:
            self.color = (255, 40, 60)
            lab = "MENSAJES AL EX:"
            m = texto("PROHIBIDOS", ANTON, 240, max_w=860)
            self.grande = neon(m, (255, 236, 236), self.color, 1.15)
            self.icono = icono_prohibido(300)
            self.ang = -5.0
        self.label = neon(texto(lab, MONT, 50, esp=9), (255, 255, 255), (255, 170, 230), 0.45)
        self.sub = subrayado(int(min(m.shape[1], 900) * 0.72), self.color)

    def cuadro_fondo(self, t):
        n = len(self.fondo)
        i = int(t * FPS) % (2 * n - 2)
        return self.fondo[i if i < n else 2 * n - 2 - i].copy()

    def frame(self, t):
        f = self.cuadro_fondo(t)
        q = clamp01(t / 0.6)
        # aro que se expande
        if q < 1:
            capa = np.zeros((H, W), np.float32)
            cv2.circle(capa, (W // 2, 960), int(120 + 1000 * e_out(q)), 1.0, 12, cv2.LINE_AA)
            capa = (capa + cv2.GaussianBlur(capa, (0, 0), 14) * 2) * (1 - q)
            f = np.clip(f + capa[..., None] * np.array(self.color, np.float32) * 0.9, 0, 255).astype(np.uint8)
        golpe = 0.12 if self.nombre == "aplauso" else 0.30
        qt = clamp01((t - golpe) / 0.25)
        pulso = 1 + 0.025 * max(0.0, math.cos(math.pi * 2 * ((t - golpe) % 0.5) / 0.5)) ** 8 if t > golpe + 0.3 else 1
        sale = clamp01((t - (self.dur - 0.3)) / 0.3)
        a = clamp01(qt * 4) * (1 - sale)
        cy = 1000
        if self.nombre == "ex":
            # el sello entra con golpe y sacude la pantalla
            esc = 1 + 1.4 * (1 - e_out(qt))
            if qt > 0 and t < golpe + 0.55:
                k = (1 - clamp01((t - golpe - 0.25) / 0.3))
                dx, dy = int(np.sin(t * 95) * 18 * k), int(np.cos(t * 80) * 12 * k)
                f = np.roll(np.roll(f, dx, 1), dy, 0)
        else:
            esc = 1 + 0.35 * (1 - e_out(qt))
        if self.nombre == "aplauso":                      # corazones por detrás del texto
            for i, cz in enumerate(self.extra * 2):
                fase = (t * 0.22 + i * 0.137) % 1.0
                x = [150, 930, 250, 840, 110, 980, 330, 760][i]
                y = 1700 - fase * 1500
                al = clamp01((t - 0.6) * 2) * math.sin(math.pi * fase) * (1 - sale)
                fp.blit(f, cz, x + 30 * math.sin(t * 2 + i), y, alpha=al, ang=15 * math.sin(t * 1.5 + i))
        fp.blit(f, self.grande, W / 2, cy, alpha=a, escala=esc * pulso, ang=self.ang)
        ql = clamp01((t - 0.2) / 0.35)
        fp.blit(f, self.label, W / 2, 790 + (1 - e_out(ql)) * 30, alpha=e_out(ql) * (1 - sale))
        qs = clamp01((t - 0.35) / 0.35)
        if qs > 0:
            sub = self.sub
            w = max(4, int(sub.shape[1] * e_out(qs)))
            x0 = (sub.shape[1] - w) // 2
            fp.blit(f, sub[:, x0:x0 + w], W / 2, 1175, alpha=1 - sale)
        if self.nombre == "ex":
            qi = clamp01((t - 0.6) / 0.3)
            if qi > 0:
                fp.blit(f, self.icono, W / 2, 520, alpha=clamp01(qi * 3) * (1 - sale),
                        escala=max(fp.e_back(qi, 2.2), 0.01), ang=8 * math.sin(t * 3))
        # destello inicial y glitch de entrada/salida
        if t < 0.1:
            f = np.clip(f.astype(np.float32) + 160 * (1 - t / 0.1), 0, 255).astype(np.uint8)
        gl = max(1 - clamp01(t / 0.25), sale)
        f = glitch(f, gl, int(t * FPS))
        return f


# ------------------------------------------------------------------ audio
def efecto_altavoz(x):
    """Voz de altavoz de avión: corta graves y agudos, presencia en medios, compresión y un poco de reverb."""
    tmp_in, tmp_out = os.path.join(AQUI, "cache", "_v_in.wav"), os.path.join(AQUI, "cache", "_v_out.wav")
    pad = np.concatenate([x, np.zeros(int(0.6 * SR), np.float32)])
    wavfile.write(tmp_in, SR, pad.astype(np.float32))
    cadena = ("highpass=f=380:poles=2,highpass=f=380:poles=2,lowpass=f=3400:poles=2,lowpass=f=3400:poles=2,"
              "equalizer=f=1700:t=q:w=1.2:g=5,acompressor=threshold=-20dB:ratio=4:attack=4:release=90:makeup=3,"
              "aecho=0.9:0.55:28|47|71:0.28|0.18|0.10")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp_in, "-af", cadena, "-ar", str(SR), "-ac", "1",
                    "-c:a", "pcm_f32le", tmp_out], check=True)
    y = wavfile.read(tmp_out)[1].astype(np.float32)
    return y


def ding_dong():
    """Campanita de cabina: dos tonos (agudo y grave) con armónicos y caída suave."""
    n = int(2.2 * SR)
    t = np.arange(n) / SR
    out = np.zeros(n, np.float32)
    for t0, f0 in ((0.0, 784.0), (0.62, 622.3)):
        tt = t - t0
        on = tt >= 0
        env = np.where(on, np.minimum(tt / 0.004, 1) * np.exp(-np.clip(tt, 0, None) / 0.55), 0)
        tono = (np.sin(2 * np.pi * f0 * tt) + 0.35 * np.sin(2 * np.pi * 2 * f0 * tt) * np.exp(-np.clip(tt, 0, None) / 0.2)
                + 0.12 * np.sin(2 * np.pi * 3.01 * f0 * tt) * np.exp(-np.clip(tt, 0, None) / 0.12))
        out += (env * tono).astype(np.float32)
    out /= np.abs(out).max()
    return out


def rms(x):
    return float(np.sqrt((x ** 2).mean()) + 1e-9)


class Linea:
    def __init__(self, fuente):
        self.f = fuente
        self.ini, self.dur = inicios()
        self.nuevas = {}

    def mapa(self, t):
        """Para el segundo nuevo t: ('src', t_original) o ('nueva', nombre, t_local)."""
        for p, t0 in zip(PLAN, self.ini):
            d = duracion(p)
            if t < t0 + d or p is PLAN[-1]:
                u = t - t0
                if p[0] == "src":
                    return ("src", min(p[1] + u, p[2] - 1 / FPS))
                if p[0] == "sost":
                    k = max(1, math.ceil(d / 0.8))
                    A = d / (2 * k)
                    fase = (u % (2 * A)) / A
                    return ("src", p[1] - A * (fase if fase <= 1 else 2 - fase))
                return ("nueva", p[1], u)

    def audio(self):
        partes = []
        fade = int(0.003 * SR)
        for p in PLAN:
            if p[0] == "src":
                x = self.f.tramo_audio(p[1], p[2])
            elif p[0] == "sost":
                _, _, d, a, l = p
                ch = self.f.tramo_audio(a, a + l)
                x = np.concatenate([ch] * int(round(d / l)))
            else:
                _, _, blk, d = p
                extra = d - 3.0
                l = 1.0 if abs(extra % 1.0) < 1e-6 else 0.5
                loop = self.f.tramo_audio(blk + 1.5, blk + 1.5 + l)
                x = np.concatenate([self.f.tramo_audio(blk, blk + 2.5)] + [loop] * int(round(extra / l))
                                   + [self.f.tramo_audio(blk + 2.5, blk + 3.0)])
            partes.append(x.copy())
        # unión sin perder muestras (los cortes caen sobre el pulso): micro fundido de salida y de entrada
        r = np.linspace(0, 1, fade, dtype=np.float32)[:, None]
        for i, x in enumerate(partes):
            if i > 0:
                x[:fade] *= r
            if i < len(partes) - 1:
                x[-fade:] *= r[::-1]
        out = np.concatenate(partes)
        return out


def voces():
    """Devuelve [(clave, audio procesado, t_inicio, tiempos_palabras, ding)]."""
    res = []
    for clave, txt, ancla, t_ancla, ding in AVISOS:
        a, tiempos = voz_tts.clip_palabras(txt, voz=VOZ, rate=VEL)
        t0 = t_ancla - tiempos[ancla]
        res.append((clave, a.astype(np.float32), t0, tiempos, ding, txt))
    return res


def mezclar(linea, vs, ruta):
    musica = linea.audio()
    n = len(musica)
    voz = np.zeros(n, np.float32)
    act = np.zeros(n, np.float32)
    dd = ding_dong()
    dd_pa = efecto_altavoz(dd * 0.5)
    dd_pa *= 10 ** (-9 / 20) / (np.abs(dd_pa).max() + 1e-9)       # pico del ding-dong a -9 dBFS
    for clave, a, t0, _, ding, _ in vs:
        y = efecto_altavoz(a)
        y *= 10 ** (-15 / 20) / rms(y[:len(a)])
        i = int(t0 * SR)
        voz[i:i + len(y)] += y[:max(0, n - i)]
        act[i:i + len(a)] = 1.0
        if ding:
            j = int((t0 - DING_ANTES) * SR)
            voz[j:j + len(dd_pa)] += dd_pa[:max(0, n - j)]
            act[j:j + int(1.2 * SR)] = np.maximum(act[j:j + int(1.2 * SR)], 0.6)
    # ducking suave: -11 dB con la voz, -6 dB con el ding
    k = int(0.25 * SR)
    sm = np.convolve(np.pad(act, (k, k), mode="edge"), np.ones(k) / k, mode="same")[k:-k]
    gan = 10 ** (-11 * np.clip(sm, 0, 1) / 20)
    mix = musica * gan[:, None] + voz[:, None]
    tmp = ruta.replace(".wav", "_crudo.wav")
    wavfile.write(tmp, SR, np.clip(mix, -1, 1).astype(np.float32))
    med = subprocess.run(["ffmpeg", "-hide_banner", "-i", tmp, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    j = json.loads(med[med.rfind("{"):med.rfind("}") + 1])
    ln = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
          f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af", f"{ln},alimiter=limit=0.89:level=false",
                    "-ar", "48000", "-ac", "2", ruta], check=True)
    os.remove(tmp)


# ------------------------------------------------------------------ video
class Video:
    def __init__(self):
        os.makedirs(os.path.join(AQUI, "cache"), exist_ok=True)
        self.fuente = Fuente()
        self.linea = Linea(self.fuente)
        self.dur = self.linea.dur
        self.nuevas = {p[1]: EscenaNueva(p[1], self.fuente, p[2], p[3]) for p in PLAN if p[0] == "nueva"}

    def frame(self, t):
        m = self.linea.mapa(t)
        if m[0] == "src":
            return self.fuente.cuadro(m[1])
        return self.nuevas[m[1]].frame(m[2])


def plan():
    ini, total = inicios()
    print(f"duración total {total:.2f} s")
    for p, t0 in zip(PLAN, ini):
        print(f"  {t0:6.2f} → {t0 + duracion(p):6.2f}  {p}")
    print("voces:")
    vs = voces()
    for clave, a, t0, tiempos, ding, txt in vs:
        print(f"  {clave:5s} ding {t0 - DING_ANTES if ding else 0:6.2f}  voz {t0:6.2f} → {t0 + len(a) / SR:6.2f}  {txt[:50]}")
    for (c1, a1, t1, *_), (c2, a2, t2, _, d2, _) in zip(vs, vs[1:]):
        hueco = (t2 - (DING_ANTES if d2 else 0)) - (t1 + len(a1) / SR)
        if hueco < 0.15:
            print("  ¡OJO! se pisan", c1, c2, round(hueco, 2))
    return vs


def main():
    if "--plan" in sys.argv:
        plan()
        return
    v = Video()
    if "--cuadros" in sys.argv:
        d = os.path.join(AQUI, "previas", "cuadros")
        os.makedirs(d, exist_ok=True)
        for s in [float(x) for x in sys.argv[sys.argv.index("--cuadros") + 1:]]:
            Image.fromarray(v.frame(s)).save(os.path.join(d, f"{s:05.2f}.png"))
        return
    vs = plan()
    os.makedirs(SALIDA, exist_ok=True)
    wav = os.path.join(AQUI, "cache", "mezcla.wav")
    mezclar(v.linea, vs, wav)
    tmp = os.path.join(AQUI, "cache", "video.mp4")
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-profile:v", "high", "-preset", "slow",
                          "-crf", "16", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for i in range(int(round(v.dur * FPS))):
        p.stdin.write(np.ascontiguousarray(v.frame(i / FPS)).tobytes())
    p.stdin.close()
    p.wait()
    final = os.path.join(SALIDA, "intro_18_ignacio_azafata.mp4")
    comun = ["-c:v", "libx264", "-profile:v", "high", "-preset", "slow", "-b:v", "2900k", "-maxrate", "4500k",
             "-bufsize", "6000k", "-pix_fmt", "yuv420p", "-r", str(FPS)]
    log = os.path.join(AQUI, "cache", "x264pass")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp] + comun + ["-pass", "1", "-passlogfile", log, "-an",
                    "-f", "mp4", os.devnull], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-i", wav, "-map", "0:v", "-map", "1:a"] + comun +
                   ["-pass", "2", "-passlogfile", log, "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                    "-movflags", "+faststart", final], check=True)
    print("Listo:", final)


if __name__ == "__main__":
    main()
