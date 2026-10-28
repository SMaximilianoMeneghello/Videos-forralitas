"""Video "¡Llegó la viruta!" — Forrajería Forralitas (vertical 1080x1920, 20 s).

Uso:   python viruta_promo.py              → forralitas_viruta_9x16.mp4 (con voz) y forralitas_viruta_9x16_sin_audio.mp4
       python viruta_promo.py --cuadros 2 6 10 13 17   → vistas previas en previas/

Datos del cierre: DATOS (abajo). Textos y locución: TEXTOS / VOZ.
"""
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, os.path.join(RAIZ, "forralitas_video_final", "proyecto"))
sys.path.insert(0, RAIZ)
import forralitas_promo as fp          # noqa: E402  (utilidades de texto, color y logo; cambia el cwd)
import voz_tts                         # noqa: E402

os.chdir(os.path.join(RAIZ, "forralitas_video_final", "proyecto"))   # fuentes/ y material/logo.jpg
W, H, FPS, DUR = 1080, 1920, 30, 20.0
SR = 44100
MAT = os.path.join(AQUI, "material")

# ============================================================ datos (los del chat, sin cambios)
DATOS = {
    "nombre": "FORRAJERÍA FORRALITAS",
    "rubro": "Forrajería y Semillería",
    "direccion": ("Ruta 305 km 7,5", "Las Talitas"),
    "horarios": (("Lunes a viernes", "8:00 a 19:00"), ("Sábados", "8:30 a 19:00")),
    "pagos": "Efectivo · Transferencia · Débito · Crédito",
    "whatsapp": ("381 526 9004", "381 633 4344"),
}
TEXTOS = {
    "t1": "¡LLEGÓ LA VIRUTA!",
    "t2a": "Ya la tenemos en", "t2b": "FORRALITAS",
    "t3a": "Y muchos", "t3b": "productos más",
    "t4a": "Mejor calidad", "t4b": "Mejor precio",
    "t5": "¡TE ESPERAMOS!",
}
# locución: exactamente el mensaje, en 4 partes; (inicio s, texto voz, subtítulo con *palabras* resaltadas)
VOZ = [
    (0.55, "¡Llegó la viruta a nuestra forrajería!", "¡Llegó la *viruta* | a nuestra *forrajería!*"),
    (8.35, "Y tenemos muchos productos más,", "Y tenemos muchos | *productos* *más,*"),
    (12.2, "con la mejor calidad y al mejor precio.", "con la *mejor* *calidad* | y al *mejor* *precio.*"),
    (15.25, "¡Te esperamos!", "*¡Te* *esperamos!*"),
]
VOZ_NOMBRE, VOZ_VEL = "es-AR-TomasNeural", "+0%"

# paleta tierra
VIRUTA = (240, 200, 120)
AMARILLO = (255, 208, 64)
MARRON, MARRON_OSC = (120, 78, 42), (58, 36, 18)
VERDE, VERDE_OSC = (52, 104, 50), (22, 52, 26)
BLANCO, NEGRO = (255, 255, 255), (16, 12, 8)
ANTON, MONT = fp.F_ANTON, fp.F_MONT

e_out, e_inout, e_back, prog, clamp01 = fp.e_out, fp.e_inout, fp.e_back, fp.prog, fp.clamp01
blit, sprite, caja, sobre = fp.blit, fp.sprite, fp.caja, fp.sobre


def T(txt, ruta, tam, col=BLANCO, trazo=0, sombra=0.6):
    return sprite([(txt, col)], ruta, tam, trazo, NEGRO, sombra)


def ajustar(txt, ruta, tam, max_w):
    while fp.fuente(ruta, tam).getlength(txt) > max_w and tam > 20:
        tam -= 2
    return tam


