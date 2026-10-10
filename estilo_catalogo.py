"""Video Forralitas "por animal": ¿Para caballos? / cerdos / gallinas / perros y gatos, con locución.

Uso:
    python estilo_catalogo.py                  # genera videos_salida/forralitas_catalogo.mp4
    python estilo_catalogo.py --frames 2 6 12  # vistas previas
    python estilo_catalogo.py --audio          # solo el audio mezclado

Qué foto va con cada producto: ver CATALOGO (abajo). Los textos de contacto, horarios y pagos
salen de CONFIG en crear_video.py. La duración de cada escena la marca la locución.
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from moviepy import AudioFileClip, VideoClip
from PIL import Image

import crear_video as cv
import estilo2 as e2
import estilo_voz as ev
import voz_tts
from efectos import H, W, blit, clamp01, ease_in_out, ease_out_back, ease_out_cubic, prog

SR = voz_tts.SR
TR = 0.6
FPS = e2.FPS
SALIDA = "videos_salida/forralitas_catalogo.mp4"
N = "assets/nuevas/"
P = "fotos_presentacion/"

# (título en pantalla, subtítulo, lo que dice la voz, foto)
CATALOGO = [
    ("caballos", "¿Para *caballos?*", "¿Para caballos?", N + "n03.png", [
        ("*Alfa*", "", "Alfa.", N + "n08.jpg"),
        ("Pellet de *trigo*", "Bolsa x 30 kg y suelto", "Pélet de trigo. Bolsa por treinta kilos y suelto.", N + "n12.jpg"),
        ("Mezcla de *caballo* preparada", "Bolsa x 35 kg y suelto",
         "Mezcla de caballo preparada. Bolsa por treinta y cinco kilos y suelto.", N + "n10.jpg"),
        ("Maíz *quebrado*", "Bolsa x 40 kg y suelto", "Maíz quebrado. Bolsa por cuarenta kilos y suelto.", N + "n11.jpg"),
        ("Maíz *entero*", "", "Maíz entero.", P + "05_maiz_entero.jpg"),
    ]),
    ("cerdos", "¿Para *cerdos?*", "¿Para cerdos?", N + "n02.png", [
        ("Mezcla para *cerdo* preparada", "", "Mezcla para cerdo preparada.", P + "02_engorde_cerdo.jpg"),
        ("Pellet con *maíz*", "Bolsa x 30 kg y suelto", "Pélet con maíz. Bolsa por treinta kilos y suelto.", N + "n09.jpg"),
        ("Engorde con *harina de carne*", "", "Engorde con harina de carne.", N + "n02.png"),
    ]),
    ("gallinas", "¿Para *gallinas?*", "¿Para gallinas?", N + "n01.png", [
        ("*Ponedora*", "Por bolsa y suelto", "Ponedora. Por bolsa y suelto.", N + "n13.jpg"),
        ("Afrecho de *maíz*", "Por bolsa y suelto", "Afrecho de maíz. Por bolsa y suelto.", N + "n14.jpg"),
        ("*Recría*", "", "Recría.", P + "11_iniciador_parrillero.jpg"),
        ("*Terminador* engorde", "", "Terminador, engorde.", P + "12_engorde_terminador.jpg"),
    ]),
    ("perros y gatos", "¿Para *perros* y *gatos?*", "¿Para perros y gatos?", "fotos/02_perros_gatos.jpg", [
        ("*Wenuy*", "", "Güenuy.", N + "n05.png"),
        ("*Sabrositos*", "", "Sabrositos.", "fotos/01_perros_sabrositos.jpg"),
        ("*Manada*", "", "Manada.", "fotos/02_perros_gatos.jpg"),
    ]),
]
FRASE_TODO = "Todo lo que buscás en un solo lugar, y al mejor precio."
FRASE_VISITA = "¿Qué esperás para visitarnos?"
FRASE_SOMOS = "Somos Forralitas."
FRASE_UBIC = "Estamos ubicados en ruta trescientos cinco, kilómetro siete coma cinco. Las Talitas."
CIERRE = [
    ("tit", "¡Te esperamos!"),
    ("tel", ev.CIERRE[1][1]),
    ("hora", ev.CIERRE[2][1]),
    ("envio", "Hacemos envíos según la zona."),
    ("mayor", "Venta por mayor y menor."),
    ("pagos", ev.CIERRE[6][1]),
    ("firma", ev.CIERRE[7][1]),
]
T, Titulo, CREMA, TRIGO, TIERRA, VERDE_OSC = e2.T, e2.Titulo, e2.CREMA, e2.TRIGO, e2.TIERRA, e2.VERDE_OSC
VARIANTES = ["tarjeta", "circulo", "diagonal"]
CW, CH, CY = 960, 1230, 835          # tarjeta de foto de las escenas "grandes"


def puntos(f, cur, total, t):
    """Indicador de sección (puntos) arriba a la derecha."""
    q = ease_out_cubic(prog(t, 0.3, 0.5))
    x0 = W - 66 - (total - 1) * 36
    for i in range(total):
        cx, cy = int(x0 + i * 36), 130
        if i == cur:
            cv2.circle(f, (cx, cy), int(13 * q), TRIGO, -1, cv2.LINE_AA)
        else:
            cv2.circle(f, (cx, cy), int(8 * q), TIERRA, -1, cv2.LINE_AA)


class Tarjeta:
    """Foto grande con marco, sombra y una hoja dorada detrás; admite una o varias fotos que se suceden."""

    def __init__(self, rutas, cams, w=CW, h=CH, cuts=None):
        self.visores = [e2.Visor(r, w, h) for r in rutas]
        self.cams = cams
        self.cuts = cuts or [0.0]
        self.masc = e2.mascara_redonda(w, h, 46)
        self.sombra = e2.sombra_de(self.masc)
        self.atras = e2.transformar(e2.caja(w + 30, h + 30, 54, TRIGO), 1.0, -2.6)
        self.atras2 = e2.transformar(e2.caja(w + 26, h + 26, 52, (255, 252, 244)), 1.0, 1.4)

    def foto(self, t, dur):
        p = t / dur
        n = len(self.visores)
        k = max(i for i in range(n) if p >= self.cuts[i])
        a, b = self.cuts[k], (self.cuts[k + 1] if k + 1 < n else 1.0)
        z0, z1, pa, pb = self.cams[k]
        img = self.visores[k].frame(clamp01((p - a) / (b - a)), z0, z1, pa, pb)
        if k > 0 and (p - a) * dur < 0.3:                 # fundido corto entre fotos
            z0, z1, pa, pb = self.cams[k - 1]
            ant = self.visores[k - 1].frame(1.0, z0, z1, pa, pb)
            m = (p - a) * dur / 0.3
            img = cv2.addWeighted(ant, 1 - m, img, m, 0)
        return img

    def dibujar(self, f, t, dur, cx=W / 2, cy=CY):
        q = prog(t, 0.0, 0.75)
        e = ease_out_back(q, 1.3)
        drop = (1 - ease_out_cubic(q)) * 420
        blit(f, self.atras, cx, cy + drop, alpha=clamp01(q * 3), escala=0.9 + 0.1 * e, centro=True)
        blit(f, self.atras2, cx, cy + drop, alpha=clamp01(q * 3), escala=0.9 + 0.1 * e, centro=True)
        blit(f, self.sombra, cx, cy + 22 + drop, alpha=clamp01(q * 2), escala=0.9 + 0.1 * e, centro=True)
        blit(f, e2.recortar(self.foto(t, dur), self.masc), cx, cy + drop, alpha=clamp01(q * 3),
             escala=0.9 + 0.1 * e, centro=True)


PLACA = e2.caja(1000, 250, 54, (255, 252, 244), 0.96)
PLACA_SOMBRA = e2.sombra_de(PLACA[:, :, 3], 40, 0.30, 14)
PLACA_ALTA = e2.caja(1000, 330, 54, (255, 252, 244), 0.96)
PLACA_ALTA_SOMBRA = e2.sombra_de(PLACA_ALTA[:, :, 3], 40, 0.30, 14)


def placa(f, t, t0, alta=False, cy=1400):
    q = prog(t, t0, 0.6)
    e = ease_out_back(q, 1.2)
    sp, sh = (PLACA_ALTA, PLACA_ALTA_SOMBRA) if alta else (PLACA, PLACA_SOMBRA)
    blit(f, sh, W / 2, cy + 14 + (1 - e) * 220, alpha=clamp01(q * 3), centro=True)
    blit(f, sp, W / 2, cy + (1 - e) * 220, alpha=clamp01(q * 3), centro=True)


# ------------------------------------------------------------ escenas
def escena_seccion(ruta, titulo_m, idx, g0, dur):
    tarjeta = Tarjeta([ruta], [(1.0, 1.2, (0.5, 0.65), (0.5, 0.4))])
    titulo = Titulo(titulo_m, 124, W - 90)

    def fn(t):
        gt = g0 + t
        f = e2.fondo_papel(gt)
        tarjeta.dibujar(f, t, dur)
        e2.cabecera(f, t)
        puntos(f, idx, 4, t)
        placa(f, t, 0.35)
        titulo.draw(f, 1318, t, 0.55, paso=0.14)
        e2.dibujar_ticker(f, gt, prog(t, 0.2, 0.6))
        return f
    return fn


def escena_todo(g0, dur, voz_txt):
    rutas = [N + "n06.png", N + "n05.png", N + "n07.png"]
    cams = [(1.0, 1.2, (0.1, 0.5), (0.8, 0.5)), (1.0, 1.22, (0.9, 0.5), (0.2, 0.5)), (1.0, 1.15, (0.5, 0.2), (0.5, 0.8))]
    tarjeta = Tarjeta(rutas, cams, cuts=[0.0, 0.36, 0.68])
    l1 = Titulo("Todo lo que *buscás*", 92, W - 90)
    l2 = Titulo("en un *solo lugar*", 92, W - 90)
    l3 = Titulo("y al *mejor precio*", 92, W - 90)
    c2 = ev.frac(voz_txt, "en un solo") * 0.85
    c3 = ev.frac(voz_txt, "y al mejor") * 0.85

    def fn(t):
        gt = g0 + t
        f = e2.fondo_papel(gt)
        tarjeta.dibujar(f, t, dur)
        e2.cabecera(f, t)
        placa(f, t, 0.3, alta=True, cy=1380)
        l1.draw(f, 1245, t, 0.45, paso=0.1)
        l2.draw(f, 1345, t, 0.45 + c2 * dur, paso=0.1)
        l3.draw(f, 1445, t, 0.45 + c3 * dur, paso=0.1)
        e2.dibujar_ticker(f, gt, prog(t, 0.2, 0.6))
        return f
    return fn


def escena_visita(g0, dur, voz_txt):
    tarjeta = Tarjeta([N + "n04.png"], [(1.0, 1.22, (0.08, 0.5), (0.92, 0.5))])
    l1 = Titulo("¿Qué *esperás*", 108, W - 90)
    l2 = Titulo("para *visitarnos?*", 108, W - 90)
    c2 = ev.frac(voz_txt, "para") * 0.9

    def fn(t):
        gt = g0 + t
        f = e2.fondo_papel(gt)
        tarjeta.dibujar(f, t, dur)
        e2.cabecera(f, t)
        placa(f, t, 0.3, alta=True, cy=1380)
        l1.draw(f, 1260, t, 0.45, paso=0.12)
        l2.draw(f, 1390, t, 0.45 + c2 * dur, paso=0.12)
        e2.dibujar_ticker(f, gt, prog(t, 0.2, 0.6))
        return f
    return fn


# ------------------------------------------------------------ línea de tiempo
def construir():
    cl = voz_tts.clip
    dur = lambda x: len(x) / SR
    escenas = []            # (duración, constructor(g0, dur) -> fn, [(offset local, audio)])
    n_sec = len(CATALOGO)
    for si, (_, tit, dicho, foto_animal, prods) in enumerate(CATALOGO):
        a = cl(dicho)
        d = max(2.5, 0.7 + dur(a) + TR - 0.05)
        escenas.append((d, (lambda g0, d_, r=foto_animal, t_=tit, i=si: escena_seccion(r, t_, i, g0, d_)),
                        [(0.7, a)], "seccion"))
        for pi, (tit_p, sub, dicho_p, foto) in enumerate(prods):
            c = cl(dicho_p)
            d = max(2.3, 0.6 + dur(c) + TR - 0.05)
            kick = "PARA " + CATALOGO[si][0].upper()
            escenas.append((d, (lambda g0, d_, r=foto, t_=tit_p, s_=sub, k=kick, ci=(pi + 1, len(prods)), v=VARIANTES[pi % 3], pj=pi:
                                e2.escena_producto(r, pj, t_, s_, d_, g0, v, e2.CAMARAS[(pj + si) % len(e2.CAMARAS)],
                                                   kicker_txt=k, cont=ci)),
                            [(0.6, c)], "producto"))
    t_ = cl(FRASE_TODO)
    d = max(3.4, 0.6 + dur(t_) + TR + 0.3)
    escenas.append((d, (lambda g0, d_: escena_todo(g0, d_, FRASE_TODO)), [(0.6, t_)], "todo"))
    v = cl(FRASE_VISITA)
    d = max(2.8, 0.6 + dur(v) + TR + 0.3)
    escenas.append((d, (lambda g0, d_: escena_visita(g0, d_, FRASE_VISITA)), [(0.6, v)], "visita"))

    # presentación aérea ("Somos Forralitas") con la misma lógica de tiempos que el video anterior
    s1, s2 = cl(FRASE_SOMOS), cl(FRASE_UBIC)
    s10 = 0.8
    s20 = s10 + dur(s1) + 0.25
    d_somos = s20 + dur(s2) + TR + 0.2
    e2.TM["b_pin"] = s20 - 0.35
    e2.TM["b_est"] = s20 - 0.05
    e2.TM["b_ruta"] = s20 + ev.frac(FRASE_UBIC, "ruta") * dur(s2) - 0.1
    e2.TM["b_tal"] = s20 + ev.frac(FRASE_UBIC, "Las Talitas") * dur(s2) - 0.1
    escenas.append((d_somos, (lambda g0, d_: e2.escena_dron("assets/dron/dron2.jpg", d_, g0, (60, 650, 960, 600),
                                                           (1.0, 1.75, (0.5, 0.5), (0.42, 0.58), 1.2, -0.8), None,
                                                           e2.decorado_b("Somos"))),
                    [(s10, s1), (s20, s2)], "somos"))

    # cierre con los datos
    cc = [(k, cl(t, rate=ev.RATE_RAPIDO.get(k))) for k, t in CIERRE]
    t_loc, cur = {}, 0.75
    for k, x in cc:
        t_loc[k] = cur
        cur += dur(x) + ev.GAP
    d_c = t_loc["firma"] + dur(cc[-1][1]) + 1.6
    cv.T_TEL, cv.T_HORA = t_loc["tel"] - 0.12, t_loc["hora"] - 0.12
    cv.T_UBIC = t_loc["hora"] + dur(dict(cc)["hora"]) - 0.1
    cv.T_ENVIO, cv.T_MAYOR, cv.T_PAGOS = t_loc["envio"] - 0.12, t_loc["mayor"] - 0.12, t_loc["pagos"] - 0.12
    cv.T_TIMBRE0, cv.PERIODO_TIMBRE = t_loc["tel"] + 0.2, 1.9
    pg, txt = dict(cc)["pagos"], dict(CIERRE)["pagos"]
    cv.T_CHIPS = tuple(t_loc["pagos"] + ev.frac(txt, w) * dur(pg) - 0.15
                       for w in ("efectivo", "transferencia", "débito", "crédito"))
    e2.TM["firma"] = t_loc["firma"] - 0.1
    escenas.append((d_c, (lambda g0, d_: e2.escena_cierre(g0)), [(t_loc[k], x) for k, x in cc], "cierre"))

    inicios, t = [], 0.0
    for d, *_ in escenas:
        inicios.append(t)
        t += d - TR
    total = inicios[-1] + escenas[-1][0]
    segs, voces, tipos = [], [], []
    for (d, ctor, vs, tipo), t0 in zip(escenas, inicios):
        segs.append((d, ctor(t0, d)))
        voces += [(t0 + off, x) for off, x in vs]
        tipos.append(tipo)
    return segs, inicios, total, voces, tipos


def transiciones(tipos):
    rot = [e2.tr_barras, e2.tr_persianas, e2.tr_rombo, e2.tr_reloj, e2.tr_empuje, e2.tr_circulo, e2.tr_zoom_desenfoque]
    out, k = [], 0
    for i in range(len(tipos) - 1):
        sig = tipos[i + 1]
        if sig in ("seccion", "cierre"):
            out.append(e2.tr_cortina)
        elif sig == "somos":
            out.append(e2.tr_zoom_desenfoque)
        else:
            out.append(rot[k % len(rot)])
            k += 1
    return out


def hacer_frame_fn(segs, inicios, total, tipos):
    trans = transiciones(tipos)
    fin_barra = inicios[-1]

    def make_frame(t):
        t = min(t, total - 1e-3)
        act = [i for i, (s, (d, _)) in enumerate(zip(inicios, segs)) if s <= t < s + d]
        if len(act) == 1:
            f = segs[act[0]][1](t - inicios[act[0]])
        else:
            a, b = act[0], act[-1]
            f = trans[a](segs[a][1](t - inicios[a]), segs[b][1](t - inicios[b]), (t - inicios[b]) / TR)
        if t < fin_barra + 0.2:
            f = np.ascontiguousarray(f)
            x0, x1, y = 60, W - 60, 58
            q = clamp01(t / fin_barra)
            ov = f.copy()
            cv2.line(ov, (x0, y), (x1, y), TIERRA, 8, cv2.LINE_AA)
            f = cv2.addWeighted(ov, 0.22, f, 0.78, 0)
            cv2.line(f, (x0, y), (int(x0 + (x1 - x0) * q), y), TRIGO, 8, cv2.LINE_AA)
        return f
    return make_frame


def main():
    segs, inicios, total, voces, tipos = construir()
    Path("videos_salida").mkdir(exist_ok=True)
    if "--frames" in sys.argv:
        mf = hacer_frame_fn(segs, inicios, total, tipos)
        for s in [float(x) for x in sys.argv[sys.argv.index("--frames") + 1:]]:
            Image.fromarray(mf(s)).save(f"videos_salida/prev_{s:05.1f}.png")
        print("duración total:", round(total, 2), "s | inicios:", [round(x, 1) for x in inicios])
        return
    audio_wav = ev.mezclar(total, inicios, voces)
    print("audio listo:", audio_wav, f"({total:.1f} s)")
    if "--audio" in sys.argv:
        return
    make_frame = hacer_frame_fn(segs, inicios, total, tipos)
    video = VideoClip(make_frame, duration=total).with_audio(AudioFileClip(audio_wav).subclipped(0, total))
    video.write_videofile(SALIDA, fps=FPS, codec="libx264", audio_codec="aac", audio_bitrate="192k", preset="medium",
                          ffmpeg_params=["-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart"])
    print("Listo:", SALIDA, f"({total:.1f} s)")


if __name__ == "__main__":
    main()
