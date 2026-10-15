"""Video publicitario vertical (1080x1920) para la venta del PH de Rivadavia 2647.

Usa el metraje real del recorrido (assets_casa/entrada.mp4) con locución (voz
neuronal), música suave de fondo y textos animados con los datos de la
propiedad.

Uso:
    source .venv/bin/activate
    python casa_rivadavia.py                 # genera videos_salida/casa_rivadavia.mp4
    python casa_rivadavia.py --frames 2 10 60 # vistas previas (PNG)
    python casa_rivadavia.py --audio          # solo arma el audio mezclado
"""
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from moviepy import AudioFileClip, VideoClip, VideoFileClip
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

import audio_suave
import voz_tts
from efectos import (AMARILLO, BLANCO, VERDE_OSCURO, W, H, blit, caja, clamp01,
                     ease_out_back, ease_out_cubic, fondo_animado, icono, prog,
                     sobre, texto, ancho_texto)

FPS = 30
SR = voz_tts.SR
ENTRADA = "assets_casa/entrada.mp4"
SALIDA = "videos_salida/casa_rivadavia.mp4"
TEL = "381 526 9004"
DIRECCION = "Rivadavia 2647"
VOZ = "es-AR-ElenaNeural"

# ------------------------------------------------------------ guion (lo que se dice)
L_INTRO = "Vendo PH en Rivadavia, dos mil seiscientos cuarenta y siete."
L_BODY = [
    "Dos dormitorios grandes, cocina comedor y living.",
    "Baño y lavadero, con terraza propia.",
    "A solo cincuenta metros de avenida Francisco de Aguirre.",
    "Con cuatro líneas de colectivos a la puerta.",
    "La escuela te queda a cien metros.",
    "Y tenés todo tipo de comercios cerca.",
]
L_CIERRE = "Consultá ya. Tres ocho uno, cinco dos seis, nueve cero cero cuatro."

# textos en pantalla (paralelos a L_BODY). Las palabras con * salen en amarillo.
C_BODY = [
    "2 *dormitorios* grandes · Cocina comedor · Living",
    "Baño y *lavadero* · Terraza propia",
    "A 50 m de Av. *Francisco de Aguirre*",
    "4 líneas de *colectivos* a la puerta",
    "Escuela a *100 metros*",
    "Todo tipo de *comercios* cerca",
]

D_INTRO = 4.6
D_CIERRE = 7.5
GAP = 0.5


# ------------------------------------------------------------ texto ajustado con resaltado
def linea_resaltada(marcado, tam, max_w, color=BLANCO):
    pal = [(p.strip("*"), p.startswith("*")) for p in marcado.split()]
    while True:
        gap = tam * 0.28
        anchos = [ancho_texto(p, tam) for p, _ in pal]
        total = sum(anchos) + gap * (len(pal) - 1)
        if total <= max_w or tam <= 28:
            break
        tam -= 3
    sprites = [texto(p, tam, AMARILLO if d else color) for p, d in pal]
    x, xs = (W - total) / 2, []
    for a in anchos:
        xs.append(x)
        x += a + gap
    return sprites, xs


def texto_ajustado(txt, tam, max_w, color=BLANCO, sombra=False):
    while ancho_texto(txt, tam) > max_w and tam > 20:
        tam -= 2
    return texto(txt, tam, color, sombra)