# ============================================================ fotos
class Foto:
    def __init__(self, nombre, perfil):
        self.img = np.asarray(Image.open(os.path.join(MAT, nombre)).convert("RGB"))
        self.grade = fp.Grade(perfil, cv2.resize(self.img, (240, 320)))

    def cuadro(self, p, a, b, vig):
        e = e_inout(p)
        cx, cy, z = (a[i] + (b[i] - a[i]) * e for i in range(3))
        return self.grade(fp.recorte(self.img, W, H, cx, cy, z), vig)


yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
_r = np.hypot(xx - W / 2, yy - H / 2) / np.hypot(W / 2, H / 2)
VIG = (1 - 0.18 * _r ** 2.4)[..., None].astype(np.float32)
_y = yy[:, :1] / H
GRAD = (1 - 0.40 * np.clip((0.36 - _y) / 0.28, 0, 1) - 0.55 * np.clip((_y - 0.60) / 0.30, 0, 1))[..., None]

# escenas (inicio, fin) y encuadres (cx, cy, zoom) inicial → final
ESC = {
    "chico": (0.0, 4.0, "foto_chico_viruta.jpg", "calido", (0.47, 0.50, 1.00), (0.44, 0.44, 1.12)),
    "camion": (4.0, 8.0, "foto_camion_viruta.jpg", "calido", (0.40, 0.30, 1.62), (0.44, 0.31, 1.50)),
    "bolsas": (8.0, 12.0, "foto_bolsas_alimento.jpg", "calido", (0.24, 0.80, 1.30), (0.33, 0.62, 1.04)),
}
TR = 0.5          # duración de cada transición


def degradado(c1, c2):
    t = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    return np.repeat(np.array(c1, np.float32) * (1 - t) + np.array(c2, np.float32) * t, W, axis=1)


FONDO_MARRON = degradado((150, 100, 52), MARRON_OSC)
FONDO_VERDE = degradado((40, 90, 44), (12, 32, 16))


def fondo_textura(base, t, semilla):
    """Fondo de color con 'virutas' que flotan suavemente."""
    f = base * (1 - 0.30 * _r[..., None] ** 2)
    f = np.clip(f, 0, 255).astype(np.uint8)
    rng = np.random.default_rng(semilla)
    ov = f.copy()
    for _ in range(26):
        x, y, v, a0, s = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(20, 60), rng.uniform(0, 180), rng.uniform(0.6, 1.4)
        cx, cy = x + 20 * np.sin(t + a0), (y - v * t) % (H + 60) - 30
        cv2.ellipse(ov, (int(cx), int(cy)), (int(16 * s), int(5 * s)), (a0 + t * 25) % 180, 0, 360, VIRUTA, -1, cv2.LINE_AA)
    return cv2.addWeighted(ov, 0.22, f, 0.78, 0)


