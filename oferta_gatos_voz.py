"""Oferta combos gato (20 s) con locución y música de chacarera de fondo.

Uso:
    python oferta_gatos_voz.py             # genera videos_salida/oferta_gatos_voz.mp4

Música: si existe CANCION (mp3/wav), se usa esa canción. Si no, suena una chacarera instrumental
sintetizada (guitarra, bombo legüero y violín en 6/8) como fondo provisorio.
La música baja sola cuando habla la voz.
"""
import subprocess
from pathlib import Path

import numpy as np
from moviepy import AudioFileClip, VideoClip
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

import audio as au
import audio_campo as ac
import oferta_gatos as og
import oferta_gatos_20 as o20
import voz_tts

SALIDA = "videos_salida/oferta_gatos_voz.mp4"
CANCION = "assets/musica/chacarera_del_violin.mp3"
CANCION_INICIO = 0.0          # segundo de la canción desde donde empieza a sonar
SR = au.SR
DUR = 20.0
VOZ, RATE = "es-AR-TomasNeural", "+25%"

# escenas acomodadas para que entre toda la locución
o20.R_INTRO, o20.R_C1, o20.R_C2, o20.R_FIN = (0.0, 2.5), (2.05, 8.4), (7.95, 14.3), (13.85, 20.0)

LOCUCION = [
    (0.65, "¡Ofertas para tu gato en Forralitas!"),
    (2.15, "Sabrositos gato mix, más piedras sanitarias de un kilo."),
    (4.85, "¡Las dos, por solo veinticinco mil pesos!"),
    (8.05, "Y Sabrositos gato pescado, más piedras sanitarias."),
    (10.6, "¡Las dos, por solo veintiocho mil pesos!"),
    (13.2, "Pedilo ya al tres ocho uno, cinco dos seis, nueve cero cero cuatro, "
           "o al tres ocho uno, seis tres tres, cuatro tres cuatro cuatro."),
]


# ------------------------------------------------------------ chacarera instrumental (provisoria)
CORCHEA = 0.19                     # 6/8: un compás = 6 corcheas
COMPAS = 6 * CORCHEA
nota = au.nota


def parche():
    t = au._t(0.5)
    f = 62 + 50 * np.exp(-t * 28)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6)
    golpe = au._filtro(np.random.default_rng(1).standard_normal(t.size), "lowpass", 900) * np.exp(-t * 40) * 0.5
    return s + golpe


def aro():
    t = au._t(0.12)
    r = au._filtro(np.random.default_rng(2).standard_normal(t.size), "bandpass", [1500, 5000]) * np.exp(-t * 55)
    return r * 0.8 + np.sin(2 * np.pi * 1900 * t) * np.exp(-t * 70) * 0.35


def rasguido(midis, fuerte=1.0, abajo=True):
    orden = midis if abajo else midis[::-1]
    out = np.zeros(int(1.2 * SR))
    for k, m in enumerate(orden):
        c = ac.cuerda(nota(m), 1.1, 0.995, 0.4)
        i = int(k * 0.011 * SR)
        out[i:i + c.size] += c[:out.size - i] * (0.9 - 0.06 * k)
    return out * fuerte * 0.32


def violin(f, dur):
    t = au._t(dur)
    vib = 1 + 0.007 * np.sin(2 * np.pi * 5.6 * t) * np.clip((t - 0.12) / 0.2, 0, 1)
    fase = np.cumsum(f * vib) / SR
    s = sum((1 / k) * np.sin(2 * np.pi * k * fase) for k in range(1, 12))
    arco = au._filtro(np.random.default_rng(3).standard_normal(t.size), "bandpass", [2500, 6000]) * 0.04
    s = au._filtro(s + arco, "bandpass", [280, 5200])
    env = np.minimum(t / 0.05, 1) * np.minimum((dur - t) / 0.06, 1).clip(0, 1)
    return s * env * 0.5


ACORDES = {"Am": (45, (57, 60, 64, 69)), "Dm": (50, (57, 62, 65, 69)), "E7": (40, (56, 59, 62, 64)),
           "C": (48, (55, 60, 64, 67)), "G7": (43, (55, 59, 62, 65))}
PROGRESION = ["Am", "Am", "Dm", "E7", "Am", "C", "E7", "Am"]
# melodía de violín: (corchea dentro de 2 compases, duración en corcheas, nota)
MELODIA = [
    [(0, 2, 76), (2, 1, 74), (3, 2, 72), (5, 1, 71), (6, 3, 69), (9, 3, 72)],
    [(0, 2, 77), (2, 1, 76), (3, 2, 74), (5, 1, 72), (6, 3, 71), (9, 3, 68)],
    [(0, 2, 76), (2, 1, 77), (3, 2, 76), (5, 1, 74), (6, 3, 72), (9, 3, 76)],
    [(0, 2, 74), (2, 1, 72), (3, 2, 71), (5, 1, 68), (6, 6, 69)],
]


