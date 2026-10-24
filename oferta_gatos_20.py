"""Oferta combos gato en 20 s: mismas escenas que oferta_gatos.py pero con tiempo estirado,
cámara lenta (speed ramp) al caer el precio, estelas de movimiento, luces en movimiento y transiciones nuevas.

Uso:
    python oferta_gatos_20.py                  # genera videos_salida/oferta_gatos_20s.mp4
    python oferta_gatos_20.py --frames 1 5 12  # vistas previas
"""
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from moviepy import AudioFileClip, VideoClip
from PIL import Image
from scipy.io import wavfile

import audio as au
import oferta_gatos as og
from efectos import H, W, clamp01, ease_in_out

FPS, DUR = 30, 20.0
SALIDA = "videos_salida/oferta_gatos_20s.mp4"
TR = 0.45
# (inicio, fin) reales de cada escena
R_INTRO, R_C1, R_C2, R_FIN = (0.0, 2.5), (2.05, 9.0), (8.55, 15.5), (15.05, 20.0)
SLOWMO = 0.95          # segundos reales de cámara lenta después de que cae el precio


# ------------------------------------------------------------ tiempo: estiramiento y speed ramp
def curva_tiempo(dur_real, tramos):
    """tramos: lista de (t_real_inicio, velocidad). Devuelve tiempo interno por cada t real (suavizado)."""
    ts = np.linspace(0, dur_real, int(dur_real * 600) + 1)
    v = np.zeros_like(ts)
    for i, (t0, vel) in enumerate(tramos):
        v[ts >= t0] = vel
    k = 60                                  # suavizado de los cambios de velocidad (0.1 s)
    v = np.convolve(np.pad(v, (k, k), mode="edge"), np.ones(2 * k + 1) / (2 * k + 1), mode="same")[k:-k]
    tau = np.concatenate([[0], np.cumsum((v[1:] + v[:-1]) / 2 * np.diff(ts))])
    return lambda t: float(np.interp(t, ts, tau)), lambda t: float(np.interp(t, ts, v))


def armar():
    intro = og.escena_intro()
    fin = og.escena_final(3.1)
    escenas = [(R_INTRO, intro, curva_tiempo(R_INTRO[1] - R_INTRO[0], [(0, 1 / 1.7)]), [(0.08, 0.75)]),
               ]
    for c, r in zip(og.COMBOS, (R_C1, R_C2)):
        dur = r[1] - r[0]
        t_golpe = (og.STAMP + 0.14) * 1.6            # real: precio ya apoyado
        tramos = [(0, 1 / 1.6), (t_golpe, 0.18), (t_golpe + SLOWMO, 0.45)]
        escenas.append((r, og.escena_combo(c, 3.3), curva_tiempo(dur, tramos),
                        [(0.0, 0.8)]))
    escenas.append((R_FIN, fin, curva_tiempo(R_FIN[1] - R_FIN[0], [(0, 1 / 1.55)]), [(0.0, 0.5)]))
    return escenas


def render_escena(esc, tl):
    rango, fn, (tau, vel), rapidos = esc
    ti = tau(tl)
    # estela de movimiento en los tramos rápidos (promedio de sub-cuadros internos)
    if any(a <= ti <= b for a, b in rapidos):
        d = 0.035
        acc = fn(ti).astype(np.float32) * 0.5 + fn(max(ti - d, 0)).astype(np.float32) * 0.3 + \
            fn(max(ti - 2 * d, 0)).astype(np.float32) * 0.2
        return acc.astype(np.uint8)
    return fn(ti)


