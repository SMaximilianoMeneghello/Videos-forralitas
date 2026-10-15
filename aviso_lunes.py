"""Aviso corto: hoy lunes 12/10 Forralitas atiende todo el día hasta las 19 hs.

Uso:
    python aviso_lunes.py                  # genera videos_salida/aviso_lunes_12_10.mp4
    python aviso_lunes.py --frames 1 5 9   # vistas previas
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from moviepy import AudioFileClip, VideoClip
from PIL import Image

import estilo2 as e2
import estilo_catalogo as ec
import estilo_voz as ev
import voz_tts
from efectos import H, W, blit, caja, clamp01, ease_out_back, ease_out_cubic, logo_redondo, prog, sobre

SR, FPS, TR = voz_tts.SR, e2.FPS, 0.6
SALIDA = "videos_salida/aviso_lunes_12_10.mp4"
T, Titulo, VERDE_OSC, TRIGO, TIERRA, CREMA = e2.T, e2.Titulo, e2.VERDE_OSC, e2.TRIGO, e2.TIERRA, e2.CREMA
N, P = ec.N, ec.P

F1 = "¡Atención! Hoy lunes doce de octubre, Forralitas atiende todo el día."
F2 = "Te esperamos hasta las diecinueve horas."
F3 = "Aprovechá para comprar productos de primera calidad, y al mejor precio."

LOGO = logo_redondo(430)
LOGO_SOMBRA = e2.sombra_de(LOGO[:, :, 3], 60, 0.35, 20)


def reloj(f, cx, cy, r, t, t0):
    """Reloj que marca las 19:00 con la aguja grande girando hasta su lugar."""
    q = ease_out_cubic(prog(t, t0, 1.2))
    cv2.circle(f, (cx, cy + 10), r + 14, (150, 140, 120), -1, cv2.LINE_AA)
    cv2.circle(f, (cx, cy), r + 12, VERDE_OSC, -1, cv2.LINE_AA)
    cv2.circle(f, (cx, cy), r - 6, (255, 252, 244), -1, cv2.LINE_AA)
    for i in range(12):
        a = i * np.pi / 6
        p0 = (int(cx + (r - 14) * np.sin(a)), int(cy - (r - 14) * np.cos(a)))
        p1 = (int(cx + (r - 34) * np.sin(a)), int(cy - (r - 34) * np.cos(a)))
        cv2.line(f, p0, p1, TIERRA, 6 if i % 3 == 0 else 3, cv2.LINE_AA)
    amin = 2 * np.pi * (3 - 3 * q)                      # minutero: gira y termina en las 12
    ahor = np.pi * 2 * (19 % 12) / 12 - (1 - q) * np.pi * 1.3
    cv2.line(f, (cx, cy), (int(cx + (r - 50) * np.sin(amin)), int(cy - (r - 50) * np.cos(amin))), VERDE_OSC, 8, cv2.LINE_AA)
    cv2.line(f, (cx, cy), (int(cx + (r - 105) * np.sin(ahor)), int(cy - (r - 105) * np.cos(ahor))), TIERRA, 14, cv2.LINE_AA)
    cv2.circle(f, (cx, cy), 15, TRIGO, -1, cv2.LINE_AA)


def escena_hoy(g0, dur):
    kick = e2.texto_espaciado("AVISO IMPORTANTE", 36, TIERRA, e2.SANS, 10)
    fecha = T("HOY LUNES 12/10", 96, CREMA, e2.SERIF)
    pastilla = sobre(caja(fecha.shape[1] + 40, fecha.shape[0] - 6, 56, VERDE_OSC, 0.97), fecha, 20, -3)
    l1 = Titulo("Atendemos *todo el día*", 96, W - 90)
    sub = T("Forrajería y Semillería", 46, TIERRA, e2.SANS_SEMI)

    def fn(t):
        f = e2.fondo_papel(g0 + t)
        q = prog(t, 0.0, 0.9)
        e = ease_out_back(q, 1.3)
        cx, cy = W / 2, 560
        cv2.circle(f, (int(cx), int(cy)), int(300 + 14 * np.sin(t * 2)), TRIGO, 10, cv2.LINE_AA)
        blit(f, LOGO_SOMBRA, cx, cy + 20, alpha=clamp01(q * 2), escala=0.7 + 0.3 * e, centro=True)
        blit(f, LOGO, cx, cy, alpha=clamp01(q * 2.5), escala=(0.7 + 0.3 * e) * (1 + 0.012 * np.sin(t * 2)), centro=True)
        k = ease_out_cubic(prog(t, 0.7, 0.5))
        blit(f, kick, (W - kick.shape[1]) / 2, 960, alpha=k)
        p = prog(t, 0.9, 0.6)
        blit(f, pastilla, (W - pastilla.shape[1]) / 2, 1030 + (1 - ease_out_cubic(p)) * 60, alpha=ease_out_cubic(p * 2),
             escala=0.9 + 0.1 * ease_out_back(p, 1.6))
        l1.draw(f, 1215, t, 1.5, paso=0.12)
        blit(f, sub, (W - sub.shape[1]) / 2, 1350, alpha=ease_out_cubic(prog(t, 2.4, 0.6)))
        e2.dibujar_ticker(f, g0 + t, prog(t, 0.2, 0.6))
        return f
    return fn


def escena_hasta(g0, dur):
    l1 = Titulo("Hasta las *19 hs*", 130, W - 90)
    l2 = Titulo("¡Te esperamos!", 90, W - 90)
    horas = T("Abierto de corrido", 52, TIERRA, e2.SANS_SEMI)

    def fn(t):
        f = e2.fondo_papel(g0 + t)
        e2.cabecera(f, t)
        q = prog(t, 0.1, 0.7)
        s = 0.85 + 0.15 * ease_out_back(q, 1.3)
        reloj_f = f.copy()
        reloj(reloj_f, W // 2, 760, int(300 * s), t, 0.5)
        m = clamp01(q * 2.5)
        f[:] = cv2.addWeighted(reloj_f, m, f, 1 - m, 0)
        l1.draw(f, 1170, t, 0.9, paso=0.14)
        blit(f, horas, (W - horas.shape[1]) / 2, 1330, alpha=ease_out_cubic(prog(t, 1.6, 0.6)))
        l2.draw(f, 1410, t, 2.0, paso=0.1)
        e2.dibujar_ticker(f, g0 + t, prog(t, 0.2, 0.6))
        return f
    return fn


def escena_precio(g0, dur):
    rutas = [N + "n10.jpg", N + "n12.jpg", N + "n09.jpg", N + "n13.jpg"]
    cams = [(1.0, 1.2, (0.2, 0.5), (0.8, 0.5)), (1.0, 1.2, (0.8, 0.5), (0.2, 0.5)),
            (1.0, 1.18, (0.5, 0.2), (0.5, 0.8)), (1.0, 1.2, (0.3, 0.6), (0.7, 0.4))]
    tarjeta = ec.Tarjeta(rutas, cams, cuts=[0.0, 0.26, 0.52, 0.76])
    l1 = Titulo("Productos de *1ª calidad*", 88, W - 90)
    l2 = Titulo("al *mejor precio*", 108, W - 90)
    c2 = ev.frac(F3, "y al mejor") * 0.9

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


def escena_final(g0, dur):
    logo = logo_redondo(300)
    l0 = Titulo("*Forralitas*", 120, W - 90)
    l1 = Titulo("Hoy abierto hasta las *19 hs*", 70, W - 70)
    card = caja(940, 150, 38, VERDE_OSC, 0.96)
    u1 = T("Ruta 305 km 7,5 · Las Talitas", 52, CREMA, e2.SANS_SEMI)
    card = sobre(card, u1, (940 - u1.shape[1]) // 2, (150 - u1.shape[0]) // 2)
    tel = caja(940, 150, 38, TRIGO)
    t1 = T("381 526 9004  ·  381 633 4344", 54, VERDE_OSC, e2.SANS)
    tel = sobre(tel, t1, (940 - t1.shape[1]) // 2, (150 - t1.shape[0]) // 2)

    def fn(t):
        f = e2.fondo_papel(g0 + t)
        q = prog(t, 0.0, 0.8)
        blit(f, logo, W / 2, 470, alpha=clamp01(q * 2.5), escala=0.7 + 0.3 * ease_out_back(q, 1.3), centro=True)
        l0.draw(f, 700, t, 0.5, paso=0.1)
        l1.draw(f, 880, t, 1.0, paso=0.08)
        for spr, y, t0 in ((card, 1060, 1.6), (tel, 1250, 2.1)):
            p = prog(t, t0, 0.6)
            blit(f, spr, W / 2, y + (1 - ease_out_cubic(p)) * 80, alpha=ease_out_cubic(p * 2), centro=True,
                 escala=0.92 + 0.08 * ease_out_back(p, 1.4))
        e2.dibujar_ticker(f, g0 + t, prog(t, 0.2, 0.6))
        return f
    return fn


MODELO = "/tmp/claude-0/-home-user-Videos-forralitas/df62490c-9a54-5d48-b887-16a37994cf35/scratchpad/pv/es_AR-daniela-high.onnx"


def clip_local(texto):
    """Locución con Piper (voz es_AR, sin internet) cuando la voz neuronal de Edge no está disponible."""
    import hashlib, subprocess
    from scipy.io import wavfile
    h = hashlib.md5(texto.encode()).hexdigest()[:10]
    crudo, wav = f"voz/piper_{h}_raw.wav", f"voz/piper_{h}.wav"
    if not Path(wav).exists():
        subprocess.run([sys.executable, "-m", "piper", "-m", MODELO, "-f", crudo, "--length-scale", "0.93", "--", texto], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", crudo, "-ac", "1", "-ar", str(SR), wav], check=True)
    _, x = wavfile.read(wav)
    x = x.astype(np.float32) / 32768
    idx = np.where(np.abs(x) > 0.012)[0]
    return x[max(idx[0] - int(0.02 * SR), 0): idx[-1] + int(0.04 * SR)]


def clip_voz(texto, rate=None):
    """Voz de siempre (Edge es-AR-TomasNeural); si el entorno la bloquea, usa Piper y avisa."""
    global VOZ_ORIGINAL
    try:
        return voz_tts.clip(texto, rate=rate)
    except Exception:
        VOZ_ORIGINAL = False
        return clip_local(texto)


VOZ_ORIGINAL = True


def cierre(cl):
    """Cierre estándar de todos los videos: teléfonos, horarios, ubicación, envíos, mayor/menor y medios de pago."""
    d = lambda x: len(x) / SR
    # cierre completo (igual que el resto de los videos): teléfonos, horarios, envíos, mayor/menor y medios de pago
    cc = [(k, cl(t, rate=ev.RATE_RAPIDO.get(k))) for k, t in ec.CIERRE]
    t_loc, cur = {}, 0.75
    for k, x in cc:
        t_loc[k] = cur
        cur += d(x) + ev.GAP
    d_c = t_loc["firma"] + d(cc[-1][1]) + 1.6
    cv = ec.cv
    cv.T_TEL, cv.T_HORA = t_loc["tel"] - 0.12, t_loc["hora"] - 0.12
    cv.T_UBIC = t_loc["hora"] + d(dict(cc)["hora"]) - 0.1
    cv.T_ENVIO, cv.T_MAYOR, cv.T_PAGOS = t_loc["envio"] - 0.12, t_loc["mayor"] - 0.12, t_loc["pagos"] - 0.12
    cv.T_TIMBRE0, cv.PERIODO_TIMBRE = t_loc["tel"] + 0.2, 1.9
    pg, txt = dict(cc)["pagos"], dict(ec.CIERRE)["pagos"]
    cv.T_CHIPS = tuple(t_loc["pagos"] + ev.frac(txt, w) * d(pg) - 0.15
                       for w in ("efectivo", "transferencia", "débito", "crédito"))
    e2.TM["firma"] = t_loc["firma"] - 0.1
    return (d_c, lambda g0, d_: e2.escena_cierre(g0), [(t_loc[k], x) for k, x in cc], "d")



def construir():
    cl = clip_voz
    d = lambda x: len(x) / SR
    a1, a2, a3 = cl(F1), cl(F2), cl(F3)
    escenas = [
        (0.7 + d(a1) + TR + 0.3, lambda g0, d_: escena_hoy(g0, d_), [(0.7, a1)], "a"),
        (0.6 + d(a2) + TR + 1.6, lambda g0, d_: escena_hasta(g0, d_), [(0.6, a2)], "b"),
        (0.6 + d(a3) + TR + 0.6, lambda g0, d_: escena_precio(g0, d_), [(0.6, a3)], "c"),
    ]
    escenas.append(cierre(cl))

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


def hacer_frame_fn(segs, inicios, total):
    trans = [e2.tr_cortina, e2.tr_circulo, e2.tr_barras]

    def make_frame(t):
        t = min(t, total - 1e-3)
        act = [i for i, (s, (d, _)) in enumerate(zip(inicios, segs)) if s <= t < s + d]
        if len(act) == 1:
            return segs[act[0]][1](t - inicios[act[0]])
        a, b = act[0], act[-1]
        return trans[a](segs[a][1](t - inicios[a]), segs[b][1](t - inicios[b]), (t - inicios[b]) / TR)
    return make_frame


def main():
    segs, inicios, total, voces = construir()
    Path("videos_salida").mkdir(exist_ok=True)
    mf = hacer_frame_fn(segs, inicios, total)
    if "--frames" in sys.argv:
        for s in [float(x) for x in sys.argv[sys.argv.index("--frames") + 1:]]:
            Image.fromarray(mf(s)).save(f"videos_salida/prev_{s:05.1f}.png")
        print("duración total:", round(total, 2), "s | inicios:", [round(x, 1) for x in inicios])
        return
    wav = ev.mezclar(total, inicios, voces)
    pista = AudioFileClip(wav)
    video = VideoClip(mf, duration=total).with_audio(pista.subclipped(0, min(total, pista.duration)))
    video.write_videofile(SALIDA, fps=FPS, codec="libx264", audio_codec="aac", audio_bitrate="192k", preset="medium",
                          ffmpeg_params=["-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart"])
    if not VOZ_ORIGINAL:
        print("AVISO: la voz de Edge está bloqueada en este entorno; se usó la voz de respaldo (Piper).")
    print("Listo:", SALIDA, f"({total:.1f} s)")


if __name__ == "__main__":
    main()
