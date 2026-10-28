"""Versión 3 del video "¡Llegó la viruta!" — guion nuevo (la marca se nombra una sola vez en la voz)
y edición más cuidada: luces cálidas, títulos con barra que se dibuja, fondo de foto desenfocada en
"Mejor calidad / Mejor precio" y marca solo en el cierre.

Uso:  python viruta_promo_v3.py                 → forralitas_viruta_v3_9x16.mp4 (+ versión solo música)
      python viruta_promo_v3.py --cuadros 1 5 9  → previas_v3/
"""
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import viruta_promo_v2 as v2       # noqa: E402
import viruta_promo as v1          # noqa: E402

fp = v1.fp
W, H, FPS, DUR = v2.W, v2.H, v2.FPS, v2.DUR
e_out, e_inout, e_back, prog, clamp01 = fp.e_out, fp.e_inout, fp.e_back, fp.prog, fp.clamp01
blit, caja, sobre = fp.blit, fp.caja, fp.sobre
AMARILLO, BLANCO, MARRON_OSC, ANTON, MONT = v1.AMARILLO, v1.BLANCO, v1.MARRON_OSC, v1.ANTON, v1.MONT

# ============================================================ guion (FORRALITAS se nombra una vez)
v1.VOZ = [
    (0.55, "¡Llegó la viruta a Forralitas!", "¡Llegó la *viruta* | a *Forralitas!*"),
    (4.7, "Recién descargada del camión.", "Recién *descargada* | del *camión.*"),
    (8.35, "Y además, muchos productos más,", "Y además, | muchos *productos* *más,*"),
    (12.2, "con la mejor calidad y al mejor precio.", "con la *mejor* *calidad* | y al *mejor* *precio.*"),
    (15.25, "¡Te esperamos!", "*¡Te* *esperamos!*"),
]


# ============================================================ luces cálidas (light leaks)
_ly, _lx = np.mgrid[0:H // 8, 0:W // 8].astype(np.float32) * 8
FUGAS = [((255, 170, 70), 0.09, 0.0, 560), ((255, 120, 60), 0.07, 2.4, 480), ((255, 225, 150), 0.05, 4.1, 650)]


def luces(f, t, op):
    acc = np.zeros(_ly.shape + (3,), np.float32)
    for color, vel, fase, rad in FUGAS:
        cx = W * (0.5 + 0.7 * np.sin(t * vel * 6 + fase))
        cy = H * (0.45 + 0.5 * np.cos(t * vel * 4 + fase * 1.6))
        acc += np.exp(-(((_lx - cx) ** 2 + (_ly - cy) ** 2) / (2 * rad ** 2)))[..., None] * np.array(color, np.float32)
    acc = cv2.resize(acc, (W, H)) * op
    return np.clip(f.astype(np.float32) + acc, 0, 255).astype(np.uint8)


def barra(f, cx, y, ancho, t, t0, color=AMARILLO, grosor=12):
    """Barra que se dibuja desde el centro hacia los costados."""
    q = e_out(prog(t, t0, 0.45))
    if q > 0:
        a = int(ancho / 2 * q)
        cv2.rectangle(f, (int(cx - a), int(y)), (int(cx + a), int(y + grosor)), color, -1, cv2.LINE_AA)


# ============================================================ video
class Video(v2.Video):
    def __init__(self):
        super().__init__()
        self.ya = v2.resaltado("RECIÉN", 80, AMARILLO, MARRON_OSC)
        self.forr = v1.T("DESCARGADA", ANTON, v1.ajustar("DESCARGADA", ANTON, 168, 980), AMARILLO)
        self.ym = v2.resaltado("Y muchos", 84, BLANCO, MARRON_OSC)
        # fondo cálido desenfocado para "Mejor calidad / Mejor precio"
        foto = self.fotos["chico"]
        base = fp.recorte(foto.img, W // 3, H // 3, 0.62, 0.45, 1.25)
        base = cv2.resize(cv2.GaussianBlur(base, (0, 0), 7), (W, H)).astype(np.float32)
        base = base * np.array([1.05, 0.92, 0.75], np.float32) * 0.55
        self.fondo_cal = np.clip(base * v1.VIG, 0, 255).astype(np.uint8)
        # virutas: menos ráfagas, más suaves
        self.virutas = v2.Virutas([
            (0.30, W / 2, H * 0.78, 26, 2200),
            (5.30, W / 2, H * 0.82, 16, 1900),
            (self.t_pre, W / 2, H * 0.62, 16, 1900),
            (15.10, W / 2, H * 0.32, 26, 2200),
        ], semilla=11)

    def esc_chico(self, t):
        f = super().esc_chico(t)
        barra(f, W / 2, 650, 520, t, 0.75)
        return f

    def esc_camion(self, t):
        f = super().esc_camion(t)
        barra(f, W / 2, 565, 480, t - 4.0, 1.05)
        return f

    def esc_bolsas(self, t):
        f = super().esc_bolsas(t)
        barra(f, W / 2, 590, 560, t - 8.0, 0.9)
        return f

    def esc_calidad(self, t):
        tl = t - 12.0
        z = 1.04 + 0.05 * tl / 3
        M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, z)
        f = cv2.warpAffine(self.fondo_cal, M, (W, H), borderMode=cv2.BORDER_REFLECT)
        f = v1.fondo_textura(f.astype(np.float32), t, 3)
        for spr, t0, y, ang in ((self.s_cal, self.t_cal - 0.12, 780, -4), (self.s_pre, self.t_pre - 0.12, 1020, 3)):
            q = prog(t, t0, 0.3)
            if q > 0:
                blit(f, spr, W / 2, y + (1 - e_out(q)) * 40, alpha=clamp01(q * 3.5),
                     escala=1.9 - 0.9 * e_back(q, 1.4), ang=ang)
        dx, dy, a = v2.temblor(t, self.t_pre + 0.12, 14)
        f = v2.camara(f, 1.0, dx, dy, a)
        return v2.flash(f, t, self.t_pre + 0.1, 0.15, 0.35)

    def frame(self, t):
        t = min(t, DUR - 1e-3)
        f = np.ascontiguousarray(self.base(t))
        self.virutas.dibujar(f, t)
        f = luces(f, t, 0.10 if t < 15.0 else 0.06)
        self.subtitulos(f, t)
        if t < 0.25:
            f = (f.astype(np.float32) * (t / 0.25)).astype(np.uint8)
        if t > DUR - 0.35:
            f = (f.astype(np.float32) * ((DUR - t) / 0.35)).astype(np.uint8)
        return f


def main():
    v = Video()
    if "--cuadros" in sys.argv:
        d = os.path.join(AQUI, "previas_v3")
        os.makedirs(d, exist_ok=True)
        for s in [float(x) for x in sys.argv[sys.argv.index("--cuadros") + 1:]]:
            Image.fromarray(v.frame(s)).save(os.path.join(d, f"{s:05.2f}.png"))
        return
    sal = os.path.join(AQUI, "forralitas_viruta_v3_9x16.mp4")
    sal_sin_voz = os.path.join(AQUI, "forralitas_viruta_v3_9x16_solo_musica.mp4")
    wav = v.audio(os.path.join(AQUI, "_v3.wav"))
    wav2 = v.audio(os.path.join(AQUI, "_v3_sin_voz.wav"), con_voz=False)
    video_tmp = os.path.join(AQUI, "_v3_video.mp4")
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