# ============================================================ capas de texto
class Capas:
    def __init__(self):
        self.t1 = T(TEXTOS["t1"], ANTON, ajustar(TEXTOS["t1"], ANTON, 150, 980), AMARILLO, 0)
        self.t2a = T(TEXTOS["t2a"], ANTON, 92)
        self.t2b = T(TEXTOS["t2b"], ANTON, 150, AMARILLO)
        self.t3a = T(TEXTOS["t3a"], ANTON, 110)
        self.t3b = T(TEXTOS["t3b"], ANTON, 140, AMARILLO)
        self.t4a = T(TEXTOS["t4a"].upper(), ANTON, 150, BLANCO)
        self.t4b = T(TEXTOS["t4b"].upper(), ANTON, 150, AMARILLO)
        self.punto = caja(34, 34, 17, AMARILLO)
        self.t5 = T(TEXTOS["t5"], ANTON, 132, AMARILLO)
        self.logo = fp.logo_circular(210)
        self.nombre = T(DATOS["nombre"], ANTON, 76)
        self.rubro = T(DATOS["rubro"], MONT, 38, AMARILLO, sombra=0.4)
        self.filas = self._filas()
        self._subs = {}

    def _filas(self):
        """Tarjetas del cierre: dirección, horarios, pagos y WhatsApp (letra grande)."""
        def poner(base, txt, ruta, tam, col, x, y, derecha=False):
            spr = T(txt, ruta, tam, col, sombra=0)
            pad = int(tam * 0.35)
            if derecha:
                x = x - (spr.shape[1] - 2 * pad)
            return sobre(base, spr, int(x - pad), int(y - pad))

        def tarjeta(h):
            return caja(960, h, 30, (0, 0, 0), 0.48)
        filas = []
        c = tarjeta(164)
        c = sobre(c, fp.icono_pin(76), 30, 44)
        c = poner(c, DATOS["direccion"][0], ANTON, 66, BLANCO, 130, 12)
        c = poner(c, DATOS["direccion"][1], MONT, 42, AMARILLO, 132, 104)
        filas.append((c, 164))
        c = tarjeta(194)
        for k, (dia, hora) in enumerate(DATOS["horarios"]):
            y = 14 + k * 86
            c = poner(c, dia, MONT, 42, AMARILLO, 40, y + 10)
            c = poner(c, hora, ANTON, 62, BLANCO, 925, y, derecha=True)
        filas.append((c, 194))
        c = tarjeta(150)
        c = poner(c, "Formas de pago", MONT, 36, AMARILLO, 40, 16)
        c = poner(c, DATOS["pagos"], MONT, ajustar(DATOS["pagos"], MONT, 44, 880), BLANCO, 40, 74)
        filas.append((c, 150))
        c = tarjeta(226)
        c = poner(c, "WhatsApp", MONT, 36, AMARILLO, 925, 20, derecha=True)
        for k, num in enumerate(DATOS["whatsapp"]):
            y = 12 + k * 104
            c = sobre(c, fp.icono_whatsapp(74), 32, y + 16)
            c = poner(c, num, ANTON, 76, BLANCO, 130, y - 6)
        filas.append((c, 226))
        return filas

    def subtitulo(self, f, partes, t_ent):
        clave = tuple(partes)
        if clave not in self._subs:
            tam = 74
            s = sprite(partes, MONT, tam, 8, NEGRO, 0.5)
            while s.shape[1] > W - 50 and tam > 36:
                tam -= 4
                s = sprite(partes, MONT, tam, 8, NEGRO, 0.5)
            self._subs[clave] = s
        q = e_back(prog(t_ent, 0, 0.16), 2.0)
        blit(f, self._subs[clave], W / 2, 1450, alpha=clamp01(t_ent / 0.08), escala=0.9 + 0.1 * q)


