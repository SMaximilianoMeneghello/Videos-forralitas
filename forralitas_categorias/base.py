"""Base común para los videos por categoría (caballos, chanchos, gallinas, mascotas).

Voz (edge-tts, es-AR), música con ducking, subtítulos con estilo configurable, cierre con los datos del
local y exportación (versión con voz y versión solo música).
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
sys.path.insert(0, os.path.join(RAIZ, "forralitas_video_final", "proyecto"))
sys.path.insert(0, RAIZ)
import forralitas_promo as fp      # noqa: E402  (utilidades de texto y dibujo; cambia el cwd)
import voz_tts                     # noqa: E402
import audio as sfxlib             # noqa: E402
from efectos import icono          # noqa: E402

W, H, FPS, SR = 1080, 1920, 30, 44100
e_out, e_inout, e_back, prog, clamp01 = fp.e_out, fp.e_inout, fp.e_back, fp.prog, fp.clamp01
blit, caja, sobre = fp.blit, fp.caja, fp.sobre
ANTON = os.path.join(RAIZ, "forralitas_video_final", "proyecto", fp.F_ANTON)
MONT = os.path.join(RAIZ, "forralitas_video_final", "proyecto", fp.F_MONT)
RYE = os.path.join(AQUI, "fuentes", "Rye.ttf")
SLAB = os.path.join(AQUI, "fuentes", "AlfaSlabOne.ttf")
FREDOKA = os.path.join(AQUI, "fuentes", "Fredoka.ttf")
LILITA = os.path.join(AQUI, "fuentes", "LilitaOne.ttf")
BALOO = os.path.join(AQUI, "fuentes", "Baloo2.ttf")
SALIDA = os.path.join(AQUI, "videos")

# Datos del local (los de siempre; no cambiar sin confirmarlo)
DATOS = {
    "nombre": "FORRAJERÍA FORRALITAS",
    "rubro": "Forrajería y Semillería",
    "direccion": ("Ruta 305 km 7,5", "Las Talitas"),
    "horarios": (("Lunes a viernes", "8:00 a 19:00"), ("Sábados", "8:30 a 19:00")),
    "pagos": "Efectivo · Transferencia · Débito · Crédito",
    "servicios": ("Envíos según la zona", "Venta por mayor y menor"),
    "whatsapp": ("381 526 9004", "381 633 4344"),
}
VOZ_NOMBRE, VOZ_VEL = "es-AR-TomasNeural", "+4%"


# ============================================================ utilidades
def ruta(rel):
    return os.path.join(RAIZ, rel)


def foto(rel, max_lado=2600):
    im = Image.open(ruta(rel)).convert("RGB")
    s = min(1.0, max_lado / max(im.size))
    if s < 1:
        im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    return np.asarray(im)


def recorte_png(rel, alto):
    """PNG con transparencia, recortado a su contenido y escalado a `alto` (sprite premultiplicado)."""
    im = Image.open(ruta(rel)).convert("RGBA")
    im = im.crop(im.getchannel("A").point(lambda v: 255 if v > 20 else 0).getbbox())
    im = im.resize((int(im.width * alto / im.height), alto), Image.LANCZOS)
    a = np.asarray(im, np.float32)
    a[..., :3] *= a[..., 3:4] / 255
    a[..., 3] /= 255
    return a


def realzar(rgb, sat=1.10, cont=0.14, brillo=1.03):
    x = rgb.astype(np.float32) / 255 * brillo
    g = x.mean(2, keepdims=True)
    x = np.clip(g + (x - g) * sat, 0, 1)
    x = (1 - cont) * x + cont * (x * x * (3 - 2 * x))
    return (x * 255).astype(np.uint8)


def cover(img, w, h, cx=0.5, cy=0.5, z=1.0):
    return fp.recorte(img, w, h, cx, cy, z)


def T(txt, fuente, tam, col, trazo=0, trazo_col=(0, 0, 0), sombra=0.0, esp=0):
    return fp.sprite([(txt, col)], fuente, tam, trazo, trazo_col, sombra, esp)


def ajustar(txt, fuente, tam, max_w):
    while fp.fuente(fuente, tam).getlength(txt) > max_w and tam > 18:
        tam -= 2
    return tam


def centrar(base, spr, cx, cy):
    return sobre(base, spr, int(round(cx - spr.shape[1] / 2)), int(round(cy - spr.shape[0] / 2)))


def sombra(spr, blur=18, op=0.30, pad=40):
    h, w = spr.shape[:2]
    a = np.zeros((h + 2 * pad, w + 2 * pad), np.float32)
    a[pad:pad + h, pad:pad + w] = spr[..., 3]
    a = cv2.GaussianBlur(a, (0, 0), blur) * op
    return np.dstack([np.zeros(a.shape + (3,), np.float32), a])


def a_sprite(rgb, mascara):
    return np.dstack([rgb.astype(np.float32) * mascara[..., None], mascara])


def mascara_redonda(w, h, r):
    return caja(w, h, r, (255, 255, 255))[..., 3]


def mascara_circulo(d):
    m = np.zeros((d * 3, d * 3), np.uint8)
    cv2.circle(m, (d * 3 // 2, d * 3 // 2), d * 3 // 2 - 2, 255, -1, cv2.LINE_AA)
    return cv2.resize(m, (d, d), interpolation=cv2.INTER_AREA).astype(np.float32) / 255


def fundido(a, b, p):
    e = e_inout(p)
    return cv2.addWeighted(a, 1 - e, b, e, 0)


# ============================================================ voz
class Guion:
    """lista: [(clave, texto voz, subtítulo)]. En el subtítulo: *resaltado*, | separa bloques, _ = no se muestra."""

    def __init__(self, lista):
        self.v = {}
        self.orden = []
        for clave, txt, sub in lista:
            audio, tiempos = voz_tts.clip_palabras(txt, voz=VOZ_NOMBRE, rate=VOZ_VEL)
            assert len(sub.replace("|", "").split()) == len(txt.split()), clave
            self.v[clave] = dict(audio=audio, tiempos=tiempos, dur=len(audio) / SR, txt=txt, t0=None,
                                 bloques=[b.split() for b in sub.split("|")])
            self.orden.append(clave)

    def __getitem__(self, k):
        return self.v[k]

    def fin(self, k):
        return self.v[k]["t0"] + self.v[k]["dur"]

    def palabra(self, k, i):
        return self.v[k]["t0"] + self.v[k]["tiempos"][i]


def subtitulos(f, guion, t, estilo, cache):
    """estilo: fuente, tam, color, resaltado, y, caja (color o None), caja_alpha, trazo, trazo_col, radio."""
    for v in guion.v.values():
        if v["t0"] is None or not (v["t0"] - 0.05 <= t <= v["t0"] + v["dur"] + 0.45):
            continue
        tiempos = [v["t0"] + x for x in v["tiempos"]]
        i = 0
        for bi, b in enumerate(v["bloques"]):
            ini = tiempos[i] - 0.05
            fin = tiempos[i + len(b)] - 0.05 if bi + 1 < len(v["bloques"]) else v["t0"] + v["dur"] + 0.45
            if ini <= t < fin:
                vis = [(j, w) for j, w in enumerate(b) if w != "_"]
                partes = []
                for n, (j, w) in enumerate(vis):
                    dicha = tiempos[i + j] - 0.03 <= t
                    col = estilo["resaltado"] if (w.startswith("*") and dicha) else estilo["color"]
                    partes.append((w.replace("*", "") + (" " if n < len(vis) - 1 else ""), col))
                k = tuple(partes)
                if k not in cache:
                    tam = estilo["tam"]
                    mk = lambda tm: fp.sprite(partes, estilo["fuente"], tm, estilo.get("trazo", 0),
                                              estilo.get("trazo_col", (0, 0, 0)), estilo.get("sombra", 0.0))
                    s = mk(tam)
                    while s.shape[1] > W - 140 and tam > 30:
                        tam -= 4
                        s = mk(tam)
                    if estilo.get("caja") is not None:
                        pad = int(tam * 0.35) + estilo.get("trazo", 0)
                        w, h = s.shape[1] - 2 * pad + int(tam * 1.1), int(tam * 1.65)
                        base = centrar(caja(w, h, estilo.get("radio", h // 2), estilo["caja"], estilo.get("caja_alpha", 1.0)),
                                       s, w / 2, h / 2 + tam * 0.04)
                        cache[k] = (base, sombra(base, 10, 0.22))
                    else:
                        cache[k] = (s, None)
                spr, sh = cache[k]
                q = e_back(prog(t - ini, 0, 0.16), 2.0)
                a = clamp01((t - ini) / 0.08)
                if sh is not None:
                    blit(f, sh, W / 2 + 3, estilo["y"] + 8, alpha=a, escala=0.9 + 0.1 * q)
                blit(f, spr, W / 2, estilo["y"], alpha=a, escala=0.9 + 0.1 * q)
                return
            i += len(b)


# ============================================================ cierre con los datos del local
class Cierre:
    """Piezas del cierre, con colores y fuentes de cada estilo.
    e: titulo_f, texto_f, num_f, col_titulo, col_texto, col_sub, tarjeta, tarjeta_alpha, ic_fondo, ic_tinta,
       espera (texto), col_espera, espera_f, logo (bool)"""

    def __init__(self, e):
        self.e = e
        self.logo = fp.logo_circular(170)
        self.nombre = T(DATOS["nombre"], e["titulo_f"], ajustar(DATOS["nombre"], e["titulo_f"], 72, 700), e["col_titulo"])
        self.rubro = T(DATOS["rubro"], e["texto_f"], 36, e["col_sub"])
        esp = e.get("espera", "¡TE ESPERAMOS!")
        self.espera = T(esp, e["espera_f"], ajustar(esp, e["espera_f"], 124, 960), e["col_espera"], sombra=e.get("sombra", 0.0))
        ic = lambda n: icono(n, 84, e["ic_fondo"], e["ic_tinta"])

        def fila(icn, lineas, alto):
            base = caja(960, alto, 30, e["tarjeta"], e["tarjeta_alpha"])
            base = centrar(base, icn, 72, alto / 2)
            y = alto / 2 - (len(lineas) - 1) * 31
            for txt, fuente, tam, col in lineas:
                s = T(txt, fuente, ajustar(txt, fuente, tam, 790), col)
                base = sobre(base, s, int(136 - tam * 0.35), int(y - s.shape[0] / 2))
                y += 62
            return base
        tf, nf = e["texto_f"], e["num_f"]
        ct, cs = e["col_texto"], e["col_sub"]
        self.filas = [
            fila(ic("ubicacion"), [(DATOS["direccion"][0], nf, 54, ct), (DATOS["direccion"][1], tf, 36, cs)], 150),
            fila(ic("reloj"), [(DATOS["horarios"][0][0] + "  " + DATOS["horarios"][0][1], tf, 38, ct),
                               (DATOS["horarios"][1][0] + "  " + DATOS["horarios"][1][1], tf, 38, ct)], 150),
            fila(ic("efectivo"), [("Formas de pago", tf, 32, cs), (DATOS["pagos"], tf, 38, ct)], 150),
            fila(ic("camion"), [(DATOS["servicios"][0], tf, 38, ct), (DATOS["servicios"][1], tf, 38, ct)], 150),
            fila(fp.icono_whatsapp(84), [(DATOS["whatsapp"][0], nf, 60, ct), (DATOS["whatsapp"][1], nf, 60, ct)], 170),
        ]
        self.sombras = [sombra(x, 10, 0.18) for x in self.filas]

    def dibujar(self, f, tl, y0=180, desde="izq"):
        """Dibuja el cierre (sin fondo) con tl = segundos desde que empieza."""
        q = prog(tl, 0.05, 0.5)
        blit(f, self.logo, 150, y0, alpha=clamp01(q * 3), escala=max(e_back(q, 1.6), 0.01))
        q = prog(tl, 0.2, 0.45)
        blit(f, self.nombre, 610, y0 - 25 - (1 - e_out(q)) * 30, alpha=clamp01(q * 3))
        blit(f, self.rubro, 610, y0 + 45, alpha=clamp01(prog(tl, 0.35, 0.4) * 3))
        q = prog(tl, 0.35, 0.45)
        blit(f, self.espera, W / 2, y0 + 205, alpha=clamp01(q * 3), escala=max(e_back(q, 1.8), 0.01))
        y = y0 + 345
        for i, (fila, sh) in enumerate(zip(self.filas, self.sombras)):
            h = fila.shape[0]
            q = prog(tl, 0.7 + 0.2 * i, 0.45)
            sgn = -1 if (desde == "izq" or (desde == "alterno" and i % 2 == 0)) else 1
            dx = sgn * (1 - e_out(q)) * W
            blit(f, sh, W / 2 + 4 + dx, y + h / 2 + 6, alpha=clamp01(q * 3))
            blit(f, fila, W / 2 + dx, y + h / 2, alpha=clamp01(q * 3))
            y += h + 16


# ============================================================ audio y exportación
def mezclar_audio(dur, guion, musica, inicio, sfx, ruta_wav, con_voz=True, nivel_musica=-20):
    """sfx: lista de (segundo, tipo) con tipo en {"whoosh", "golpe", "pop"}."""
    n = int(dur * SR)
    voz = np.zeros(n, np.float32)
    if con_voz:
        for v in guion.v.values():
            x = v["audio"] * (10 ** (-17 / 20) / (np.sqrt((v["audio"] ** 2).mean()) + 1e-9))
            i = int(v["t0"] * SR)
            voz[i:i + x.size] += x[:max(0, n - i)]
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(inicio), "-t", str(dur + 1), "-i", musica,
                          "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
    mus = np.frombuffer(raw, np.float32).reshape(-1, 2)[:n].copy()
    if len(mus) < n:
        mus = np.pad(mus, ((0, n - len(mus)), (0, 0)))
    mus *= 10 ** (nivel_musica / 20) / (np.sqrt((mus ** 2).mean()) + 1e-9)
    if con_voz:
        env = np.sqrt(np.convolve(voz ** 2, np.ones(int(0.04 * SR)) / int(0.04 * SR), mode="same"))
        act = (env > 0.01).astype(np.float32)
        k = int(0.3 * SR)
        sm = np.convolve(np.pad(act, (k, k), mode="edge"), np.ones(k) / k, mode="same")[k:-k]
        mus *= (1 - 0.65 * np.clip(sm * 1.4, 0, 1))[:, None]
    mus[:int(0.05 * SR)] *= np.linspace(0, 1, int(0.05 * SR))[:, None]
    fo = int(1.5 * SR)
    mus[-fo:] *= np.linspace(1, 0, fo)[:, None]
    fx = np.zeros(n, np.float32)
    pop = np.sin(2 * np.pi * 880 * np.arange(int(0.07 * SR)) / SR) * np.exp(-np.arange(int(0.07 * SR)) / SR * 60)
    for t, tipo in sfx:
        x, g = {"whoosh": (sfxlib.whoosh(0.45), 0.08), "golpe": (sfxlib.golpe(), 0.18), "pop": (pop, 0.05)}[tipo]
        i = int(t * SR)
        if 0 <= i < n:
            m = min(len(x), n - i)
            fx[i:i + m] += x[:m] * g
    mix = mus + (voz + fx)[:, None]
    tmp = ruta_wav.replace(".wav", "_crudo.wav")
    wavfile.write(tmp, SR, np.clip(mix, -1, 1).astype(np.float32))
    cadena = "acompressor=threshold=-20dB:ratio=2.2:attack=12:release=160:makeup=2"
    med = subprocess.run(["ffmpeg", "-hide_banner", "-i", tmp, "-af", cadena + ",loudnorm=I=-14:TP=-1.5:LRA=8:print_format=json",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    j = json.loads(med[med.rfind("{"):med.rfind("}") + 1])
    ln = (f"loudnorm=I=-14:TP=-1.5:LRA=8:measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
          f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af", f"{cadena},{ln},alimiter=limit=0.89:level=false",
                    "-ar", "48000", "-ac", "2", ruta_wav], check=True)
    os.remove(tmp)
    return ruta_wav


def ejecutar(video, nombre):
    """--cuadros s1 s2 ... → previas; sin argumentos → render completo (con voz y solo música)."""
    print(nombre, "duración", round(video.dur, 2), "| voces",
          {k: (round(v["t0"], 2), round(v["dur"], 2)) for k, v in video.guion.v.items()})
    if "--cuadros" in sys.argv:
        d = os.path.join(AQUI, "previas", nombre)
        os.makedirs(d, exist_ok=True)
        for s in [float(x) for x in sys.argv[sys.argv.index("--cuadros") + 1:]]:
            Image.fromarray(video.frame(s)).save(os.path.join(d, f"{s:05.2f}.png"))
        return
    os.makedirs(SALIDA, exist_ok=True)
    base = os.path.join(SALIDA, nombre)
    wav = mezclar_audio(video.dur, video.guion, video.musica, video.musica_inicio, video.sfx(), base + "_voz.wav")
    wav2 = mezclar_audio(video.dur, video.guion, video.musica, video.musica_inicio, video.sfx(), base + "_mus.wav", False)
    tmp = base + "_video.mp4"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-profile:v", "high", "-preset", "slow",
                          "-crf", "18", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for i in range(int(video.dur * FPS)):
        p.stdin.write(np.ascontiguousarray(video.frame(i / FPS)).tobytes())
    p.stdin.close()
    p.wait()
    for w, s in ((wav, base + "_9x16.mp4"), (wav2, base + "_9x16_solo_musica.mp4")):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-i", w, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-shortest", "-movflags", "+faststart", s], check=True)
        os.remove(w)
    os.remove(tmp)
    print("Listo:", base + "_9x16.mp4")
