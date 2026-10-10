"""Video Forralitas con locución (voz neuronal) y música suave que baja cuando se habla.

Uso:
    python estilo_voz.py                  # genera videos_salida/forralitas_voz.mp4
    python estilo_voz.py --frames 2 6 12  # vistas previas
    python estilo_voz.py --audio          # solo genera el audio mezclado (voz + música)

La duración de cada escena la marca la locución: se mide cada frase y las animaciones
se sincronizan con lo que se dice. Voz y velocidad: VOZ / RATE en voz_tts.py.
"""
import subprocess
import sys
from pathlib import Path

import numpy as np
from moviepy import AudioFileClip, VideoClip
from PIL import Image
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

import audio_campo
import audio_suave
import crear_video as cv
import estilo2 as e2
import voz_tts

SR = voz_tts.SR
TR = e2.TR
PRODUCTOS = e2.PRODUCTOS

# Lo que se dice (misma información que los subtítulos; números y marcas escritos como se pronuncian)
FRASES_A = "¿Sos de Las Talitas y no sabés dónde comprar alimentos para tus animales?"
FRASES_B1 = "Te presento Forralitas."
FRASES_B2 = "Estamos ubicados en ruta trescientos cinco, kilómetro siete coma cinco. Las Talitas."
DICHO_PRODUCTO = [
    "Tenemos alfa.",
    "Engorde de cerdo. Bolsa por treinta kilos y suelto.",
    "Mezcla de caballo. Bolsa por treinta y cinco kilos y suelto.",
    "Pélet de alfa.",
    "Maíz entero.",
    "Maíz quebrado. Bolsa por cuarenta kilos y suelto.",
    "Pélet de trigo. Bolsa por treinta kilos y suelto.",
    "Afrecho de trigo.",
    "Afrecho de maíz. Por bolsa y suelto.",
    "Ponedora para gallinas. Por bolsa y suelto.",
    "Iniciador parrillero.",
    "Engorde terminador.",
    "Alimentos para perro y gato.",
    "Virutas.",
]
FRASE_MOSAICO = "¡Y mucho más!"
CIERRE = [
    ("tit", "¡Te esperamos!"),
    ("tel", "Llamanos al tres ocho uno, cinco dos seis, nueve cero cero cuatro, "
            "o al tres ocho uno, seis tres tres, cuatro tres cuatro cuatro."),
    ("hora", "De lunes a viernes de ocho a diecinueve horas, y sábados de ocho y media a diecinueve horas."),
    ("ubic", "Ruta trescientos cinco, kilómetro siete coma cinco, Las Talitas."),
    ("envio", "Hacemos envíos según la zona."),
    ("mayor", "Venta por mayor y menor."),
    ("pagos", "Aceptamos todos los medios de pago: efectivo, transferencia, débito y crédito."),
    ("firma", "Forralitas. Todo para tus animales."),
]
GAP = 0.15
RATE_RAPIDO = {"tel": "+16%", "hora": "+10%"}


def frac(texto, hasta):
    """Fracción de la frase (por letras) que se dice antes de `hasta`."""
    i = texto.index(hasta)
    return len(texto[:i]) / len(texto)