# ============================================================ video
class Video:
    def __init__(self):
        self.fotos = {k: Foto(v[2], v[3]) for k, v in ESC.items()}
        self.c = Capas()
        self.voces = []
        for t0, txt, sub in VOZ:
            audio, tiempos = voz_tts.clip_palabras(txt, voz=VOZ_NOMBRE, rate=VOZ_VEL)
            bloques = [b.split() for b in sub.split("|")]
            assert sum(len(b) for b in bloques) == len(txt.split()), txt
            self.voces.append(dict(t0=t0, audio=audio, tiempos=tiempos, dur=len(audio) / SR, bloques=bloques))

    # --- escenas
    def foto(self, k, t):
        a, b, _, _, ini, fin = ESC[k]
        p = clamp01((t - a + TR / 2) / (b - a + TR))
        f = self.fotos[k].cuadro(p, ini, fin, VIG)
        return (f.astype(np.float32) * GRAD).astype(np.uint8)

    def titulo(self, f, t):
        c = self.c
        if t < 4.2:
            q = prog(t, 0.3, 0.5)
            blit(f, c.t1, W / 2, 420 + (1 - e_out(q)) * 60, alpha=clamp01(q * 3), escala=max(e_back(q, 1.8), 0.01))
        elif t < 8.2:
            tl = t - 4.0
            q = prog(tl, 0.35, 0.5)
            blit(f, c.t2a, W / 2 - (1 - e_out(q)) * W, 380, alpha=clamp01(q * 3))
            q = prog(tl, 0.6, 0.5)
            blit(f, c.t2b, W / 2, 500, alpha=clamp01(q * 3), escala=max(e_back(q, 1.8), 0.01))
        elif t < 12.2:
            tl = t - 8.0
            q = prog(tl, 0.35, 0.5)
            blit(f, c.t3a, W / 2 - (1 - e_out(q)) * W, 390, alpha=clamp01(q * 3))
            q = prog(tl, 0.6, 0.5)
            blit(f, c.t3b, W / 2 + (1 - e_out(q)) * W, 520, alpha=clamp01(q * 3))

    def calidad(self, t):
        tl = t - 12.0
        f = fondo_textura(FONDO_MARRON, t, 3)
        c = self.c
        v = self.voces[2]
        t_cal = v["t0"] + v["tiempos"][3] - 12.0 - 0.15     # "calidad"
        t_pre = v["t0"] + v["tiempos"][7] - 12.0 - 0.15     # "precio"
        q = prog(tl, min(0.3, t_cal), 0.5)
        blit(f, c.t4a, W / 2, 760, alpha=clamp01(q * 3), escala=max(e_back(q, 1.8), 0.01))
        q = prog(tl, t_pre - 0.3, 0.3)
        blit(f, c.punto, W / 2, 890, alpha=clamp01(q * 3), escala=max(e_back(q, 2.4), 0.01))
        q = prog(tl, t_pre, 0.5)
        blit(f, c.t4b, W / 2, 1020, alpha=clamp01(q * 3), escala=max(e_back(q, 1.8), 0.01))
        return f

    def cierre(self, t):
        tl = t - 15.0
        f = fondo_textura(FONDO_VERDE, t, 5)
        c = self.c
        q = prog(tl, 0.1, 0.45)
        blit(f, c.t5, W / 2, 300, alpha=clamp01(q * 3), escala=max(e_back(q, 1.8), 0.01))
        q = prog(tl, 0.35, 0.5)
        blit(f, c.logo, 175, 478, alpha=clamp01(q * 3), escala=max(e_back(q, 1.6), 0.01))
        q = prog(tl, 0.45, 0.45)
        blit(f, c.nombre, 630, 455 - (1 - e_out(q)) * 30, alpha=clamp01(q * 3))
        blit(f, c.rubro, 630, 525, alpha=clamp01(prog(tl, 0.6, 0.4) * 3))
        y = 615
        for i, (fila, h) in enumerate(c.filas):
            q = prog(tl, 0.7 + 0.22 * i, 0.45)
            blit(f, fila, W / 2 + (1 - e_out(q)) * (W if i % 2 == 0 else -W), y + h / 2, alpha=clamp01(q * 3))
            y += h + 18
        return f

    def base(self, t):
        if t < 4.0 - TR / 2:
            return self.foto("chico", t)
        if t < 4.0 + TR / 2:
            return deslizar(self.foto("chico", t), self.foto("camion", t), (t - 3.75) / TR)
        if t < 8.0 - TR / 2:
            return self.foto("camion", t)
        if t < 8.0 + TR / 2:
            return deslizar(self.foto("camion", t), self.foto("bolsas", t), (t - 7.75) / TR)
        if t < 12.0 - TR / 2:
            return self.foto("bolsas", t)
        if t < 12.0 + TR / 2:
            return fundido(self.foto("bolsas", t), self.calidad(max(t, 12.0)), (t - 11.75) / TR)
        if t < 15.0 - TR / 2:
            return self.calidad(t)
        if t < 15.0 + TR / 2:
            return fundido(self.calidad(t), self.cierre(max(t, 15.0)), (t - 14.75) / TR)
        return self.cierre(t)

    def subtitulos(self, f, t):
        for v in self.voces:
            if not (v["t0"] - 0.05 <= t <= v["t0"] + v["dur"] + 0.45):
                continue
            tiempos = [v["t0"] + x for x in v["tiempos"]]
            i = 0
            for bi, b in enumerate(v["bloques"]):
                ini = tiempos[i] - 0.05
                fin = tiempos[i + len(b)] - 0.05 if bi + 1 < len(v["bloques"]) else v["t0"] + v["dur"] + 0.45
                if ini <= t < fin:
                    partes = []
                    for j, w in enumerate(b):
                        hablada = tiempos[i + j] - 0.03 <= t
                        col = AMARILLO if (w.startswith("*") and hablada) else BLANCO
                        partes.append((w.replace("*", "") + (" " if j < len(b) - 1 else ""), col))
                    self.c.subtitulo(f, partes, t - ini)
                    return
                i += len(b)

    def frame(self, t):
        t = min(t, DUR - 1e-3)
        f = np.ascontiguousarray(self.base(t))
        self.titulo(f, t)
        self.subtitulos(f, t)
        if t < 0.3:                                            # entrada suave desde negro
            f = (f.astype(np.float32) * (t / 0.3)).astype(np.uint8)
        if t > DUR - 0.4:                                      # salida suave
            f = (f.astype(np.float32) * ((DUR - t) / 0.4)).astype(np.uint8)
        return f

    def audio(self, ruta):
        n = int(DUR * SR)
        voz = np.zeros(n, np.float32)
        for v in self.voces:
            x = v["audio"] * (10 ** (-18 / 20) / (np.sqrt((v["audio"] ** 2).mean()) + 1e-9))
            i = int(v["t0"] * SR)
            voz[i:i + x.size] += x[:max(0, n - i)]
        tmp = ruta.replace(".wav", "_crudo.wav")
        from scipy.io import wavfile
        wavfile.write(tmp, SR, voz)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af",
                        "highpass=f=80,acompressor=threshold=-20dB:ratio=2:attack=10:release=150,"
                        "loudnorm=I=-14:TP=-1.5:LRA=7", "-ar", "48000", "-ac", "2", ruta], check=True)
        return ruta


