"""Versión 2 (más dinámica) del video "¡Llegó la viruta!" — 20 s, 1080x1920.

Mismo mensaje, mismos datos y misma estructura que viruta_promo.py, con:
música con ritmo (ducking bajo la voz), cortes y saltos de zoom sobre el beat, textos con impacto,
temblor de cámara, virutas que vuelan, foto tipo polaroid que se agranda, sellos y cierre animado.

Uso:  python viruta_promo_v2.py                 → forralitas_viruta_v2_9x16.mp4 (+ versión sin voz)
      python viruta_promo_v2.py --cuadros 1 5 9  → previas_v2/
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
sys.path.insert(0, AQUI)
import viruta_promo as v1          # noqa: E402  (datos, voz, fotos, cierre; cambia el cwd)

fp = v1.fp
# locución con la marca: (inicio s, texto voz, subtítulo con *resaltado* y | entre bloques)
v1.VOZ = [
    (0.55, "¡Llegó la viruta a Forrajería Forralitas!", "¡Llegó la *viruta* | a Forrajería *Forralitas!*"),
    (4.75, "¡Ya la tenemos en Forralitas!", "¡Ya la tenemos | en *Forralitas!*"),
    (8.35, "Y tenemos muchos productos más,", "Y tenemos muchos | *productos* *más,*"),
    (12.2, "con la mejor calidad y al mejor precio.", "con la *mejor* *calidad* | y al *mejor* *precio.*"),
    (15.25, "¡Te esperamos en Forralitas!", "*¡Te* *esperamos* | en *Forralitas!*"),
]
W, H, FPS, DUR, SR = 1080, 1920, 30, 20.0, 44100
MUSICA = os.path.join(AQUI, "musica", "Happy_Alley.mp3")
MUSICA_INICIO, BPM = 12.91, 111.5
BEAT = 60 / BPM
e_out, e_inout, e_back, prog, clamp01 = fp.e_out, fp.e_inout, fp.e_back, fp.prog, fp.clamp01
blit, sprite, caja, sobre = fp.blit, fp.sprite, fp.caja, fp.sobre
AMARILLO, BLANCO, NEGRO = v1.AMARILLO, v1.BLANCO, v1.NEGRO
VIRUTA, MARRON_OSC, VERDE_OSC = v1.VIRUTA, v1.MARRON_OSC, v1.VERDE_OSC
ANTON, MONT = v1.ANTON, v1.MONT


def beat(n):
    return n * BEAT


# ============================================================ cámara
def camara(f, zoom=1.0, dx=0.0, dy=0.0, ang=0.0):
    if abs(zoom - 1) < 1e-3 and abs(dx) < 0.3 and abs(dy) < 0.3 and abs(ang) < 0.01:
        return f
    M = cv2.getRotationMatrix2D((W / 2, H / 2), ang, zoom)
    M[0, 2] += dx
    M[1, 2] += dy
    return cv2.warpAffine(f, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def temblor(t, t0, amp=18, dur=0.35):
    if not (t0 <= t <= t0 + dur):
        return 0.0, 0.0, 0.0
    k = (1 - (t - t0) / dur) ** 2
    return amp * k * np.sin(t * 97), amp * k * np.cos(t * 83), 1.2 * k * np.sin(t * 61)


def punch(t, t0, amt=0.07, dur=0.35):
    """Salto de zoom sobre el beat (sube rápido y vuelve con suavidad)."""
    if t < t0:
        return 0.0
    x = (t - t0) / dur
    return amt * (e_out(min(x * 3, 1)) - e_inout(clamp01((x - 0.33) / 0.67)) * 0.6)


def flash(f, t, t0, dur=0.18, op=0.7):
    q = (t - t0) / dur
    if 0 <= q <= 1:
        a = op * (1 - q) ** 2
        f = cv2.addWeighted(f, 1 - a, np.full_like(f, (255, 244, 220)), a, 0)
    return f


# ============================================================ virutas que vuelan
def _sprite_viruta(rng):
    l = int(rng.uniform(26, 54))
    im = Image.new("RGBA", (l * 2, l * 2), (0, 0, 0, 0))
    from PIL import ImageDraw
    d = ImageDraw.Draw(im)
    col = tuple(int(c) for c in np.clip(np.array(VIRUTA) * rng.uniform(0.82, 1.08), 0, 255))
    oscuro = tuple(int(c * 0.72) for c in col)
    ancho = rng.uniform(0.35, 0.6)
    d.ellipse((l * 0.2, l * (1 - ancho / 2), l * 1.8, l * (1 + ancho / 2)), fill=col + (255,))
    d.arc((l * 0.25, l * (1 - ancho / 2), l * 1.75, l * (1 + ancho / 2)), 200, 340, fill=oscuro + (255,), width=3)
    a = np.asarray(im, np.float32)
    a[..., :3] *= a[..., 3:4] / 255
    a[..., 3] /= 255
    return a


class Virutas:
    """Ráfagas de virutas: salen de un punto, giran y caen con gravedad."""

    def __init__(self, rafagas, semilla=1):
        rng = np.random.default_rng(semilla)
        self.sprites = [_sprite_viruta(rng) for _ in range(10)]
        self.part = []
        for t0, x0, y0, n, fuerza in rafagas:
            for _ in range(n):
                ang = rng.uniform(-np.pi * 0.95, -np.pi * 0.05)
                v = rng.uniform(0.5, 1.0) * fuerza
                self.part.append(dict(t0=t0 + rng.uniform(0, 0.08), x=x0 + rng.uniform(-60, 60), y=y0,
                                      vx=np.cos(ang) * v, vy=np.sin(ang) * v, rot=rng.uniform(0, 360),
                                      vr=rng.uniform(-500, 500), s=rng.uniform(0.6, 1.25),
                                      k=int(rng.integers(len(self.sprites)))))

    def dibujar(self, f, t):
        g = 2600.0
        for p in self.part:
            dt = t - p["t0"]
            if dt < 0 or dt > 1.8:
                continue
            x = p["x"] + p["vx"] * dt
            y = p["y"] + p["vy"] * dt + 0.5 * g * dt * dt
            if y > H + 80:
                continue
            a = clamp01(dt / 0.05) * clamp01((1.8 - dt) / 0.4)
            blit(f, self.sprites[p["k"]], x, y, alpha=a, escala=p["s"], ang=p["rot"] + p["vr"] * dt)


# ============================================================ piezas
def polaroid(img, w, h, borde=26):
    base = caja(w + 2 * borde, h + 2 * borde + 40, 18, (252, 248, 238))
    foto = np.dstack([img.astype(np.float32), np.ones(img.shape[:2], np.float32)])
    return sobre(base, foto, borde, borde)


def sombra(spr, blur=22, op=0.45):
    a = cv2.GaussianBlur(spr[..., 3], (0, 0), blur) * op
    return np.dstack([np.zeros(spr.shape[:2] + (3,), np.float32), a])


def resaltado(txt, tam, fondo, tinta, padx=28):
    """Texto sobre una franja de color (estilo marcador)."""
    s = sprite([(txt, tinta)], ANTON, tam, 0, NEGRO, 0)
    pad = int(tam * 0.35)
    w = s.shape[1] - 2 * pad + 2 * padx
    h = int(tam * 1.25)
    base = caja(w, h, 10, fondo)
    return sobre(base, s, padx - pad, (h - s.shape[0]) // 2 + int(tam * 0.06))


def sello(txt, tam, color):
    s = sprite([(txt, color)], ANTON, tam, 0, NEGRO, 0)
    pad = int(tam * 0.35)
    w = s.shape[1] - 2 * pad + 90
    h = int(tam * 1.45)
    borde = caja(w, h, 22, color)
    base = sobre(borde, caja(w - 16, h - 16, 16, MARRON_OSC), 8, 8)
    return sobre(base, s, 45 - pad, (h - s.shape[0]) // 2 + int(tam * 0.06))


def rayos(t, c1, c2, n=16):
    yy, xx = np.mgrid[0:H // 4, 0:W // 4].astype(np.float32) * 4
    ang = np.arctan2(yy - H * 0.47, xx - W / 2)
    r = np.hypot(xx - W / 2, yy - H * 0.47) / np.hypot(W / 2, H / 2)
    m = (np.sin(n * (ang + t * 0.35)) > 0).astype(np.float32)
    m = cv2.GaussianBlur(m, (0, 0), 1.2)
    base = np.array(c1, np.float32) * (1 - m[..., None]) + np.array(c2, np.float32) * m[..., None]
    base *= (1 - 0.45 * r[..., None] ** 1.6)
    return cv2.resize(np.clip(base, 0, 255).astype(np.uint8), (W, H), interpolation=cv2.INTER_LINEAR)


# ============================================================ video
class Video(v1.Video):
    def __init__(self):
        super().__init__()
        c = self.c
        self.l1 = v1.T("¡LLEGÓ", ANTON, 190, BLANCO)
        self.l2 = v1.T("LA VIRUTA!", ANTON, v1.ajustar("LA VIRUTA!", ANTON, 210, 1000), AMARILLO)
        self.ya = resaltado("Ya la tenemos en", 74, AMARILLO, MARRON_OSC)
        self.forr = v1.T("FORRALITAS", ANTON, 168, AMARILLO)
        self.ym = resaltado("Y muchos", 88, BLANCO, MARRON_OSC)
        self.prod = v1.T("productos más", ANTON, v1.ajustar("productos más", ANTON, 160, 1000), AMARILLO)
        self.s_cal = sello("MEJOR CALIDAD", 120, AMARILLO)
        self.s_pre = sello("MEJOR PRECIO", 120, BLANCO)
        self.mas = v1.T("+", ANTON, 230, AMARILLO)
        foto_cam = self.fotos["camion"]
        self.cam_card_img = foto_cam.grade(fp.recorte(foto_cam.img, 660, 900, 0.42, 0.30, 1.55), np.ones((900, 660, 1), np.float32))
        self.card = polaroid(self.cam_card_img, 660, 900)
        self.card_sombra = sombra(self.card)
        v = self.voces
        self.t_cal = v[3]["t0"] + v[3]["tiempos"][3] - 0.05
        self.t_pre = v[3]["t0"] + v[3]["tiempos"][7] - 0.05
        logo = fp.logo_circular(96)
        nom = v1.T("FORRALITAS", ANTON, 62, BLANCO)
        pad = int(62 * 0.35)
        ancho = 96 + 14 + nom.shape[1] - 2 * pad + 40
        bug = caja(ancho, 116, 58, (0, 0, 0), 0.45)
        bug = sobre(bug, logo, 10, 10)
        self.marca = sobre(bug, nom, 96 + 24 - pad, (116 - nom.shape[0]) // 2 + 4)
        self.virutas = Virutas([
            (0.30, W / 2, H * 0.75, 34, 2300),          # explota con el título
            (beat(4), W * 0.3, H * 0.9, 16, 1900),
            (5.30, W / 2, H * 0.8, 22, 2100),           # la polaroid se agranda
            (self.t_cal, W * 0.25, H * 0.62, 18, 2000),
            (self.t_pre, W * 0.75, H * 0.62, 18, 2000),
            (15.10, W / 2, H * 0.30, 40, 2400),         # ¡te esperamos!
        ], semilla=7)
        # cortes rápidos sobre la foto de bolsas: (inicio, fin, (cx, cy, zoom) inicial, final)
        self.cortes_bolsas = [
            (8.0, 8.0 + beat(2), (0.22, 0.82, 1.55), (0.22, 0.80, 1.65)),
            (8.0 + beat(2), 8.0 + beat(4), (0.45, 0.42, 1.45), (0.45, 0.40, 1.55)),
            (8.0 + beat(4), 12.0, (0.30, 0.66, 1.25), (0.33, 0.58, 1.04)),
        ]

    # ---- escenas
    def esc_chico(self, t):
        z = 1.0 + 0.22 * (1 - e_out(clamp01(t / 0.45))) + 0.05 * t / 4 + punch(t, beat(4), 0.09)
        f = self.fotos["chico"].cuadro(0.0, (0.47, 0.50, 1.0), (0.47, 0.50, 1.0), v1.VIG)
        f = (f.astype(np.float32) * v1.GRAD).astype(np.uint8)
        dx, dy, a = temblor(t, 0.3, 26)
        dx2, dy2, a2 = temblor(t, beat(4), 14)
        f = camara(f, z, dx + dx2, dy + dy2, a + a2)
        q = prog(t, 0.25, 0.32)
        blit(f, self.l1, W / 2, 370, alpha=clamp01(q * 3), escala=max(2.6 - 1.6 * e_out(q), 0.01), ang=-4 * (1 - q))
        q = prog(t, 0.5, 0.35)
        wig = 1.5 * np.sin(t * 5) * clamp01((t - 0.9) * 2)
        blit(f, self.l2, W / 2, 560, alpha=clamp01(q * 3), escala=max(e_back(q, 2.2), 0.01), ang=wig)
        return flash(f, t, 0.28, 0.2, 0.75)

    def esc_camion(self, t):
        tl = t - 4.0
        foto = self.fotos["camion"]
        if tl < 1.3:                                   # polaroid entra girando sobre el fondo desenfocado
            fondo = foto.cuadro(0.5, (0.42, 0.3, 1.5), (0.42, 0.3, 1.5), v1.VIG)
            fondo = cv2.GaussianBlur(cv2.resize(fondo, (W // 4, H // 4)), (0, 0), 5)
            f = (cv2.resize(fondo, (W, H)).astype(np.float32) * 0.55).astype(np.uint8)
            q = prog(tl, 0.0, 0.55)
            y = 1040 + (1 - e_out(q)) * 1300
            ang = -14 + 10 * e_back(q, 1.4)
            blit(f, self.card_sombra, W / 2 + 12, y + 22, alpha=clamp01(q * 3), ang=ang)
            blit(f, self.card, W / 2, y, alpha=clamp01(q * 3), ang=ang)
        else:                                          # se agranda a pantalla completa
            p = clamp01((tl - 1.3) / 0.35)
            full = foto.cuadro(clamp01((tl - 1.3) / 2.7), (0.42, 0.30, 1.55), (0.45, 0.31, 1.45), v1.VIG)
            full = (full.astype(np.float32) * v1.GRAD).astype(np.uint8)
            if p < 1:
                e = e_inout(p)
                fondo = (cv2.GaussianBlur(full, (0, 0), 14).astype(np.float32) * 0.55).astype(np.uint8)
                esc = 0.6 + 0.4 * e
                M = cv2.getRotationMatrix2D((W / 2, H / 2), -4 * (1 - e), esc)
                M[1, 2] += (1040 - H / 2) * (1 - e)
                capa = cv2.warpAffine(full, M, (W, H), borderMode=cv2.BORDER_CONSTANT)
                m = cv2.warpAffine(np.ones((H, W), np.float32), M, (W, H))[..., None]
                f = (capa * m + fondo * (1 - m)).astype(np.uint8)
            else:
                f = full
            dx, dy, a = temblor(tl, 1.3 + 0.35, 12)
            f = camara(f, 1 + punch(tl, 1.65, 0.05), dx, dy, a)
        q = prog(tl, 0.45, 0.4)
        blit(f, self.ya, W / 2 - (1 - e_out(q)) * W, 330, alpha=clamp01(q * 3), ang=-3)
        q = prog(tl, 0.8, 0.35)
        blit(f, self.forr, W / 2, 470, alpha=clamp01(q * 3), escala=max(2.2 - 1.2 * e_out(q), 0.01))
        return f

    def esc_bolsas(self, t):
        foto = self.fotos["bolsas"]
        for k, (a, b, ini, fin) in enumerate(self.cortes_bolsas):
            if a <= t < b or k == len(self.cortes_bolsas) - 1:
                p = clamp01((t - a) / (b - a))
                f = foto.cuadro(p, ini, fin, v1.VIG)
                f = (f.astype(np.float32) * v1.GRAD).astype(np.uint8)
                f = flash(f, t, a, 0.12, 0.45) if k else f
                dx, dy, ang = temblor(t, a, 10, 0.25) if k else (0, 0, 0)
                f = camara(f, 1 + punch(t, a, 0.05), dx, dy, ang)
                break
        tl = t - 8.0
        q = prog(tl, 0.35, 0.4)
        blit(f, self.ym, W / 2 - (1 - e_out(q)) * W, 350, alpha=clamp01(q * 3), ang=-3)
        q = prog(tl, 0.6, 0.4)
        blit(f, self.prod, W / 2, 500, alpha=clamp01(q * 3), escala=max(e_back(q, 2.0), 0.01))
        for i, (bx, by, t0) in enumerate(((180, 760, 1.2), (900, 700, 1.45), (840, 1150, 1.7))):
            q = prog(tl, t0, 0.35)
            if q > 0:
                blit(f, self.mas, bx, by + 10 * np.sin(t * 4 + i), alpha=clamp01(q * 3) * 0.95,
                     escala=max(e_back(q, 2.6), 0.01), ang=15 * np.sin(t * 2 + i))
        return f

    def esc_calidad(self, t):
        f = rayos(t, (140, 92, 46), (112, 72, 36))
        f = v1.fondo_textura(f.astype(np.float32), t, 3)
        for spr, t0, y, ang in ((self.s_cal, self.t_cal - 0.12, 760, -5), (self.s_pre, self.t_pre - 0.12, 1010, 4)):
            q = prog(t, t0, 0.22)
            if q > 0:
                blit(f, spr, W / 2, y, alpha=clamp01(q * 4), escala=2.6 - 1.6 * e_out(q), ang=ang)
        dx, dy, a = temblor(t, self.t_cal + 0.1, 22)
        dx2, dy2, a2 = temblor(t, self.t_pre + 0.1, 22)
        f = camara(f, 1.0, dx + dx2, dy + dy2, a + a2)
        f = flash(f, t, self.t_cal + 0.08, 0.15, 0.5)
        return flash(f, t, self.t_pre + 0.08, 0.15, 0.5)

    def esc_cierre(self, t):
        f = v1.Video.cierre(self, t)
        dx, dy, a = temblor(t, 15.15, 18)
        return camara(f, 1 + punch(t, 15.12, 0.04), dx, dy, a)

    # ---- montaje con transiciones
    def base(self, t):
        T = [(0.0, 4.0, self.esc_chico), (4.0, 8.0, self.esc_camion), (8.0, 12.0, self.esc_bolsas),
             (12.0, 15.0, self.esc_calidad), (15.0, DUR, self.esc_cierre)]
        tr = {4.0: (whip, 0.36), 8.0: (zoom_through, 0.4), 12.0: (whip_vertical, 0.36), 15.0: (zoom_through, 0.4)}
        for corte, (fn, d) in tr.items():
            if corte - d / 2 <= t < corte + d / 2:
                ia = next(i for i, x in enumerate(T) if x[1] == corte)
                p = (t - (corte - d / 2)) / d
                return fn(T[ia][2](min(t, corte - 1e-3)), T[ia + 1][2](max(t, corte)), p)
        for a, b, fn in T:
            if a <= t < b:
                return fn(t)
        return T[-1][2](t)

    def titulo(self, f, t):           # los títulos ya van dentro de cada escena
        return

    def frame(self, t):
        t = min(t, DUR - 1e-3)
        f = np.ascontiguousarray(self.base(t))
        self.virutas.dibujar(f, t)
        if 0.9 <= t < 15.0:                                   # marca fija arriba
            q = prog(t, 0.9, 0.4) * (1 - prog(t, 14.6, 0.3))
            blit(f, self.marca, W / 2, 150 - (1 - e_out(prog(t, 0.9, 0.4))) * 120, alpha=clamp01(q * 3))
        self.subtitulos(f, t)
        if t > DUR - 0.35:
            f = (f.astype(np.float32) * ((DUR - t) / 0.35)).astype(np.uint8)
        return f

    # ---- audio: voz + música con ducking + efectos sutiles
    def audio(self, ruta, con_voz=True):
        n = int(DUR * SR)
        voz = np.zeros(n, np.float32)
        if con_voz:
            for v in self.voces:
                x = v["audio"] * (10 ** (-17 / 20) / (np.sqrt((v["audio"] ** 2).mean()) + 1e-9))
                i = int(v["t0"] * SR)
                voz[i:i + x.size] += x[:max(0, n - i)]
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(MUSICA_INICIO), "-t", str(DUR + 1), "-i", MUSICA,
                              "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
        mus = np.frombuffer(raw, np.float32).reshape(-1, 2)[:n].copy()
        mus *= 10 ** (-20 / 20) / (np.sqrt((mus ** 2).mean()) + 1e-9)
        if con_voz:
            env = np.sqrt(np.convolve(voz ** 2, np.ones(int(0.04 * SR)) / int(0.04 * SR), mode="same"))
            act = (env > 0.01).astype(np.float32)
            k = int(0.3 * SR)
            sm = np.convolve(np.pad(act, (k, k), mode="edge"), np.ones(k) / k, mode="same")[k:-k]
            mus *= (1 - 0.65 * np.clip(sm * 1.4, 0, 1))[:, None]
        fo = int(1.2 * SR)
        mus[-fo:] *= np.linspace(1, 0, fo)[:, None]
        mus[:int(0.05 * SR)] *= np.linspace(0, 1, int(0.05 * SR))[:, None]
        sfx = np.zeros(n, np.float32)
        import audio as sfxlib

        def poner(x, t, g):
            i = int(t * SR)
            if 0 <= i < n:
                m = min(len(x), n - i)
                sfx[i:i + m] += x[:m] * g
        golpe = sfxlib.golpe()
        for t in (0.3, self.t_cal, self.t_pre, 15.12):
            poner(golpe, t, 0.22)
        for t in (4.0, 8.0, 12.0, 15.0):
            poner(sfxlib.whoosh(0.4), t - 0.2, 0.09)
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


# ============================================================ transiciones
def whip(a, b, p):
    e = e_inout(p)
    off = int(e * W)
    out = np.empty_like(a)
    out[:, :W - off] = a[:, off:]
    out[:, W - off:] = b[:, :off]
    k = int(1 + 140 * np.sin(np.pi * p))
    k += k % 2 == 0
    return cv2.blur(out, (k, 1)) if k > 1 else out


def whip_vertical(a, b, p):
    e = e_inout(p)
    off = int(e * H)
    out = np.empty_like(a)
    out[:H - off] = a[off:]
    out[H - off:] = b[:off]
    k = int(1 + 120 * np.sin(np.pi * p))
    k += k % 2 == 0
    return cv2.blur(out, (1, k)) if k > 1 else out


def zoom_through(a, b, p):
    return fp.tr_zoom(a, b, p)


def main():
    v = Video()
    if "--cuadros" in sys.argv:
        d = os.path.join(AQUI, "previas_v2")
        os.makedirs(d, exist_ok=True)
        for s in [float(x) for x in sys.argv[sys.argv.index("--cuadros") + 1:]]:
            Image.fromarray(v.frame(s)).save(os.path.join(d, f"{s:05.2f}.png"))
        return
    sal = os.path.join(AQUI, "forralitas_viruta_v2_9x16.mp4")
    sal_sin_voz = os.path.join(AQUI, "forralitas_viruta_v2_9x16_solo_musica.mp4")
    wav = v.audio(os.path.join(AQUI, "_v2.wav"))
    wav2 = v.audio(os.path.join(AQUI, "_v2_sin_voz.wav"), con_voz=False)
    video_tmp = os.path.join(AQUI, "_v2_video.mp4")
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-profile:v", "high", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
           video_tmp]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        p.stdin.write(v.frame(i / FPS).tobytes())
    p.stdin.close()
    p.wait()
    for w, s in ((wav, sal), (wav2, sal_sin_voz)):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video_tmp, "-i", w, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-shortest", "-movflags", "+faststart", s], check=True)
        os.remove(w)
    os.remove(video_tmp)
    print("Listo:", sal, "|", sal_sin_voz)


if __name__ == "__main__":
    main()