# ------------------------------------------------------------ escena intro
def escena_intro(voz_dur):
    tit1 = texto("PH EN VENTA", 104, AMARILLO)
    tit2 = texto(DIRECCION, 80, BLANCO)
    sub = texto("A metros de Av. Francisco de Aguirre", 42, (210, 235, 210))

    def fn(t):
        f = fondo_animado(t, semilla=11)
        p1 = ease_out_cubic(prog(t, 0.25, 0.8))
        blit(f, tit1, W / 2, 760 + (1 - p1) * 60, alpha=p1, escala=max(ease_out_back(prog(t, 0.25, 0.8)), 0.01),
             centro=True)
        p2 = ease_out_cubic(prog(t, 0.75, 0.7))
        blit(f, tit2, W / 2, 900 + (1 - p2) * 40, alpha=p2, centro=True)
        linea = int(420 * ease_out_cubic(prog(t, 1.25, 0.5)))
        if linea > 0:
            cv2.rectangle(f, (W // 2 - linea // 2, 1010), (W // 2 + linea // 2, 1022), AMARILLO, -1, cv2.LINE_AA)
        p3 = ease_out_cubic(prog(t, 1.5, 0.6))
        blit(f, sub, W / 2, 1060, alpha=p3, centro=True)
        return f
    return fn


# ------------------------------------------------------------ escena cierre
def escena_cierre():
    tit = texto("¡CONSULTANOS YA!", 78, AMARILLO)
    ic_tel = icono("telefono", 150)
    num = texto_ajustado(TEL, 90, 760, BLANCO, True)
    tarjeta = sobre(caja(940, 220, 46, (3, 34, 14), 0.88), num, int((940 - num.shape[1]) / 2 + 60), int((220 - num.shape[0]) / 2))
    ic_ubic = icono("ubicacion", 90)
    dir1 = texto_ajustado(DIRECCION, 54, 760, BLANCO)
    tarjeta2 = sobre(sobre(caja(940, 150, 40, (3, 34, 14), 0.86), ic_ubic, 30, 30), dir1, 150, int((150 - dir1.shape[0]) / 2))
    pie = texto_ajustado("PH 2 dormitorios · Cocina comedor · Living · Terraza", 36, W - 80, (205, 235, 205))

    def fn(t):
        f = fondo_animado(t, semilla=19)
        p = ease_out_cubic(prog(t, 0.2, 0.7))
        blit(f, tit, W / 2, 330 + (1 - p) * 40, alpha=p, centro=True)

        q = prog(t, 0.6, 0.65)
        e = ease_out_cubic(q)
        x = (W - 940) / 2
        blit(f, tarjeta, x, 540 + (1 - e) * 60, alpha=clamp01(q * 2.5))
        if q > 0.1:
            fase = (t - 0.9) % 1.7
            env = max(0.0, 1 - fase / 0.55)
            ang = 18 * np.sin(fase * 50) * env if env > 0 else 0
            from efectos import rotar_sprite
            blit(f, rotar_sprite(ic_tel, ang), x + 70, 540 + 110, alpha=clamp01(q * 2.5),
                 escala=1 + 0.06 * env, centro=True)

        q2 = prog(t, 1.3, 0.65)
        e2 = ease_out_cubic(q2)
        blit(f, tarjeta2, x, 810 + (1 - e2) * 60, alpha=clamp01(q2 * 2.5))

        q3 = ease_out_cubic(prog(t, 2.0, 0.7))
        blit(f, pie, W / 2, 1040 + (1 - q3) * 30, alpha=q3, centro=True)
        return f
    return fn


# ------------------------------------------------------------ captions sobre el recorrido
def dibujar_badge():
    tag = texto("EN VENTA", 34, VERDE_OSCURO, sombra=False)
    pastilla = sobre(caja(tag.shape[1] + 50, tag.shape[0] + 6, 30, AMARILLO, 0.95), tag, 25, 0)
    dirsp = texto(DIRECCION, 34, BLANCO, sombra=True)
    dirpast = sobre(caja(dirsp.shape[1] + 46, dirsp.shape[0] + 4, 26, (3, 34, 14), 0.78), dirsp, 20, -1)
    return pastilla, dirpast


def construir_captions(inicios_body, b_dur):
    sprites = []
    for marcado, t0, dur in zip(C_BODY, inicios_body, b_dur):
        spr, xs = linea_resaltada(marcado, 52, W - 140)
        ancho = max(x + s.shape[1] for s, x in zip(spr, xs)) - min(xs)
        tot_w = ancho + 70
        fondo = caja(int(tot_w), 110, 32, (3, 34, 14), 0.72)
        off = min(xs)
        placa = fondo
        for s, x in zip(spr, xs):
            placa = sobre(placa, s, int(x - off + 35), int((110 - s.shape[0]) / 2))
        sprites.append((placa, t0, dur))
    return sprites


# ------------------------------------------------------------ construir linea de tiempo + voces
def construir():
    cl = lambda t, **kw: voz_tts.clip(t, voz=VOZ, **kw)
    dur = lambda x: len(x) / SR

    intro_voz = cl(L_INTRO)
    cierre_voz = cl(L_CIERRE)
    body_voces = [cl(t) for t in L_BODY]

    video = VideoFileClip(ENTRADA).resized(width=W)
    video = video.cropped(y_center=video.h / 2, height=H)
    dur_video = video.duration

    # repartir las 6 frases a lo largo del recorrido, dejando aire al principio y al final
    margen = 3.0
    usable = max(dur_video - 2 * margen, 10.0)
    n = len(body_voces)
    inicios_body = [margen + usable * (i + 0.5) / n - dur(body_voces[i]) / 2 for i in range(n)]
    inicios_body = [max(0.0, min(t, dur_video - dur(v) - 0.3)) for t, v in zip(inicios_body, body_voces)]

    total = D_INTRO + dur_video + D_CIERRE

    voces = [(0.5, intro_voz)]
    for t0, v in zip(inicios_body, body_voces):
        voces.append((D_INTRO + t0, v))
    voces.append((D_INTRO + dur_video + 0.9, cierre_voz))

    captions = construir_captions(inicios_body, [dur(v) for v in body_voces])
    return video, dur_video, total, voces, captions


# ------------------------------------------------------------ mezcla de audio
def _env(x, ms):
    k = max(1, int(SR * ms / 1000))
    return np.sqrt(np.convolve(x ** 2, np.ones(k) / k, mode="same"))


def mezclar(total, voces, ruta="videos_salida/_mezcla_casa.wav"):
    n = int(total * SR)
    voz = np.zeros(n, np.float32)
    for t0, x in voces:
        x = x * (10 ** (-18 / 20) / (np.sqrt((x ** 2).mean()) + 1e-9))
        x = np.tanh(x * 1.5) / 1.5
        i = int(t0 * SR)
        voz[i:i + x.size] += x[: max(0, n - i)]
    voz = sosfilt(butter(2, 70, btype="highpass", fs=SR, output="sos"), voz)

    musica = audio_suave.musica(total)
    musica = musica[:n] * (10 ** (-26 / 20) / (np.sqrt((musica ** 2).mean()) + 1e-9))
    activa = (_env(voz, 40) > 0.012).astype(np.float32)
    k = int(SR * 0.45)
    suave = np.convolve(np.pad(activa, (k, k), mode="edge"), np.ones(k) / k, mode="same")[k:-k]
    ganancia = 1 - 0.7 * np.clip(suave, 0, 1)

    mix = musica * ganancia[:, None] + np.repeat(voz[:, None], 2, axis=1)
    fi, fo = int(0.6 * SR), int(2.0 * SR)
    mix[:fi] *= np.linspace(0, 1, fi)[:, None]
    mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    mix = np.tanh(mix * 1.05)
    mix *= 0.9 / max(np.abs(mix).max(), 1e-6)
    tmp = "videos_salida/_mezcla_casa_cruda.wav"
    wavfile.write(tmp, SR, (mix * 32767).astype(np.int16))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af", "loudnorm=I=-16:TP=-1.5:LRA=9", "-ar", str(SR), ruta],
                   check=True)
    return ruta


# ------------------------------------------------------------ render
def hacer_frame_fn(video, dur_video, total, captions):
    fn_intro = escena_intro(None)
    fn_cierre = escena_cierre()
    badge, dirpast = dibujar_badge()
    TR = 0.6

    def make_frame(t):
        t = min(t, total - 1e-3)
        if t < D_INTRO:
            f = fn_intro(t)
            if t > D_INTRO - TR:
                p = (t - (D_INTRO - TR)) / TR
                fv = np.ascontiguousarray(video.get_frame(0))
                f = cv2.addWeighted(f, 1 - p, fv, p, 0)
            return f
        if t < D_INTRO + dur_video:
            tv = t - D_INTRO
            f = np.ascontiguousarray(video.get_frame(tv))
            if tv < TR:
                p = tv / TR
                fi = fn_intro(D_INTRO)
                f = cv2.addWeighted(fi, 1 - p, f, p, 0)
            if tv > dur_video - TR:
                p = (tv - (dur_video - TR)) / TR
                fc = fn_cierre(0)
                f = cv2.addWeighted(f, 1 - p, fc, p, 0)
            # viñeta suave arriba/abajo para legibilidad del texto
            yy = np.arange(H, dtype=np.float32)[:, None, None]
            top = np.clip(1 - (yy / 260), 0, 1) * 0.55
            bot = np.clip(1 - ((H - 1 - yy) / 420), 0, 1) * 0.6
            f = (f.astype(np.float32) * (1 - np.maximum(top, bot))).astype(np.uint8)
            ph = ease_out_cubic(prog(tv, 0.3, 0.6))
            blit(f, badge, 44, 70, alpha=ph)
            blit(f, dirpast, 44, 70 + badge.shape[0] + 14, alpha=ph)
            for placa, t0, d in captions:
                q = prog(tv, t0 - 0.25, 0.4)
                qf = prog(tv, t0 + d + 0.35, 0.4)
                alpha = clamp01(q) * (1 - clamp01(qf)) if tv >= t0 - 0.25 else 0
                if alpha > 0.01:
                    e = ease_out_cubic(q)
                    blit(f, placa, (W - placa.shape[1]) / 2, 1640 + (1 - e) * 35, alpha=alpha)
            return f
        tc = t - D_INTRO - dur_video
        f = fn_cierre(tc)
        if tc < TR:
            p = tc / TR
            fv = np.ascontiguousarray(video.get_frame(dur_video - 1e-2))
            f = cv2.addWeighted(fv, 1 - p, f, p, 0)
        return f
    return make_frame


def main():
    Path("videos_salida").mkdir(exist_ok=True)
    video, dur_video, total, voces, captions = construir()
    make_frame = hacer_frame_fn(video, dur_video, total, captions)

    if "--frames" in sys.argv:
        segundos = [float(x) for x in sys.argv[sys.argv.index("--frames") + 1:]]
        from PIL import Image
        for s in segundos:
            Image.fromarray(make_frame(s)).save(f"videos_salida/prev_casa_{s:05.1f}.png")
        print("duración total:", round(total, 2), "s")
        return

    audio_wav = mezclar(total, voces)
    print("audio listo:", audio_wav, f"({total:.1f} s)")
    if "--audio" in sys.argv:
        return

    clip = VideoClip(make_frame, duration=total).with_audio(AudioFileClip(audio_wav).subclipped(0, total))
    clip.write_videofile(SALIDA, fps=FPS, codec="libx264", audio_codec="aac", audio_bitrate="192k",
                         preset="medium", ffmpeg_params=["-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart"])
    print("Listo:", SALIDA, f"({total:.1f} s)")


if __name__ == "__main__":
    main()