def deslizar(a, b, p):
    """Deslizamiento suave lateral."""
    e = e_inout(p)
    off = int(e * W)
    out = np.empty_like(a)
    out[:, :W - off] = a[:, off:]
    out[:, W - off:] = b[:, :off]
    return out


def fundido(a, b, p):
    e = e_inout(p)
    return cv2.addWeighted(a, 1 - e, b, e, 0)


def main():
    v = Video()
    if "--cuadros" in sys.argv:
        os.makedirs(os.path.join(AQUI, "previas"), exist_ok=True)
        for s in [float(x) for x in sys.argv[sys.argv.index("--cuadros") + 1:]]:
            Image.fromarray(v.frame(s)).save(os.path.join(AQUI, "previas", f"{s:05.2f}.png"))
        return
    wav = v.audio(os.path.join(AQUI, "_voz.wav"))
    n = int(DUR * FPS)
    sal_voz = os.path.join(AQUI, "forralitas_viruta_9x16.mp4")
    sal_mudo = os.path.join(AQUI, "forralitas_viruta_9x16_sin_audio.mp4")
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-profile:v", "high",
           "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
           "-shortest", "-movflags", "+faststart", sal_voz + ".tmp.mp4"]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(v.frame(i / FPS).tobytes())
    p.stdin.close()
    p.wait()
    os.replace(sal_voz + ".tmp.mp4", sal_voz)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", sal_voz, "-an", "-c:v", "copy", "-movflags", "+faststart",
                    sal_mudo], check=True)
    os.remove(wav)
    print("Listo:", sal_voz, "|", sal_mudo)


if __name__ == "__main__":
    main()