def construir():
    fotos = sorted(Path("fotos_presentacion").glob("*.jp*g"), key=lambda p: p.name)
    assert len(fotos) == len(PRODUCTOS) == len(DICHO_PRODUCTO)
    cl = voz_tts.clip
    dur = lambda x: len(x) / SR
    voces = []                     # (instante global, audio)

    # ---- escena A (dron 1)
    a = cl(FRASES_A)
    a0 = 0.45
    D_A = a0 + dur(a) + TR
    e2.TM["a_top"] = a0 + 0.02
    e2.TM["a_l1"] = a0 + frac(FRASES_A, "y no sabés") * dur(a) - 0.15
    e2.TM["a_l2"] = a0 + frac(FRASES_A, "alimentos") * dur(a) - 0.1
    # ---- escena B (dron 2)
    b1, b2 = cl(FRASES_B1), cl(FRASES_B2)
    b10 = 0.8
    b20 = b10 + dur(b1) + 0.25
    D_B = b20 + dur(b2) + TR
    e2.TM["b_pin"] = b20 - 0.35
    e2.TM["b_est"] = b20 - 0.05
    e2.TM["b_ruta"] = b20 + frac(FRASES_B2, "ruta") * dur(b2) - 0.1
    e2.TM["b_tal"] = b20 + frac(FRASES_B2, "Las Talitas") * dur(b2) - 0.1
    # ---- productos
    ps = [cl(t) for t in DICHO_PRODUCTO]
    D_PS = [max(e2.D_PROD, 0.6 + dur(p) + TR - 0.1) for p in ps]
    # ---- mosaico
    m = cl(FRASE_MOSAICO)
    D_M = max(e2.D_MOS, 0.7 + dur(m) + 1.7)
    # ---- cierre: cada tarjeta entra cuando se dice
    cc = [(k, cl(t, rate=RATE_RAPIDO.get(k))) for k, t in CIERRE]
    t_loc, cur = {}, 0.75
    for k, x in cc:
        t_loc[k] = cur
        cur += dur(x) + GAP
    D_C = t_loc["firma"] + dur(cc[-1][1]) + 1.6

    cv.T_TEL, cv.T_HORA, cv.T_UBIC = t_loc["tel"] - 0.12, t_loc["hora"] - 0.12, t_loc["ubic"] - 0.12
    cv.T_ENVIO, cv.T_MAYOR, cv.T_PAGOS = t_loc["envio"] - 0.12, t_loc["mayor"] - 0.12, t_loc["pagos"] - 0.12
    cv.T_TIMBRE0, cv.PERIODO_TIMBRE = t_loc["tel"] + 0.2, 1.9
    pg = dict(cc)["pagos"]
    txt = dict(CIERRE)["pagos"]
    cv.T_CHIPS = tuple(t_loc["pagos"] + frac(txt, w) * dur(pg) - 0.15
                       for w in ("efectivo", "transferencia", "débito", "crédito"))
    e2.TM["firma"] = t_loc["firma"] - 0.1

    durs = [D_A, D_B] + D_PS + [D_M, D_C]
    inicios, t = [], 0.0
    for d in durs:
        inicios.append(t)
        t += d - TR
    total = inicios[-1] + durs[-1]

    voces += [(inicios[0] + a0, a), (inicios[1] + b10, b1), (inicios[1] + b20, b2)]
    for i, p in enumerate(ps):
        voces.append((inicios[2 + i] + 0.6, p))
    voces.append((inicios[-2] + 0.7, m))
    for k, x in cc:
        voces.append((inicios[-1] + t_loc[k], x))

    segs = [(D_A, e2.escena_dron("assets/dron/dron1.jpg", D_A, inicios[0], (60, 590, 960, 700),
                                 (1.0, 1.7, (0.5, 0.5), (0.2, 0.5), -1.5, 1.0), None, e2.decorado_a())),
            (D_B, e2.escena_dron("assets/dron/dron2.jpg", D_B, inicios[1], (60, 650, 960, 600),
                                 (1.0, 1.75, (0.5, 0.5), (0.42, 0.58), 1.2, -0.8), None, e2.decorado_b()))]
    variantes = ["tarjeta", "circulo", "diagonal"]
    for i, (ruta, (tit, sub)) in enumerate(zip(fotos, PRODUCTOS)):
        segs.append((D_PS[i], e2.escena_producto(ruta, i, tit, sub, D_PS[i], inicios[2 + i],
                                                 variantes[i % 3], e2.CAMARAS[i % len(e2.CAMARAS)])))
    elegidas = [fotos[i] for i in (0, 1, 2, 3, 4, 5, 6, 7, 9, 10, 12, 13)]
    nombres = ["Alfa", "Engorde de cerdo", "Mezcla de caballo", "Pellet de alfa", "Maíz entero", "Maíz quebrado",
               "Pellet de trigo", "Afrecho de trigo", "Ponedora", "Parrillero", "Perro y gato", "Virutas"]
    segs.append((D_M, e2.escena_mosaico(elegidas, nombres, D_M, inicios[-2])))
    segs.append((D_C, e2.escena_cierre(inicios[-1])))
    return segs, inicios, total, voces


