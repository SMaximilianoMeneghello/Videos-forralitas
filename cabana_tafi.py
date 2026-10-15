"""Video publicitario vertical (1080x1920) para la venta de la cabaña del
Club de Campo Taficillo, Tafí Viejo.

Formato distinto al de casa_rivadavia.py: combina el metraje real del
exterior con las fotos del interior y la pileta (paneo tipo Ken Burns),
identidad propia "bosque + terracota" (verde profundo, texto crema,
acentos terracota), tarjetas alineadas a la izquierda en vez de centradas.

Uso:
    source .venv/bin/activate
    python cabana_tafi.py                  # genera videos_salida/cabana_tafi.mp4
    python cabana_tafi.py --frames 2 10 40 # vistas previas (PNG)
    python cabana_tafi.py --audio          # solo arma el audio mezclado
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
from efectos import (BLANCO, BRILLO, Foto, W, H, ancho_texto, blit, caja,
                     clamp01, ease_out_back, ease_out_cubic, icono, prog,
                     rotar_sprite, sobre, texto)

FPS = 30
SR = voz_tts.SR
VIDEO_SRC = "assets_cabana/entrada.mp4"
SALIDA = "videos_salida/cabana_tafi.mp4"
TEL = "381 585 9396"
UBIC = ("Club de Campo Taficillo", "Tafí Viejo")
VOZ = "es-AR-TomasNeural"

# ------------------------------------------------------------ identidad propia (bosque + terracota)
VERDE1 = (26, 38, 28)
VERDE2 = (9, 14, 11)
TERRACOTA = (196, 110, 61)
CREMA = (238, 227, 203)
PANEL = (13, 16, 13)

_grad_t = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
FONDO_BASE = np.repeat(np.array(VERDE1, np.float32) * (1 - _grad_t) + np.array(VERDE2, np.float32) * _grad_t, W, axis=1)


def fondo_bosque(t, semilla=3, n=16):
    pulso = 0.5 + 0.5 * np.sin(t * 1.3)
    f = FONDO_BASE + BRILLO * np.array(TERRACOTA, np.float32) * 0.12 * pulso
    f = np.clip(f, 0, 255).astype(np.uint8)
    rng = np.random.default_rng(semilla)
    xs, ys = rng.uniform(0, W, n), rng.uniform(0, H, n)
    rs, vel = rng.uniform(2, 7, n), rng.uniform(8, 30, n)
    fase = rng.uniform(0, 6.28, n)
    ov = f.copy()
    col = (236, 214, 150)
    for x, y, r, v, ph in zip(xs, ys, rs, vel, fase):
        cx = x + 10 * np.sin(t * 0.5 + ph)
        cy = (y - v * t) % (H + 60) - 30
        cv2.circle(ov, (int(cx), int(cy)), int(r), col, -1, cv2.LINE_AA)
    return cv2.addWeighted(ov, 0.07, f, 0.93, 0)


# ------------------------------------------------------------ guion: video + fotos, en orden
SEGMENTOS = [
    dict(tipo="video", ini=1.0, maxdur=4.5, cap="Ingreso al *country*",
         voz="Cabaña en venta dentro del club de campo Taficillo, en Tafí Viejo."),
    dict(tipo="video", ini=6.0, maxdur=5.5, cap="La *cabaña*",
         voz="Una cabaña de estilo, lista para disfrutar todo el año."),
    dict(tipo="foto", ruta="assets_cabana/01_living.webp", cam=(1.05, 1.28, (0.05, 0.5), (0.95, 0.45)),
         maxdur=6.5, cap="Living comedor con *hogar a leña*",
         voz="Living comedor y cocina integrados, con hogar a leña."),
    dict(tipo="foto", ruta="assets_cabana/02_dormitorio.webp", cam=(1.0, 1.18, (0.5, 0.35), (0.5, 0.6)),
         maxdur=5.5, cap="2 *dormitorios* y baño",
         voz="Cuenta con dos dormitorios y baño, más galería y lavadero."),
    dict(tipo="video", ini=31.0, maxdur=4.2, cap="2 *cisternas* de 1000 L",
         voz="Tiene dos cisternas de mil litros, con bomba."),
    dict(tipo="foto", ruta="assets_cabana/03_piscina_dia.webp", cam=(1.0, 1.16, (0.5, 0.55), (0.45, 0.4)),
         maxdur=6.0, cap="*Piscina* de 7 x 3 x 1,50 m",
         voz="Una piscina de siete por tres metros, con uno cincuenta de profundidad."),
    dict(tipo="foto", ruta="assets_cabana/04_piscina_atardecer.webp", cam=(1.02, 1.2, (0.45, 0.6), (0.55, 0.4)),
         maxdur=5.5, cap="*Hidromasaje* y cascada",
         voz="Con sistema de filtrado, hidromasaje y cascada."),
    dict(tipo="foto", ruta="assets_cabana/05_piscina_noche.webp", cam=(1.0, 1.15, (0.5, 0.45), (0.5, 0.6)),
         maxdur=5.5, cap="De día... y de *noche*",
         voz="Ideal para disfrutar de día, y también de noche."),
]
DUR_MIN = 4.0

C_FEATS = ["Terreno de *20 x 30* m", "Luz · *WiFi* · Galería · Lavadero", "Con *escritura*"]
L_FEATS = "El terreno es de veinte por treinta metros, con luz, wifi, y se entrega con escritura."
L_CIERRE = "Consultá ya. Tres ocho uno, cinco ocho cinco, nueve tres nueve seis."

D_INTRO = 4.5
D_FEATS = 8.0
D_CIERRE = 9.0
TR_VIDEO = 0.55
TR_CORTE = 0.0


# ------------------------------------------------------------ texto con resaltado
def linea_resaltada(marcado, tam, max_w, color=CREMA):
    pal = [(p.strip("*"), p.startswith("*")) for p in marcado.split()]
    while True:
        gap = tam * 0.28
        anchos = [ancho_texto(p, tam) for p, _ in pal]
        total = sum(anchos) + gap * (len(pal) - 1)
        if total <= max_w or tam <= 26:
            break
        tam -= 3
    sprites = [texto(p, tam, TERRACOTA if d else color) for p, d in pal]
    x, xs = (W - total) / 2, []
    for a in anchos:
        xs.append(x)
        x += a + gap
    return sprites, xs


def texto_ajustado(txt, tam, max_w, color=CREMA, sombra=False):
    while ancho_texto(txt, tam) > max_w and tam > 20:
        tam -= 2
    return texto(txt, tam, color, sombra)


def placa_centrada(marcado, tam=50, max_w=W - 140):
    spr, xs = linea_resaltada(marcado, tam, max_w)
    ancho = max(x + s.shape[1] for s, x in zip(spr, xs)) - min(xs)
    fondo = caja(int(ancho + 70), 108, 30, PANEL, 0.74)
    off = min(xs)
    for s, x in zip(spr, xs):
        fondo = sobre(fondo, s, int(x - off + 35), int((108 - s.shape[0]) / 2))
    return fondo


def placa_izquierda(marcado, tam=50, max_w=W - 220):
    """Tarjeta alineada a la izquierda, con franja terracota al borde."""
    pal = [(p.strip("*"), p.startswith("*")) for p in marcado.split()]
    while True:
        gap = tam * 0.28
        anchos = [ancho_texto(p, tam) for p, _ in pal]
        total = sum(anchos) + gap * (len(pal) - 1)
        if total <= max_w or tam <= 26:
            break
        tam -= 3
    sprites = [texto(p, tam, TERRACOTA if d else CREMA) for p, d in pal]
    alto = int(max(s.shape[0] for s in sprites) + 46)
    fondo = caja(int(total + 90), alto, 24, PANEL, 0.76)
    franja = caja(10, alto, 0, TERRACOTA, 1.0)
    fondo = sobre(fondo, franja, 0, 0)
    x = 50
    for s, a in zip(sprites, anchos):
        fondo = sobre(fondo, s, int(x), int((alto - s.shape[0]) / 2))
        x += a + gap
    return fondo


# ------------------------------------------------------------ escena intro
def escena_intro():
    tit = texto("CABAÑA EN VENTA", 92, TERRACOTA)
    sub1 = texto(UBIC[0], 64, CREMA)
    sub2 = texto(UBIC[1], 44, (210, 200, 180))

    def fn(t):
        f = fondo_bosque(t, semilla=7)
        p1 = ease_out_cubic(prog(t, 0.2, 0.75))
        blit(f, tit, W / 2, 760 + (1 - p1) * 50, alpha=p1,
             escala=max(ease_out_back(prog(t, 0.2, 0.75)), 0.01), centro=True)
        linea = int(380 * ease_out_cubic(prog(t, 0.75, 0.45)))
        if linea > 0:
            cv2.rectangle(f, (W // 2 - linea // 2, 880), (W // 2 + linea // 2, 888), TERRACOTA, -1, cv2.LINE_AA)
        p2 = ease_out_cubic(prog(t, 1.0, 0.6))
        blit(f, sub1, W / 2, 940 + (1 - p2) * 35, alpha=p2, centro=True)
        p3 = ease_out_cubic(prog(t, 1.3, 0.6))
        blit(f, sub2, W / 2, 1025 + (1 - p3) * 30, alpha=p3, centro=True)
        return f
    return fn


# ------------------------------------------------------------ escena terreno y servicios
def escena_features():
    tit = texto("TERRENO Y SERVICIOS", 54, TERRACOTA)
    tarjetas = [placa_izquierda(c, 46) for c in C_FEATS]
    ys = [580, 790, 1000]

    def fn(t):
        f = fondo_bosque(t, semilla=14)
        p = ease_out_cubic(prog(t, 0.15, 0.6))
        blit(f, tit, W / 2, 320 + (1 - p) * 30, alpha=p, centro=True)
        for i, (spr, y) in enumerate(zip(tarjetas, ys)):
            q = prog(t, 0.6 + i * 0.65, 0.55)
            e = ease_out_cubic(q)
            x = 90 - (1 - e) * 260
            blit(f, spr, x, y, alpha=clamp01(q * 2.2))
        return f
    return fn


# ------------------------------------------------------------ escena cierre
def escena_cierre():
    tit = texto("¡CONSULTANOS YA!", 74, TERRACOTA)
    ic_tel = icono("telefono", 150, fondo=TERRACOTA, tinta=VERDE2)
    num = texto_ajustado(TEL, 86, 760, CREMA, True)
    tarjeta = sobre(caja(940, 220, 46, PANEL, 0.82), num, int((940 - num.shape[1]) / 2 + 60), int((220 - num.shape[0]) / 2))
    ic_ubic = icono("ubicacion", 90, fondo=TERRACOTA, tinta=VERDE2)
    dir1 = texto_ajustado(f"{UBIC[0]} · {UBIC[1]}", 46, 760, CREMA)
    tarjeta2 = sobre(sobre(caja(940, 150, 40, PANEL, 0.78), ic_ubic, 30, 30), dir1, 150, int((150 - dir1.shape[0]) / 2))
    pie = texto_ajustado("2 dormitorios · Living comedor · Pileta · Con escritura", 34, W - 80, (210, 200, 180))

    def fn(t):
        f = fondo_bosque(t, semilla=21)
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


# ------------------------------------------------------------ badge persistente
def dibujar_badge():
    tag = texto("EN VENTA", 32, VERDE2, sombra=False)
    pastilla = sobre(caja(tag.shape[1] + 48, tag.shape[0] + 6, 28, TERRACOTA, 0.95), tag, 24, 0)
    dirsp = texto(f"{UBIC[0]}", 32, CREMA, sombra=True)
    dirpast = sobre(caja(dirsp.shape[1] + 44, dirsp.shape[0] + 4, 24, PANEL, 0.7), dirsp, 20, -1)
    return pastilla, dirpast


# ------------------------------------------------------------ construir línea de tiempo + voces
def construir():
    cl = lambda t, **kw: voz_tts.clip(t, voz=VOZ, **kw)
    dur = lambda x: len(x) / SR

    for s in SEGMENTOS:
        s["audio"] = cl(s["voz"])
        s["dur"] = min(s["maxdur"], max(DUR_MIN, dur(s["audio"]) + 1.6))
        s["placa"] = placa_centrada(s["cap"])
        if s["tipo"] == "foto":
            s["foto"] = Foto(s["ruta"])
    feats_voz = cl(L_FEATS, rate="+6%")
    cierre_voz = cl(L_CIERRE, rate="+8%")

    video = VideoFileClip(VIDEO_SRC).resized(width=W)
    video = video.cropped(y_center=video.h / 2, height=H)

    durs = [D_INTRO] + [s["dur"] for s in SEGMENTOS] + [D_FEATS, D_CIERRE]
    n = len(durs)
    trs = [TR_CORTE if (i == n - 2) else TR_VIDEO for i in range(n - 1)]
    inicios, t = [0.0], 0.0
    for d, tr in zip(durs[:-1], trs):
        t += d - tr
        inicios.append(t)
    total = inicios[-1] + durs[-1]

    voces = []
    for s, t0 in zip(SEGMENTOS, inicios[1:]):
        voces.append((t0 + 0.4, s["audio"]))
    voces.append((inicios[-2] + 0.6, feats_voz))
    voces.append((inicios[-1] + 0.6, cierre_voz))

    return video, SEGMENTOS, inicios, durs, trs, total, voces


# ------------------------------------------------------------ mezcla de audio
def _env(x, ms):
    k = max(1, int(SR * ms / 1000))
    return np.sqrt(np.convolve(x ** 2, np.ones(k) / k, mode="same"))


def mezclar(total, voces, ruta="videos_salida/_mezcla_cabana.wav"):
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
    tmp = "videos_salida/_mezcla_cabana_cruda.wav"
    wavfile.write(tmp, SR, (mix * 32767).astype(np.int16))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af", "loudnorm=I=-16:TP=-1.5:LRA=9", "-ar", str(SR), ruta],
                   check=True)
    return ruta


# ------------------------------------------------------------ render
def hacer_frame_fn(video, segs, inicios, durs, trs, total):
    fn_intro = escena_intro()
    fn_feats = escena_features()
    fn_cierre = escena_cierre()
    badge, dirpast = dibujar_badge()

    i_segs = list(range(1, 1 + len(segs)))
    i_feats = i_segs[-1] + 1
    i_cierre = i_feats + 1

    def frame_seg(idx, tl):
        s = segs[idx]
        p = clamp01(tl / s["dur"])
        if s["tipo"] == "video":
            tv = s["ini"] + p * s["dur"]
            f = np.ascontiguousarray(video.get_frame(tv))
        else:
            z0, z1, a, b = s["cam"]
            f = s["foto"].frame(p, z0, z1, a, b)
        yy = np.arange(H, dtype=np.float32)[:, None, None]
        top = np.clip(1 - (yy / 260), 0, 1) * 0.55
        bot = np.clip(1 - ((H - 1 - yy) / 420), 0, 1) * 0.6
        f = (f.astype(np.float32) * (1 - np.maximum(top, bot))).astype(np.uint8)
        ph = ease_out_cubic(prog(tl, 0.2, 0.5))
        blit(f, badge, W - badge.shape[1] - 44, 70, alpha=ph)
        blit(f, dirpast, W - dirpast.shape[1] - 44, 70 + badge.shape[0] + 14, alpha=ph)
        q = prog(tl, 0.35, 0.4)
        qf = prog(tl, s["dur"] - 0.35, 0.35)
        alpha = clamp01(q) * (1 - clamp01(qf))
        if alpha > 0.01:
            e = ease_out_cubic(q)
            blit(f, s["placa"], (W - s["placa"].shape[1]) / 2, 1640 + (1 - e) * 35, alpha=alpha)
        return f

    def raw(i, tl):
        if i == 0:
            return fn_intro(tl)
        if i in i_segs:
            return frame_seg(i - 1, tl)
        if i == i_feats:
            return fn_feats(tl)
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
    video, segs, inicios, durs, trs, total, voces = construir()
    make_frame = hacer_frame_fn(video, segs, inicios, durs, trs, total)

    if "--frames" in sys.argv:
        segundos = [float(x) for x in sys.argv[sys.argv.index("--frames") + 1:]]
        from PIL import Image
        for s in segundos:
            Image.fromarray(make_frame(s)).save(f"videos_salida/prev_cabana_{s:05.1f}.png")
        print("duración total:", round(total, 2), "s | inicios:", [round(x, 1) for x in inicios])
        return

    audio_wav = mezclar(total, voces)
    print("audio listo:", audio_wav, f"({total:.1f} s)")
    if "--audio" in sys.argv:
        return

    pista = AudioFileClip(audio_wav)
    clip = VideoClip(make_frame, duration=total).with_audio(pista.subclipped(0, min(total, pista.duration)))
    clip.write_videofile(SALIDA, fps=FPS, codec="libx264", audio_codec="aac", audio_bitrate="192k",
                         preset="medium", ffmpeg_params=["-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart"])
    print("Listo:", SALIDA, f"({total:.1f} s)")


if __name__ == "__main__":
    main()
