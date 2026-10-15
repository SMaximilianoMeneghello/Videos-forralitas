"""Dos videos: "nuevo ingreso de virutas" y "gracias por la compra de alfa" (fotos mejoradas con mejorar_fotos.py).

Uso:
    python videos_ingreso.py virutas                 # genera videos_salida/ingreso_virutas.mp4
    python videos_ingreso.py alfa                    # genera videos_salida/gracias_alfa.mp4
    python videos_ingreso.py virutas --frames 2 6 10 # vistas previas
El cierre (teléfonos, horarios, ubicación, envíos, mayor/menor y pagos) sale de aviso_lunes.cierre().
"""
import sys
from pathlib import Path

import numpy as np
from moviepy import AudioFileClip, VideoClip
from PIL import Image

import aviso_lunes as av
import estilo2 as e2
import estilo_catalogo as ec
import estilo_voz as ev
from efectos import W, blit, clamp01, ease_out_back, ease_out_cubic, prog, sobre, caja

SR, FPS, TR = av.SR, av.FPS, av.TR
SALIDAS = {"virutas": "videos_salida/ingreso_virutas.mp4", "alfa": "videos_salida/gracias_alfa.mp4"}
G = "assets/ingreso/"
T, Titulo, TIERRA = e2.T, e2.Titulo, e2.TIERRA

TEXTOS = {
    "virutas": ["¡Llegó mercadería nueva a Forralitas!", "Nuevo ingreso de virutas.",
                "Productos de primera calidad, y al mejor precio."],
    "alfa": ["¡Gracias por tu compra de alfa!", "Gracias por la confianza.",
             "Nos comprometemos a seguir ofreciéndote productos de primera calidad, y al mejor precio."],
}
F4 = TEXTOS["virutas"][2]

CAM = [(1.0, 1.25, (0.2, 0.55), (0.8, 0.5)), (1.0, 1.22, (0.8, 0.5), (0.25, 0.55)),
       (1.0, 1.25, (0.5, 0.75), (0.5, 0.3)), (1.0, 1.2, (0.3, 0.4), (0.7, 0.6))]


def intro(kicker, m1, m2):
  def ctor(g0, dur):
    kick = e2.texto_espaciado(kicker, 40, TIERRA, e2.SANS, 12)
    l1 = Titulo(m1, 100, W - 90)
    l2 = Titulo(m2, 130, W - 90)
    sub = T("Forrajería y Semillería", 46, TIERRA, e2.SANS_SEMI)

    def fn(t):
        f = e2.fondo_papel(g0 + t)
        q = prog(t, 0.0, 0.9)
        e = ease_out_back(q, 1.3)
        cx, cy = W / 2, 560
        blit(f, av.LOGO_SOMBRA, cx, cy + 20, alpha=clamp01(q * 2), escala=0.7 + 0.3 * e, centro=True)
        blit(f, av.LOGO, cx, cy, alpha=clamp01(q * 2.5), escala=(0.7 + 0.3 * e) * (1 + 0.012 * np.sin(t * 2)), centro=True)
        blit(f, kick, (W - kick.shape[1]) / 2, 960, alpha=ease_out_cubic(prog(t, 0.7, 0.5)))
        l1.draw(f, 1040, t, 0.9, paso=0.12)
        l2.draw(f, 1170, t, 1.5, paso=0.12)
        blit(f, sub, (W - sub.shape[1]) / 2, 1350, alpha=ease_out_cubic(prog(t, 2.0, 0.6)))
        e2.dibujar_ticker(f, g0 + t, prog(t, 0.2, 0.6))
        return f
    return fn
  return ctor


def escena_producto(rutas, cuts, titulo_m, kicker_txt, dur_total=None):
    def ctor(g0, dur):
        tarjeta = ec.Tarjeta(rutas, CAM[: len(rutas)], cuts=cuts)
        kick = e2.texto_espaciado(kicker_txt, 34, TIERRA, e2.SANS, 10)
        tit = Titulo(titulo_m, 112, W - 90)

        def fn(t):
            f = e2.fondo_papel(g0 + t)
            tarjeta.dibujar(f, t, dur)
            e2.cabecera(f, t)
            ec.placa(f, t, 0.3, alta=True, cy=1380)
            blit(f, kick, (W - kick.shape[1]) / 2, 1248, alpha=ease_out_cubic(prog(t, 0.55, 0.5)))
            tit.draw(f, 1310, t, 0.7, paso=0.14)
            e2.dibujar_ticker(f, g0 + t, prog(t, 0.2, 0.6))
            return f
        return fn
    return ctor


def escena_precio(rutas, cuts, frase=None):
    def ctor(g0, dur):
        tarjeta = ec.Tarjeta(rutas, CAM[: len(rutas)], cuts=cuts)
        l1 = Titulo("Productos de *1ª calidad*", 88, W - 90)
        l2 = Titulo("al *mejor precio*", 108, W - 90)
        c2 = ev.frac(F4, "y al mejor") * 0.9

        def fn(t):
            f = e2.fondo_papel(g0 + t)
            tarjeta.dibujar(f, t, dur)
            e2.cabecera(f, t)
            ec.placa(f, t, 0.3, alta=True, cy=1380)
            l1.draw(f, 1245, t, 0.5, paso=0.1)
            l2.draw(f, 1355, t, 0.5 + c2 * dur, paso=0.12)
            e2.dibujar_ticker(f, g0 + t, prog(t, 0.2, 0.6))
            return f
        return fn
    return ctor


