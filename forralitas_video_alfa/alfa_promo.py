"""Video "¡Llegó alfa verde!" — Forrajería Forralitas (vertical 1080x1920, ~21 s).

Uso:  python alfa_promo.py                 → forralitas_alfa_9x16.mp4 (+ versión solo música)
      python alfa_promo.py --cuadros 1 5 9  → previas/
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
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, os.path.join(RAIZ, "forralitas_video_viruta"))
import viruta_promo as v1          # noqa: E402  (datos del cierre, textos, subtítulos)
import viruta_promo_v2 as v2       # noqa: E402  (cámara, temblor, flash, partículas)
import viruta_promo_v3 as v3       # noqa: E402  (luces cálidas, barras)
import audio as sfxlib             # noqa: E402
import voz_tts                     # noqa: E402

fp = v1.fp
W, H, FPS, SR = 1080, 1920, 30, 44100
MAT = os.path.join(AQUI, "material")
MUSICA, MUSICA_INICIO = os.path.join(AQUI, "musica", "Bama_Country.mp3"), 8.0
e_out, e_inout, e_back, prog, clamp01 = fp.e_out, fp.e_inout, fp.e_back, fp.prog, fp.clamp01
blit, caja, sobre = fp.blit, fp.caja, fp.sobre
AMARILLO, BLANCO, NEGRO, ANTON, MONT = v1.AMARILLO, v1.BLANCO, v1.NEGRO, v1.ANTON, v1.MONT
VERDE_ALFA, VERDE_OSC = (150, 214, 96), (22, 52, 26)

# ============================================================ guion (la voz dice exactamente esto)
VOZ = [
    (0.6, "¡Llegó alfa verde de la mejor calidad a nuestra forrajería!",
     "¡Llegó *alfa* *verde* | de la *mejor* *calidad* | a nuestra *forrajería!*"),
    (7.25, "¿Qué esperan para venir a visitarnos?", "¿Qué *esperan* | para venir a *visitarnos?*"),
    (10.55, "No se pierdan las mejores ofertas y precios, aquí en Forralitas.",
     "No se pierdan | las mejores *ofertas* *y* *precios,* | aquí en *Forralitas.*"),
]
VOZ_NOMBRE, VOZ_VEL = "es-AR-TomasNeural", "+0%"

# ============================================================ tomas
# (inicio, fin, fuente, encuadre inicial (cx, cy, zoom), final, perfil)
TOMAS = [
    (0.0, 2.6, "video:3.4", (0.50, 0.42, 1.25), (0.50, 0.40, 1.42), "neutro"),
    (2.6, 5.4, "foto02.jpg", (0.45, 0.45, 1.25), (0.50, 0.40, 1.05), "verde"),
    (5.4, 7.0, "video:9.0", (0.50, 0.45, 1.15), (0.50, 0.42, 1.30), "neutro"),
    (7.0, 8.9, "foto09.jpg", (0.62, 0.52, 1.10), (0.58, 0.50, 1.00), "neutro"),
    (8.9, 10.4, "foto05.jpg", (0.45, 0.45, 1.30), (0.48, 0.40, 1.12), "neutro"),
    (10.4, 12.0, "foto11.jpg", (0.42, 0.55, 1.00), (0.58, 0.55, 1.00), "neutro"),
    (12.0, 13.35, "foto10.jpg", (0.50, 0.45, 1.12), (0.50, 0.42, 1.02), "neutro"),
]
T_CIERRE, DUR = 13.35, 21.0
TRANS = {2.6: "flash", 5.4: "zoom", 7.0: "whip", 8.9: "corte", 10.4: "whip_v", 12.0: "corte"}


class Video:
    def __init__(self):
        cap = cv2.VideoCapture(os.path.join(MAT, "video_alfa.mp4"))
        self.vid = []
        while True:
            ok, f = cap.read()
            if not ok:
                break
            self.vid.append(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))
        self.fotos = {}
        self.grades = {}
        for a, b, src, ini, fin, perfil in TOMAS:
            if not src.startswith("video"):
                self.fotos[src] = np.asarray(Image.open(os.path.join(MAT, src)).convert("RGB"))
                muestra = self.fotos[src]
            else:
                muestra = self.vid[int(float(src.split(":")[1]) * 30)]
            self.grades[src] = fp.Grade(perfil, cv2.resize(muestra, (240, int(240 * muestra.shape[0] / muestra.shape[1]))))
        self.c = v1.Capas()
        self.voces = []
        for t0, txt, sub in VOZ:
            audio, tiempos = voz_tts.clip_palabras(txt, voz=VOZ_NOMBRE, rate=VOZ_VEL)
            bloques = [b.split() for b in sub.split("|")]
            assert sum(len(b) for b in bloques) == len(txt.split()), txt
            self.voces.append(dict(t0=t0, audio=audio, tiempos=tiempos, dur=len(audio) / SR, bloques=bloques))
        T = v1.T
        self.llego = T("¡LLEGÓ", ANTON, 180, BLANCO)
        self.alfa = T("ALFA VERDE!", ANTON, v1.ajustar("ALFA VERDE!", ANTON, 200, 1000), VERDE_ALFA)
        self.de_la = v2.resaltado("DE LA", 70, AMARILLO, VERDE_OSC)
        self.calidad = T("MEJOR CALIDAD", ANTON, v1.ajustar("MEJOR CALIDAD", ANTON, 160, 1000), AMARILLO)
        self.que = T("¿QUÉ ESPERAN", ANTON, v1.ajustar("¿QUÉ ESPERAN", ANTON, 150, 1000), BLANCO)
        self.visit = v2.resaltado("PARA VISITARNOS?", 90, AMARILLO, VERDE_OSC)
        self.no_se = v2.resaltado("NO SE PIERDAN", 70, BLANCO, VERDE_OSC)
        self.ofertas = T("LAS MEJORES", ANTON, 120, BLANCO)
        self.precios = T("OFERTAS Y PRECIOS", ANTON, v1.ajustar("OFERTAS Y PRECIOS", ANTON, 140, 1000), AMARILLO)
        v2.VIRUTA = (120, 170, 70)            # partículas color alfa
        self.hojas = v2.Virutas([(0.6, W / 2, H * 0.80, 22, 2100), (2.65, W / 2, H * 0.62, 14, 1800),
                                 (T_CIERRE + 0.15, W / 2, H * 0.30, 24, 2200)], semilla=21)
        self.fondo_cierre = None
        self.t_forr = self.t_palabra(2, 10)       # "Forralitas"

    def t_palabra(self, iv, iw):
        v = self.voces[iv]
        return v["t0"] + v["tiempos"][iw]

    # ---- imagen de una toma
    def toma(self, k, t):
        a, b, src, ini, fin, perfil = TOMAS[k]
        p = e_inout(clamp01((t - a) / (b - a))) * 0.85 + 0.15 * clamp01((t - a) / (b - a))
        cx, cy, z = (ini[i] + (fin[i] - ini[i]) * p for i in range(3))
        if src.startswith("video"):
            s0 = float(src.split(":")[1])
            img = self.vid[int(np.clip((s0 + (t - a)) * 30, 0, len(self.vid) - 1))]
        else:
            img = self.fotos[src]
        f = self.grades[src](fp.recorte(img, W, H, cx, cy, z), v1.VIG)
        return (f.astype(np.float32) * v1.GRAD).astype(np.uint8)

    def base(self, t):
        for k in range(1, len(TOMAS)):
            corte = TOMAS[k][0]
            tipo = TRANS[corte]
            d = {"flash": 0.3, "zoom": 0.4, "whip": 0.34, "whip_v": 0.34, "corte": 0.0}[tipo]
            if d and corte - d / 2 <= t < corte + d / 2:
                p = (t - (corte - d / 2)) / d
                a, b = self.toma(k - 1, min(t, corte - 1e-3)), self.toma(k, max(t, corte))
                if tipo == "flash":
                    base = b if p >= 0.5 else a
                    fl = 0.75 * np.exp(-((p - 0.5) / 0.18) ** 2)
                    return cv2.addWeighted(base, 1 - fl, np.full_like(base, (255, 246, 225)), fl, 0)
                if tipo == "zoom":
                    return v2.zoom_through(a, b, p)
                if tipo == "whip":
                    return v2.whip(a, b, p)
                return v2.whip_vertical(a, b, p)
        k = max(i for i in range(len(TOMAS)) if t >= TOMAS[i][0])
        f = self.toma(k, t)
        # salto de zoom en los cortes secos
        if TRANS.get(TOMAS[k][0]) == "corte":
            f = v2.camara(f, 1 + v2.punch(t, TOMAS[k][0], 0.05))
        return f

    # ---- títulos
    def titulos(self, f, t):
        if t < 2.75:
            q = prog(t, 0.45, 0.32)
            blit(f, self.llego, W / 2, 360, alpha=clamp01(q * 3), escala=max(2.4 - 1.4 * e_out(q), 0.01), ang=-3 * (1 - q))
            q = prog(t, 0.75, 0.38)
            blit(f, self.alfa, W / 2, 545, alpha=clamp01(q * 3), escala=max(e_back(q, 2.0), 0.01))
            v3.barra(f, W / 2, 660, 560, t, 1.05, VERDE_ALFA)
        elif t < 5.55:
            tl = t - 2.6
            q = prog(tl, 0.1, 0.4)
            blit(f, self.de_la, W / 2 - (1 - e_out(q)) * W, 360, alpha=clamp01(q * 3), ang=-3)
            q = prog(tl, 0.3, 0.4)
            blit(f, self.calidad, W / 2, 500, alpha=clamp01(q * 3), escala=max(2.0 - 1.0 * e_out(q), 0.01))
            v3.barra(f, W / 2, 615, 620, tl, 0.6)
        elif 7.0 <= t < 10.55:
            t_q = self.t_palabra(1, 0) - 0.15
            t_v = self.t_palabra(1, 3) - 0.2
            q = prog(t, t_q, 0.35)
            blit(f, self.que, W / 2, 380, alpha=clamp01(q * 3), escala=max(e_back(q, 2.0), 0.01))
            q = prog(t, t_v, 0.4)
            blit(f, self.visit, W / 2 + (1 - e_out(q)) * W, 540, alpha=clamp01(q * 3), ang=2)
        elif 10.4 <= t < T_CIERRE + 0.2:
            q = prog(t, self.t_palabra(2, 0) - 0.1, 0.35)
            blit(f, self.no_se, W / 2 - (1 - e_out(q)) * W, 330, alpha=clamp01(q * 3), ang=-3)
            q = prog(t, self.t_palabra(2, 3) - 0.15, 0.35)
            blit(f, self.ofertas, W / 2, 470, alpha=clamp01(q * 3), escala=max(e_back(q, 2.0), 0.01))
            q = prog(t, self.t_palabra(2, 5) - 0.15, 0.35)
            blit(f, self.precios, W / 2, 610, alpha=clamp01(q * 3), escala=max(2.0 - 1.0 * e_out(q), 0.01))

    def cierre(self, t):
        f = v1.Video.cierre(self, t - T_CIERRE + 15.0)
        tl = t - T_CIERRE
        dx, dy, a = v2.temblor(tl, 0.1, 16)
        return v2.camara(f, 1 + v2.punch(tl, 0.08, 0.04), dx, dy, a)

    def frame(self, t):
        t = min(t, DUR - 1e-3)
        if t < T_CIERRE - 0.2:
            f = np.ascontiguousarray(self.base(t))
            self.titulos(f, t)
        elif t < T_CIERRE + 0.2:
            a = np.ascontiguousarray(self.base(min(t, T_CIERRE - 1e-3)))
            self.titulos(a, t)
            f = v2.zoom_through(a, self.cierre(max(t, T_CIERRE)), (t - (T_CIERRE - 0.2)) / 0.4)
        else:
            f = self.cierre(t)
        f = np.ascontiguousarray(f)
        self.hojas.dibujar(f, t)
        f = v3.luces(f, t, 0.08 if t < T_CIERRE else 0.05)
        v1.Video.subtitulos(self, f, t)
        if t < 0.25:
            f = (f.astype(np.float32) * (t / 0.25)).astype(np.uint8)
        if t > DUR - 0.4:
            f = (f.astype(np.float32) * ((DUR - t) / 0.4)).astype(np.uint8)
        return f

    # ---- audio
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
        fo = int(1.4 * SR)
        mus[-fo:] *= np.linspace(1, 0, fo)[:, None]
        sfx = np.zeros(n, np.float32)

        def poner(x, t, g):
            i = int(t * SR)
            if 0 <= i < n:
                m = min(len(x), n - i)
                sfx[i:i + m] += x[:m] * g
        for t in (0.45, T_CIERRE + 0.08):
            poner(sfxlib.golpe(), t, 0.2)
        for corte, tipo in TRANS.items():
            if tipo in ("whip", "whip_v", "zoom"):
                poner(sfxlib.whoosh(0.4), corte - 0.2, 0.08)
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


def main():
    v = Video()
    if "--cuadros" in sys.argv:
        d = os.path.join(AQUI, "previas")
        os.makedirs(d, exist_ok=True)
        for s in [float(x) for x in sys.argv[sys.argv.index("--cuadros") + 1:]]:
            Image.fromarray(v.frame(s)).save(os.path.join(d, f"{s:05.2f}.png"))
        print("voces:", [(round(x["t0"], 2), round(x["dur"], 2)) for x in v.voces], "Forralitas en", round(v.t_forr, 2))
        return
    sal = os.path.join(AQUI, "forralitas_alfa_9x16.mp4")
    sal2 = os.path.join(AQUI, "forralitas_alfa_9x16_solo_musica.mp4")
    wav, wav2 = v.audio(os.path.join(AQUI, "_voz.wav")), v.audio(os.path.join(AQUI, "_sin_voz.wav"), con_voz=False)
    tmp = os.path.join(AQUI, "_video.mp4")
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-profile:v", "high", "-preset", "slow", "-crf", "17",
                          "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        p.stdin.write(v.frame(i / FPS).tobytes())
    p.stdin.close()
    p.wait()
    for w, s in ((wav, sal), (wav2, sal2)):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-i", w, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-shortest", "-movflags", "+faststart", s], check=True)
        os.remove(w)
    os.remove(tmp)
    print("Listo:", sal, "|", sal2)


if __name__ == "__main__":
    main()
