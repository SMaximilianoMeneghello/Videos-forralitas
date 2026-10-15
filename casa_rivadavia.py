"""Video publicitario vertical (1080x1920) para la venta del PH de Rivadavia 2647.

Corto y directo: clips breves del recorrido real (uno por ambiente), locución
neuronal, textos animados y música suave. Identidad propia (grafito + dorado),
sin relación visual con los videos de Forralitas.

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
from efectos import (BLANCO, BRILLO, W, H, ancho_texto, blit, caja, clamp01,
                     ease_out_back, ease_out_cubic, icono, prog, rotar_sprite,
                     sobre, texto)

FPS = 30
SR = voz_tts.SR
ENTRADA = "assets_casa/entrada.mp4"
SALIDA = "videos_salida/casa_rivadavia.mp4"
DIRECCION = "Rivadavia 2647"
VOZ = "es-AR-ElenaNeural"

# ------------------------------------------------------------ identidad propia (grafito + dorado)
NEGRO1 = (36, 32, 27)
NEGRO2 = (12, 11, 10)
DORADO = (203, 166, 86)
PANEL = (14, 13, 13)
GRIS_TXT = (214, 210, 202)

_grad_t = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
FONDO_BASE = np.repeat(np.array(NEGRO1, np.float32) * (1 - _grad_t) + np.array(NEGRO2, np.float32) * _grad_t, W, axis=1)


def fondo_elegante(t, semilla=3, n=20):
    pulso = 0.5 + 0.5 * np.sin(t * 1.4)
    f = FONDO_BASE + BRILLO * np.array(DORADO, np.float32) * 0.16 * pulso
    f = np.clip(f, 0, 255).astype(np.uint8)
    rng = np.random.default_rng(semilla)
    xs, ys = rng.uniform(0, W, n), rng.uniform(0, H, n)
    rs, vel = rng.uniform(3, 12, n), rng.uniform(12, 45, n)
    fase = rng.uniform(0, 6.28, n)
    ov = f.copy()
    col = tuple(int(c * 0.8) for c in DORADO)
    for x, y, r, v, ph in zip(xs, ys, rs, vel, fase):
        cx = x + 14 * np.sin(t * 0.6 + ph)
        cy = (y - v * t) % (H + 60) - 30
        cv2.circle(ov, (int(cx), int(cy)), int(r), col, -1, cv2.LINE_AA)
    return cv2.addWeighted(ov, 0.09, f, 0.91, 0)


# ------------------------------------------------------------ guion: un clip por ambiente
# "ini" y "maxdur" son ventanas del recorrido verificadas cuadro a cuadro (sin
# cámara en movimiento brusco ni superposición con el ambiente siguiente).
CLIPS = [
    dict(ini=0.6, maxdur=7.5, cap="Entrada",
         voz="Vendo este PH en Rivadavia, dos mil seiscientos cuarenta y siete."),
    dict(ini=11.0, maxdur=7.0, cap="Living *comedor*",
         voz="Un living comedor amplio y luminoso, ideal para compartir en familia."),
    dict(ini=33.0, maxdur=7.5, cap="*Cocina* equipada",
         voz="La cocina tiene muebles bajo mesada, con mucho espacio de guardado."),
    dict(ini=44.0, maxdur=7.0, cap="2 *dormitorios* grandes",
         voz="Cuenta con dos dormitorios grandes."),
    dict(ini=62.0, maxdur=8.0, cap="*Living* estar",
         voz="También tiene un living estar, con mucha luz."),
    dict(ini=71.0, maxdur=5.0, cap="*Lavadero* propio",
         voz="Con lavadero propio."),
    dict(ini=79.2, maxdur=4.5, cap="Segundo *dormitorio*", brillo=2.1,
         voz="El segundo dormitorio, ideal para toda la familia."),
    dict(ini=94.0, maxdur=8.0, cap="*Baño* completo",
         voz="Y un baño completo, totalmente revestido."),
]
DUR_MIN = 6.0

L_UBIC = ("A solo cincuenta metros de avenida Francisco de Aguirre, con cuatro líneas de colectivos. "
          "La escuela te queda a cien metros, con todo tipo de comercios cerca.")
C_UBIC = ["A 50 m de Av. *Francisco de Aguirre*", "4 líneas de *colectivos* · Escuela a *100 m*", "Todo tipo de *comercios* cerca"]
L_CIERRE = "Consultá ya por este PH."
DIGITOS = {"0": "cero", "1": "uno", "2": "dos", "3": "tres", "4": "cuatro",
           "5": "cinco", "6": "seis", "7": "siete", "8": "ocho", "9": "nueve"}


def num_hablado(tel):
    """'381 526 9004' -> 'tres ocho uno, cinco dos seis, nueve cero cero cuatro'."""
    grupos = [" ".join(DIGITOS[d] for d in g) for g in tel.split()]
    return ", ".join(grupos)

D_INTRO = 4.5
D_UBIC = 8.5
D_CIERRE = 9.5
TR_VIDEO = 0.55       # disolución entre escenas que incluyen metraje
TR_CORTE = 0.0        # corte seco entre tarjetas gráficas (sin superponer texto)


# ------------------------------------------------------------ texto ajustado con resaltado
def linea_resaltada(marcado, tam, max_w, color=BLANCO):
    pal = [(p.strip("*"), p.startswith("*")) for p in marcado.split()]
    while True:
        gap = tam * 0.28
        anchos = [ancho_texto(p, tam) for p, _ in pal]
        total = sum(anchos) + gap * (len(pal) - 1)
        if total <= max_w or tam <= 26:
            break
        tam -= 3
    sprites = [texto(p, tam, DORADO if d else color) for p, d in pal]
    x, xs = (W - total) / 2, []
    for a in anchos:
        xs.append(x)
        x += a + gap
    return sprites, xs


def texto_ajustado(txt, tam, max_w, color=BLANCO, sombra=False):
    while ancho_texto(txt, tam) > max_w and tam > 20:
        tam -= 2
    return texto(txt, tam, color, sombra)


def placa(marcado, tam=52, max_w=W - 140):
    spr, xs = linea_resaltada(marcado, tam, max_w)
    ancho = max(x + s.shape[1] for s, x in zip(spr, xs)) - min(xs)
    fondo = caja(int(ancho + 70), 110, 32, PANEL, 0.74)
    off = min(xs)
    for s, x in zip(spr, xs):
        fondo = sobre(fondo, s, int(x - off + 35), int((110 - s.shape[0]) / 2))
    return fondo


# ------------------------------------------------------------ escena intro
def escena_intro():
    tit1 = texto("PH EN VENTA", 104, DORADO)
    tit2 = texto(DIRECCION, 80, BLANCO)

    def fn(t):
        f = fondo_elegante(t, semilla=11)
        p1 = ease_out_cubic(prog(t, 0.2, 0.75))
        blit(f, tit1, W / 2, 780 + (1 - p1) * 60, alpha=p1, escala=max(ease_out_back(prog(t, 0.2, 0.75)), 0.01),
             centro=True)
        p2 = ease_out_cubic(prog(t, 0.65, 0.65))
        blit(f, tit2, W / 2, 915 + (1 - p2) * 40, alpha=p2, centro=True)
        linea = int(420 * ease_out_cubic(prog(t, 1.1, 0.5)))
        if linea > 0:
            cv2.rectangle(f, (W // 2 - linea // 2, 1020), (W // 2 + linea // 2, 1030), DORADO, -1, cv2.LINE_AA)
        return f
    return fn


# ------------------------------------------------------------ escena ubicación
def escena_ubicacion():
    tit = texto("UBICACIÓN PRIVILEGIADA", 56, DORADO)
    lineas = [placa(c, 46) for c in C_UBIC]
    ys = [560, 760, 960]

    def fn(t):
        f = fondo_elegante(t, semilla=23)
        p = ease_out_cubic(prog(t, 0.15, 0.6))
        blit(f, tit, W / 2, 300 + (1 - p) * 30, alpha=p, centro=True)
        for i, (spr, y) in enumerate(zip(lineas, ys)):
            q = prog(t, 0.55 + i * 0.6, 0.55)
            e = ease_out_cubic(q)
            blit(f, spr, (W - spr.shape[1]) / 2, y + (1 - e) * 35, alpha=clamp01(q * 2.2))
        return f
    return fn


# ------------------------------------------------------------ escena cierre
def escena_cierre(tel=None):
    tit = texto("¡CONSULTANOS YA!", 78, DORADO)
    ic_tel = icono("telefono", 150, fondo=DORADO, tinta=NEGRO2)
    if tel:
        num = texto_ajustado(tel, 90, 760, BLANCO, True)
        tarjeta = sobre(caja(940, 220, 46, PANEL, 0.82), num,
                        int((940 - num.shape[1]) / 2 + 60), int((220 - num.shape[0]) / 2))
    else:
        # recuadro de teléfono vacío a propósito: lo completa quien publique el video
        tarjeta = caja(940, 220, 46, PANEL, 0.82)
    ic_ubic = icono("ubicacion", 90, fondo=DORADO, tinta=NEGRO2)
    dir1 = texto_ajustado(DIRECCION, 54, 760, BLANCO)
    tarjeta2 = sobre(sobre(caja(940, 150, 40, PANEL, 0.78), ic_ubic, 30, 30), dir1, 150, int((150 - dir1.shape[0]) / 2))
    pie = texto_ajustado("PH 2 dormitorios · Cocina comedor · Living · Terraza", 36, W - 80, GRIS_TXT)

    def fn(t):
        f = fondo_elegante(t, semilla=19)
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
            blit(f, rotar_sprite(ic_tel, ang), x + 70, 540 + 110, alpha=clamp01(q * 2.5),
                 escala=1 + 0.06 * env, centro=True)

        q2 = prog(t, 1.3, 0.65)
        e2 = ease_out_cubic(q2)
        blit(f, tarjeta2, x, 810 + (1 - e2) * 60, alpha=clamp01(q2 * 2.5))

        q3 = ease_out_cubic(prog(t, 2.0, 0.7))
        blit(f, pie, W / 2, 1040 + (1 - q3) * 30, alpha=q3, centro=True)
        return f
    return fn


# ------------------------------------------------------------ badge persistente sobre el recorrido
def dibujar_badge():
    tag = texto("EN VENTA", 34, NEGRO2, sombra=False)
    pastilla = sobre(caja(tag.shape[1] + 50, tag.shape[0] + 6, 30, DORADO, 0.95), tag, 25, 0)
    dirsp = texto(DIRECCION, 34, BLANCO, sombra=True)
    dirpast = sobre(caja(dirsp.shape[1] + 46, dirsp.shape[0] + 4, 26, PANEL, 0.72), dirsp, 20, -1)
    return pastilla, dirpast


# ------------------------------------------------------------ construir línea de tiempo + voces
def construir():
    cl = lambda t, **kw: voz_tts.clip(t, voz=VOZ, **kw)
    dur = lambda x: len(x) / SR

    for c in CLIPS:
        c["audio"] = cl(c["voz"])
        c["dur"] = min(c["maxdur"], max(DUR_MIN, dur(c["audio"]) + 1.6))
        c["placa"] = placa(c["cap"])
    ubic_voz = cl(L_UBIC, rate="+6%")

    video = VideoFileClip(ENTRADA).resized(width=W)
    video = video.cropped(y_center=video.h / 2, height=H)

    durs = [D_INTRO] + [c["dur"] for c in CLIPS] + [D_UBIC, D_CIERRE]
    n = len(durs)
    # transición entre cada par de escenas consecutivas: disolución si alguna
    # de las dos incluye metraje de la casa, corte seco entre tarjetas gráficas
    # (ubicación -> cierre) para que los títulos nunca se superpongan.
    trs = [TR_CORTE if (i == n - 2) else TR_VIDEO for i in range(n - 1)]
    inicios, t = [0.0], 0.0
    for d, tr in zip(durs[:-1], trs):
        t += d - tr
        inicios.append(t)
    total = inicios[-1] + durs[-1]

    voces = []
    for c, t0 in zip(CLIPS, inicios[1:]):
        voces.append((t0 + 0.4, c["audio"]))
    voces.append((inicios[-2] + 0.6, ubic_voz))
    t_cierre = inicios[-1] + 0.6

    return video, CLIPS, inicios, durs, trs, total, voces, t_cierre


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
    fi, fo = int(0.5 * SR), int(1.8 * SR)
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
def hacer_frame_fn(video, clips, inicios, durs, trs, total, tel=None):
    fn_intro = escena_intro()
    fn_ubic = escena_ubicacion()
    fn_cierre = escena_cierre(tel)
    badge, dirpast = dibujar_badge()

    i_intro = 0
    i_clips = list(range(1, 1 + len(clips)))
    i_ubic = i_clips[-1] + 1
    i_cierre = i_ubic + 1

    def frame_clip(idx, tl):
        c = clips[idx]
        tv = c["ini"] + clamp01(tl / c["dur"]) * c["dur"]
        f = np.ascontiguousarray(video.get_frame(tv))
        brillo = c.get("brillo", 1.0)
        if brillo != 1.0:
            fl = f.astype(np.float32) / 255.0
            fl = np.clip(fl * brillo + (brillo - 1) * 0.06, 0, 1) ** (1 / max(brillo * 0.7, 1.0))
            f = (fl * 255).astype(np.uint8)
        yy = np.arange(H, dtype=np.float32)[:, None, None]
        top = np.clip(1 - (yy / 260), 0, 1) * 0.55
        bot = np.clip(1 - ((H - 1 - yy) / 420), 0, 1) * 0.6
        f = (f.astype(np.float32) * (1 - np.maximum(top, bot))).astype(np.uint8)
        ph = ease_out_cubic(prog(tl, 0.2, 0.5))
        blit(f, badge, 44, 70, alpha=ph)
        blit(f, dirpast, 44, 70 + badge.shape[0] + 14, alpha=ph)
        q = prog(tl, 0.35, 0.4)
        qf = prog(tl, c["dur"] - 0.35, 0.35)
        alpha = clamp01(q) * (1 - clamp01(qf))
        if alpha > 0.01:
            e = ease_out_cubic(q)
            blit(f, c["placa"], (W - c["placa"].shape[1]) / 2, 1640 + (1 - e) * 35, alpha=alpha)
        return f

    def raw(i, tl):
        if i == i_intro:
            return fn_intro(tl)
        if i in i_clips:
            return frame_clip(i - 1, tl)
        if i == i_ubic:
            return fn_ubic(tl)
        return fn_cierre(tl)

    def make_frame(t):
        t = min(t, total - 1e-3)
        activos = [i for i, (s, d) in enumerate(zip(inicios, durs)) if s <= t < s + d]
        if len(activos) == 1:
            i = activos[0]
            return raw(i, t - inicios[i])
        a, b = activos[0], activos[-1]
        fa = raw(a, min(t - inicios[a], durs[a] - 1e-3))
        fb = raw(b, max(t - inicios[b], 0))
        tr = trs[a] if a < len(trs) else TR_VIDEO
        p = clamp01((t - inicios[b]) / tr) if tr > 0 else 1.0
        return cv2.addWeighted(fa, 1 - p, fb, p, 0)

    return make_frame


def main():
    Path("videos_salida").mkdir(exist_ok=True)
    video, clips, inicios, durs, trs, total, voces_base, t_cierre = construir()

    if "--frames" in sys.argv:
        make_frame = hacer_frame_fn(video, clips, inicios, durs, trs, total)
        segundos = [float(x) for x in sys.argv[sys.argv.index("--frames") + 1:]]
        from PIL import Image
        for s in segundos:
            Image.fromarray(make_frame(s)).save(f"videos_salida/prev_casa_{s:05.1f}.png")
        print("duración total:", round(total, 2), "s | inicios:", [round(x, 1) for x in inicios])
        return

    # --tel-list num1,num2,... genera una copia del video por cada número; la
    # locución del cierre nombra el número, así que el audio se mezcla por
    # separado para cada uno (el resto de las voces se reutiliza).
    if "--tel-list" in sys.argv:
        tels = sys.argv[sys.argv.index("--tel-list") + 1].split(",")
    else:
        tels = [None]

    cl = lambda t, **kw: voz_tts.clip(t, voz=VOZ, **kw)
    for tel in tels:
        texto_cierre = f"{L_CIERRE} Llamanos al {num_hablado(tel)}." if tel else L_CIERRE
        cierre_voz = cl(texto_cierre, rate="+8%")
        tag = tel.replace(" ", "") if tel else "sinnumero"
        voces = voces_base + [(t_cierre, cierre_voz)]
        audio_wav = mezclar(total, voces, ruta=f"videos_salida/_mezcla_casa_{tag}.wav")
        print("audio listo:", audio_wav, f"({total:.1f} s)")
        if "--audio" in sys.argv:
            continue

        make_frame = hacer_frame_fn(video, clips, inicios, durs, trs, total, tel=tel)
        salida = SALIDA if tel is None else f"videos_salida/casa_rivadavia_{tag}.mp4"
        pista = AudioFileClip(audio_wav)
        audio_clip = pista.subclipped(0, min(total, pista.duration))
        clip = VideoClip(make_frame, duration=total).with_audio(audio_clip)
        clip.write_videofile(salida, fps=FPS, codec="libx264", audio_codec="aac", audio_bitrate="192k",
                             preset="medium", ffmpeg_params=["-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart"])
        print("Listo:", salida, f"({total:.1f} s)")


if __name__ == "__main__":
    main()