def construir(modo):
    cl = av.clip_voz
    d = lambda x: len(x) / SR
    t1, t2, t3 = TEXTOS[modo]
    a1, a2, a3 = cl(t1), cl(t2), cl(t3)
    if modo == "virutas":
        V = [G + "viruta1.jpg", G + "viruta3.jpg", G + "viruta2.jpg", ec.P + "14_virutas.jpg"]
        escenas = [
            (0.7 + d(a1) + TR + 0.5, intro("NUEVO INGRESO", "¡Llegó *mercadería*", "*nueva!*"), [(0.7, a1)], "a"),
            (max(0.6 + d(a2) + TR + 3.8, 5.4), escena_producto(V, [0.0, 0.25, 0.5, 0.75], "Nuevo ingreso de *virutas*", "LLEGARON"),
             [(0.6, a2)], "b"),
            (0.6 + d(a3) + TR + 1.0, escena_precio([V[0], V[1], V[2]], [0.0, 0.34, 0.67]), [(0.6, a3)], "c"),
        ]
    else:
        A = [G + "alfa1.jpg", ec.N + "n08.jpg", ec.P + "01_alfa.jpg"]
        escenas = [
            (0.7 + d(a1) + TR + 0.5, intro("GRACIAS", "¡Gracias por tu", "*compra!*"), [(0.7, a1)], "a"),
            (max(0.6 + d(a2) + TR + 3.8, 5.4), escena_producto(A, [0.0, 0.4, 0.7], "Gracias por la *confianza*", "COMPRA DE ALFA"),
             [(0.6, a2)], "b"),
            (0.6 + d(a3) + TR + 1.0, escena_gracias_final(A), [(0.6, a3)], "c"),
        ]
    escenas.append(av.cierre(cl))
    inicios, t = [], 0.0
    for dur, *_ in escenas:
        inicios.append(t)
        t += dur - TR
    total = inicios[-1] + escenas[-1][0]
    segs, voces = [], []
    for (dur, ctor, vs, _), t0 in zip(escenas, inicios):
        segs.append((dur, ctor(t0, dur)))
        voces += [(t0 + off, x) for off, x in vs]
    return segs, inicios, total, voces


def escena_gracias_final(rutas):
    def ctor(g0, dur):
        tarjeta = ec.Tarjeta(rutas, CAM[: len(rutas)], cuts=[0.0, 0.34, 0.67])
        l1 = Titulo("Productos de *1ª calidad*", 88, W - 90)
        l2 = Titulo("al *mejor precio*", 108, W - 90)

        def fn(t):
            f = e2.fondo_papel(g0 + t)
            tarjeta.dibujar(f, t, dur)
            e2.cabecera(f, t)
            ec.placa(f, t, 0.3, alta=True, cy=1380)
            l1.draw(f, 1245, t, 0.5, paso=0.1)
            l2.draw(f, 1355, t, 1.3, paso=0.12)
            e2.dibujar_ticker(f, g0 + t, prog(t, 0.2, 0.6))
            return f
        return fn
    return ctor


def hacer_frame_fn(segs, inicios, total):
    trans = [e2.tr_cortina, e2.tr_circulo, e2.tr_persianas, e2.tr_barras]

    def make_frame(t):
        t = min(t, total - 1e-3)
        act = [i for i, (s, (d, _)) in enumerate(zip(inicios, segs)) if s <= t < s + d]
        if len(act) == 1:
            return segs[act[0]][1](t - inicios[act[0]])
        a, b = act[0], act[-1]
        return trans[a % len(trans)](segs[a][1](t - inicios[a]), segs[b][1](t - inicios[b]), (t - inicios[b]) / TR)
    return make_frame


def main():
    modo = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] in SALIDAS else None
    if modo is None:
        sys.exit("Uso: python videos_ingreso.py virutas|alfa [--frames t1 t2 ...]")
    segs, inicios, total, voces = construir(modo)
    Path("videos_salida").mkdir(exist_ok=True)
    mf = hacer_frame_fn(segs, inicios, total)
    if "--frames" in sys.argv:
        for s in [float(x) for x in sys.argv[sys.argv.index("--frames") + 1:]]:
            Image.fromarray(mf(s)).save(f"videos_salida/prev_{modo}_{s:05.1f}.png")
        print("duración total:", round(total, 2), "s | inicios:", [round(x, 1) for x in inicios])
        return
    wav = ev.mezclar(total, inicios, voces)
    pista = AudioFileClip(wav)
    video = VideoClip(mf, duration=total).with_audio(pista.subclipped(0, min(total, pista.duration)))
    video.write_videofile(SALIDAS[modo], fps=FPS, codec="libx264", audio_codec="aac", audio_bitrate="192k", preset="medium",
                          ffmpeg_params=["-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart"])
    if not av.VOZ_ORIGINAL:
        print("AVISO: la voz de Edge está bloqueada en este entorno; se usó la voz de respaldo (Piper).")
    print("Listo:", SALIDAS[modo], f"({total:.1f} s)")


if __name__ == "__main__":
    main()