# ------------------------------------------------------------ mezcla de audio
def _env(x, ms):
    k = int(SR * ms / 1000)
    return np.sqrt(np.convolve(x ** 2, np.ones(k) / k, mode="same"))


def mezclar(total, inicios, voces, ruta="videos_salida/_mezcla.wav", musica_fn=None, sfx_fn=None, sfx_gain=0.10):
    n = int(total * SR)
    voz = np.zeros(n, np.float32)
    for t0, x in voces:
        x = x * (10 ** (-19 / 20) / (np.sqrt((x ** 2).mean()) + 1e-9))          # mismo volumen en todas las frases
        x = np.tanh(x * 1.6) / 1.6
        i = int(t0 * SR)
        voz[i:i + x.size] += x[: max(0, n - i)]
    voz = sosfilt(butter(2, 70, btype="highpass", fs=SR, output="sos"), voz)

    musica = (musica_fn or audio_suave.musica)(total)
    musica = musica[:n] * (10 ** (-27 / 20) / (np.sqrt((musica ** 2).mean()) + 1e-9))
    # la música baja ~11 dB cuando hay voz (ataque rápido, vuelve despacio)
    activa = (_env(voz, 40) > 0.012).astype(np.float32)
    k = int(SR * 0.45)
    suave = np.convolve(np.pad(activa, (k, k), mode="edge"), np.ones(k) / k, mode="same")[k:-k]
    suave = np.maximum(suave, np.convolve(np.pad(activa, (k, 0)), np.ones(int(SR * 0.08)) / int(SR * 0.08), mode="same")[k:])
    ganancia = 1 - 0.72 * np.clip(suave, 0, 1)

    sfx = np.zeros((n, 2))
    for t in inicios[1:]:
        s = (sfx_fn or audio_campo.sutil_viento)()
        i = int((t + 0.05) * SR)
        sfx[i:i + s.size] += (s * sfx_gain)[: max(0, n - i), None]
    mix = musica * ganancia[:, None] + sfx * ganancia[:, None] + np.repeat(voz[:, None], 2, axis=1)
    fi, fo = int(0.8 * SR), int(2.5 * SR)
    mix[:fi] *= np.linspace(0, 1, fi)[:, None]
    mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    mix = np.tanh(mix * 1.05)
    mix *= 0.9 / np.abs(mix).max()
    tmp = "videos_salida/_mezcla_cruda.wav"
    wavfile.write(tmp, SR, (mix * 32767).astype(np.int16))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af", "loudnorm=I=-16:TP=-1.5:LRA=9", "-ar", str(SR), ruta],
                   check=True)
    return ruta


def main():
    segs, inicios, total, voces = construir()
    Path("videos_salida").mkdir(exist_ok=True)
    if "--frames" in sys.argv:
        mf = e2.hacer_frame_fn(segs, inicios, total)
        for s in [float(x) for x in sys.argv[sys.argv.index("--frames") + 1:]]:
            Image.fromarray(mf(s)).save(f"videos_salida/prev_{s:05.1f}.png")
        print("duración total:", round(total, 2), "s | inicios:", [round(x, 1) for x in inicios])
        return
    audio_wav = mezclar(total, inicios, voces)
    print("audio listo:", audio_wav, f"({total:.1f} s)")
    if "--audio" in sys.argv:
        return
    make_frame = e2.hacer_frame_fn(segs, inicios, total)
    salida = "videos_salida/forralitas_voz.mp4"
    video = VideoClip(make_frame, duration=total).with_audio(AudioFileClip(audio_wav).subclipped(0, total))
    video.write_videofile(salida, fps=e2.FPS, codec="libx264", audio_codec="aac", audio_bitrate="192k",
                          preset="medium", ffmpeg_params=["-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart"])
    print("Listo:", salida, f"({total:.1f} s)")


if __name__ == "__main__":
    main()