# ------------------------------------------------------------ luces en movimiento (light leaks)
_ly, _lx = np.mgrid[0:H // 8, 0:W // 8].astype(np.float32) * 8
FUGAS = [((255, 150, 50), 0.11, 0.0, 520), ((255, 70, 140), 0.08, 2.1, 460), ((255, 220, 120), 0.06, 4.2, 600)]


def fugas_luz(f, t, op=0.22):
    acc = np.zeros(_ly.shape + (3,), np.float32)
    for color, vel, fase, rad in FUGAS:
        cx = W * (0.5 + 0.65 * np.sin(t * vel * 6 + fase))
        cy = H * (0.5 + 0.45 * np.cos(t * vel * 4.3 + fase * 1.7))
        g = np.exp(-(((_lx - cx) ** 2 + (_ly - cy) ** 2) / (2 * rad ** 2)))
        acc += g[..., None] * np.array(color, np.float32)
    acc = cv2.resize(acc, (W, H), interpolation=cv2.INTER_LINEAR) * op
    return np.clip(f.astype(np.float32) + acc, 0, 255).astype(np.uint8)


def destello_anamorfico(f, cy, fuerza):
    """Raya horizontal de luz (lens flare anamórfico)."""
    if fuerza <= 0.01:
        return f
    ov = np.zeros_like(f)
    cv2.line(ov, (0, int(cy)), (W, int(cy)), (255, 220, 170), 16, cv2.LINE_AA)
    ov = cv2.GaussianBlur(ov, (0, 0), sigmaX=60, sigmaY=10)
    cv2.circle(ov, (W // 2, int(cy)), 70, (255, 240, 210), -1, cv2.LINE_AA)
    ov = cv2.GaussianBlur(ov, (0, 0), 18)
    return cv2.add(f, (ov * fuerza).astype(np.uint8))


# ------------------------------------------------------------ transiciones
def tr_quemado(a, b, p):
    """Quemado de luz cálido: la imagen se sobreexpone, aparece la siguiente."""
    e = ease_in_out(p)
    out = cv2.addWeighted(a, 1 - e, b, e, 0).astype(np.float32)
    k = np.sin(np.pi * p)
    cx = W * (0.2 + 0.6 * p)
    leak = np.exp(-(((_lx - cx) ** 2) / (2 * 420 ** 2) + ((_ly - H * 0.45) ** 2) / (2 * 900 ** 2)))
    leak = cv2.resize(leak, (W, H))[..., None] * np.array((255, 170, 70), np.float32)
    out = out * (1 + 0.6 * k) + leak * 1.1 * k
    return np.clip(out, 0, 255).astype(np.uint8)


def tr_barrido(a, b, p):
    """Barrido lateral rápido (whip pan) con desenfoque de movimiento y separación RGB."""
    e = ease_in_out(p)
    off = int(e * W)
    out = np.empty_like(a)
    out[:, :W - off] = a[:, off:]
    out[:, W - off:] = b[:, :off]
    k = int(1 + 160 * np.sin(np.pi * p))
    k += (k % 2 == 0)
    if k > 1:
        out = cv2.blur(out, (k, 1))
    s = int(18 * np.sin(np.pi * p))
    if s:
        out = out.copy()
        out[:, :, 0] = np.roll(out[:, :, 0], s, axis=1)
        out[:, :, 2] = np.roll(out[:, :, 2], -s, axis=1)
    return out


def tr_giro(a, b, p):
    """Giro con zoom: la escena gira y se acerca, la nueva entra girando desde el otro lado."""
    e = ease_in_out(p)
    def gz(img, ang, esc, blur):
        M = cv2.getRotationMatrix2D((W / 2, H / 2), ang, esc)
        img = cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REFLECT)
        return og.zoom_blur(img, blur)
    if p < 0.5:
        out = gz(a, -40 * e * 2, 1 + 0.6 * e * 2, 0.3 * e * 2)
    else:
        q = (1 - p) * 2
        out = gz(b, 40 * q, 1 + 0.6 * q, 0.3 * q)
    fl = 0.35 * np.exp(-((p - 0.5) / 0.12) ** 2)
    return cv2.addWeighted(out, 1 - fl, np.full_like(out, 255), fl, 0)


TRANS = [tr_quemado, tr_barrido, tr_giro]
ESCENAS = None


def make_frame(t):
    t = min(t, DUR - 1e-3)
    act = [(i, e) for i, e in enumerate(ESCENAS) if e[0][0] <= t < e[0][1]]
    if len(act) == 1:
        i, e = act[0]
        f = render_escena(e, t - e[0][0])
    else:
        (ia, ea), (ib, eb) = act[0], act[-1]
        p = (t - eb[0][0]) / (ea[0][1] - eb[0][0])
        f = TRANS[ia](render_escena(ea, t - ea[0][0]), render_escena(eb, t - eb[0][0]), p)
    f = fugas_luz(f, t, 0.11)
    # raya de luz anamórfica cuando cae cada precio
    for r in (R_C1, R_C2):
        tg = r[0] + (og.STAMP + 0.05) * 1.6
        if tg - 0.05 <= t <= tg + 1.4:
            f = destello_anamorfico(f, 1560, 0.7 * np.exp(-max(t - tg, 0) * 2.2) * clamp01((t - tg + 0.05) / 0.05))
    return f


# ------------------------------------------------------------ audio (20 s)
SR = au.SR


def generar_audio(ruta="videos_salida/_oferta20_audio.wav"):
    n = int((DUR + 0.5) * SR)
    musica = np.zeros((n, 2))
    sfx = np.zeros((n, 2))
    P = au._poner
    nota = au.nota
    bpm = 112
    beat = 60 / bpm
    # intro: golpe grave y braam
    P(sfx, og.braam(2.2, 55.0), 0.55, 0.9)
    P(sfx, au.golpe(), 0.62, 1.0)
    P(sfx, og.crash(2.0), 0.62, 0.45)
    P(musica, og.riser(1.5), 0.8, 0.22)
    # ritmo épico
    acordes = [(45, (57, 60, 64)), (41, (57, 60, 65)), (48, (55, 60, 64)), (43, (55, 59, 62))]
    t0, i = R_C1[0] - 0.05, 0
    while t0 + i * beat < DUR:
        t = t0 + i * beat
        bj, ac = acordes[(i // 4) % 4]
        P(musica, au.bombo(), t, 1.0)
        if i % 2 == 1:
            P(musica, au.palmada(), t, 0.5)
        P(musica, au.hihat(), t + beat / 2, 0.28)
        P(musica, au.bajo(nota(bj - 12), beat * 0.45), t, 0.55)
        P(musica, au.bajo(nota(bj - 12), beat * 0.45), t + beat / 2, 0.42)
        if i % 4 == 0:
            P(musica, au.colchon([nota(m) for m in ac], 4 * beat + 0.4), t, 0.2)
        for j, m in enumerate((ac[0], ac[2], ac[1] + 12, ac[2])):
            P(musica, au.pluck(nota(m + 12)), t + j * beat / 4, 0.13, pan=0.35 + 0.3 * (j % 2))
        i += 1
    # cámara lenta: la música se apaga "bajo el agua" mientras dura
    lento = np.zeros(n)
    for r in (R_C1, R_C2):
        tg = r[0] + (og.STAMP + 0.14) * 1.6
        a, b = int(tg * SR), int((tg + SLOWMO) * SR)
        lento[a:b] = 1
    k = int(0.12 * SR)
    lento = np.convolve(lento, np.ones(k) / k, mode="same")
    apagada = np.stack([au._filtro(musica[:, c], "lowpass", 380) for c in range(2)], 1)
    musica = musica * (1 - lento[:, None]) + apagada * 0.9 * lento[:, None]
    # efectos sincronizados
    for c0, c1 in ((R_INTRO[1], R_C1[0]), (R_C1[1], R_C2[0]), (R_C2[1], R_FIN[0])):
        P(sfx, au.whoosh(0.6), (c0 + c1) / 2 - 0.3, 0.5)
    for r in (R_C1, R_C2):
        ts = r[0] + (og.STAMP + 0.05) * 1.6
        P(sfx, og.riser(1.3), ts - 1.3, 0.32)
        P(sfx, au.golpe(), ts, 1.0)
        P(sfx, og.braam(1.6, 41.2), ts, 0.6)
        P(sfx, og.crash(2.2), ts, 0.4)
        P(sfx, og.cha_ching(), ts + 0.1, 0.4)
    P(sfx, og.braam(2.0, 55.0), R_FIN[0] + 0.3, 0.6)
    P(sfx, au.golpe(), R_FIN[0] + 0.3, 0.85)
    P(sfx, og.crash(2.5), R_FIN[0] + 0.3, 0.35)
    buf = np.tanh((musica + sfx) * 0.85)[:int(DUR * SR)]
    fo = int(1.4 * SR)
    buf[-fo:] *= np.linspace(1, 0, fo)[:, None]
    buf *= 0.9 / np.abs(buf).max()
    tmp = "videos_salida/_oferta20_crudo.wav"
    wavfile.write(tmp, SR, (buf * 32767).astype(np.int16))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af", "loudnorm=I=-14:TP=-1.2:LRA=9", "-ar", str(SR), ruta],
                   check=True)
    return ruta


def main():
    global ESCENAS
    ESCENAS = armar()
    Path("videos_salida").mkdir(exist_ok=True)
    if "--frames" in sys.argv:
        for s in [float(x) for x in sys.argv[sys.argv.index("--frames") + 1:]]:
            Image.fromarray(make_frame(s)).save(f"videos_salida/prev_{s:05.2f}.png")
        return
    wav = generar_audio()
    pista = AudioFileClip(wav)
    video = VideoClip(make_frame, duration=DUR).with_audio(pista.subclipped(0, min(DUR, pista.duration)))
    video.write_videofile(SALIDA, fps=FPS, codec="libx264", audio_codec="aac", audio_bitrate="192k", preset="medium",
                          ffmpeg_params=["-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart"])
    print("Listo:", SALIDA)


if __name__ == "__main__":
    main()