def chacarera(dur):
    n = int((dur + 2) * SR)
    buf = np.zeros((n, 2))
    P = au._poner
    compases = int(dur / COMPAS) + 2
    for c in range(compases):
        t0 = c * COMPAS
        nombre = PROGRESION[c % len(PROGRESION)]
        bajo, voces = ACORDES[nombre]
        # bombo legüero: parche - aro - aro / parche - aro - parche
        for k, (tipo, g) in enumerate((("p", 1.0), ("a", 0.6), ("a", 0.5), ("p", 0.9), ("a", 0.6), ("p", 0.55))):
            P(buf, parche() if tipo == "p" else aro(), t0 + k * CORCHEA, g * 0.55, 0.45)
        # guitarra: bajo + rasguido con acentos en 1 y 4
        P(buf, ac.cuerda(nota(bajo), 1.4, 0.997) * 0.5, t0, 0.5, 0.55)
        P(buf, ac.cuerda(nota(bajo + 7), 1.0, 0.997) * 0.4, t0 + 3 * CORCHEA, 0.45, 0.55)
        for k in range(6):
            fuerte = 1.0 if k in (0, 3) else 0.55
            P(buf, rasguido(voces, fuerte, abajo=(k % 2 == 0)), t0 + k * CORCHEA + 0.004, 0.6, 0.6)
    # violín cada 2 compases
    for b in range(0, compases, 2):
        frase = MELODIA[(b // 2) % len(MELODIA)]
        for pos, durc, m in frase:
            P(buf, violin(nota(m), durc * CORCHEA + 0.05), b * COMPAS + pos * CORCHEA, 0.55, 0.4)
    buf = ac._reverb(buf, 0.2, 1.5)
    return buf[:int(dur * SR)]


def cargar_cancion(dur):
    tmp = "videos_salida/_cancion.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(CANCION_INICIO), "-i", CANCION, "-t", str(dur + 1),
                    "-ac", "2", "-ar", str(SR), tmp], check=True)
    sr, x = wavfile.read(tmp)
    x = x.astype(np.float32) / 32768
    out = np.zeros((int(dur * SR), 2), np.float32)
    out[:min(len(x), len(out))] = x[:len(out)]
    return out


# ------------------------------------------------------------ mezcla
def env_voz(v, ms=40):
    k = int(SR * ms / 1000)
    return np.sqrt(np.convolve(v ** 2, np.ones(k) / k, mode="same"))


def generar_audio(ruta="videos_salida/_oferta_voz_audio.wav"):
    n = int(DUR * SR)
    # voz
    voz = np.zeros(n, np.float32)
    for t0, txt in LOCUCION:
        x = voz_tts.clip(txt, voz=VOZ, rate=RATE)
        x = x * (10 ** (-17 / 20) / (np.sqrt((x ** 2).mean()) + 1e-9))
        x = np.tanh(x * 1.5) / 1.5
        i = int(t0 * SR)
        voz[i:i + x.size] += x[:max(0, n - i)]
    voz = sosfilt(butter(2, 80, btype="highpass", fs=SR, output="sos"), voz)
    # música
    usa_cancion = Path(CANCION).exists()
    musica = cargar_cancion(DUR) if usa_cancion else chacarera(DUR)
    musica = musica[:n] * (10 ** (-22 / 20) / (np.sqrt((musica[:n] ** 2).mean()) + 1e-9))
    # cámara lenta: música "bajo el agua"
    lento = np.zeros(n)
    for r in (o20.R_C1, o20.R_C2):
        tg = r[0] + (og.STAMP + 0.14) * 1.6
        lento[int(tg * SR):int((tg + o20.SLOWMO) * SR)] = 1
    k = int(0.12 * SR)
    lento = np.convolve(lento, np.ones(k) / k, mode="same")
    apagada = np.stack([au._filtro(musica[:, c], "lowpass", 420) for c in range(2)], 1)
    musica = musica * (1 - lento[:, None]) + apagada * lento[:, None]
    # la música baja ~12 dB cuando habla la voz
    activa = (env_voz(voz) > 0.012).astype(np.float32)
    k = int(SR * 0.35)
    sub = np.convolve(np.pad(activa, (k, k), mode="edge"), np.ones(k) / k, mode="same")[k:-k]
    musica = musica * (1 - 0.75 * np.clip(sub, 0, 1))[:, None]
    # efectos (más suaves que en la versión sin voz)
    sfx = np.zeros((n + SR, 2))
    P = au._poner
    P(sfx, og.braam(2.0, 55.0), 0.55, 0.6)
    P(sfx, au.golpe(), 0.62, 0.7)
    for c0, c1 in ((o20.R_INTRO[1], o20.R_C1[0]), (o20.R_C1[1], o20.R_C2[0]), (o20.R_C2[1], o20.R_FIN[0])):
        P(sfx, au.whoosh(0.6), (c0 + c1) / 2 - 0.3, 0.35)
    for r in (o20.R_C1, o20.R_C2):
        ts = r[0] + (og.STAMP + 0.05) * 1.6
        P(sfx, og.riser(1.2), ts - 1.2, 0.18)
        P(sfx, au.golpe(), ts, 0.75)
        P(sfx, og.crash(2.0), ts, 0.25)
        P(sfx, og.cha_ching(), ts + 0.1, 0.3)
    P(sfx, au.golpe(), o20.R_FIN[0] + 0.3, 0.6)
    mix = musica + sfx[:n] * 0.8 + np.repeat(voz[:, None], 2, axis=1)
    fo = int(0.3 * SR)
    mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    mix = np.tanh(mix * 1.05)
    mix *= 0.9 / np.abs(mix).max()
    tmp = "videos_salida/_oferta_voz_crudo.wav"
    wavfile.write(tmp, SR, (mix * 32767).astype(np.int16))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af", "loudnorm=I=-14:TP=-1.2:LRA=9", "-ar", str(SR), ruta],
                   check=True)
    print("música:", "canción " + CANCION if usa_cancion else "chacarera instrumental provisoria")
    return ruta


def main():
    o20.ESCENAS = o20.armar()
    Path("videos_salida").mkdir(exist_ok=True)
    wav = generar_audio()
    pista = AudioFileClip(wav)
    video = VideoClip(o20.make_frame, duration=DUR).with_audio(pista.subclipped(0, min(DUR, pista.duration)))
    video.write_videofile(SALIDA, fps=30, codec="libx264", audio_codec="aac", audio_bitrate="192k", preset="medium",
                          ffmpeg_params=["-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart"])
    print("Listo:", SALIDA)


if __name__ == "__main__":
    main()
