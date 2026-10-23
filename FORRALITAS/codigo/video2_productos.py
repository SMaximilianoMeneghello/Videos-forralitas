"""VIDEO 2 — PRODUCTOS ESTRELLA ("La calidad comienza con una buena alimentación").
Dirección de arte: cálido y enérgico (trigo, crema y verde), fotos a pantalla completa, pulsos al ritmo y cortes rápidos.
Uso (desde la raíz del repositorio):
    python FORRALITAS/codigo/video2_productos.py [--frames t1 t2 ...]
"""
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import base  # noqa: E402
import elementos as el  # noqa: E402
import motor as m  # noqa: E402
from motor import W, H, prog, clamp01, ease_out_cubic, ease_out_back, ease_in_out, ease_out_expo  # noqa: E402

NOMBRE = "FORRALITAS_PRODUCTOS"
BPM = 126
D = m.datos()
CREMA, ORO, VERDE, VERDE_OSC = m.CREMA, m.ORO, m.VERDE, m.VERDE_OSC


def pulso(t, beat, k=0.05, caida=8.0):
    """Golpe de zoom al compás: 1 + k justo en el beat, vuelve suave."""
    return 1 + k * np.exp(-(t % beat) * caida)


def foto_pantalla(nombre, t, dur, a, b, z0=1.0, z1=1.3, rot=0.0, beat=None, k=0.045, oscuro=0.72):
    cx, cy, z = m.camara(prog(t, 0, dur), z0, z1, a, b, ease=lambda x: x)
    f = m.Foto(nombre).ventana(W, H, cx, cy, z, rot)
    if beat:
        s = pulso(t, beat, k)
        y0, x0 = int((H * s - H) / 2), int((W * s - W) / 2)
        f = np.ascontiguousarray(cv2.resize(f, None, fx=s, fy=s)[y0:y0 + H, x0:x0 + W])
    return (f.astype(np.float32) * oscuro).astype(np.uint8) if oscuro < 1 else f


def degradado_abajo(f, alto=760, op=0.78, color=VERDE_OSC):
    y0 = H - alto
    mk = (np.linspace(0, 1, alto, dtype=np.float32) ** 1.6 * op)[:, None, None]
    f[y0:] = (f[y0:] * (1 - mk) + np.array(color, np.float32) * mk).astype(np.uint8)


def losa(f, cx, cy, w, h, ang, color=ORO, alpha=1.0):
    """Losa de color rotada (recurso gráfico diagonal)."""
    ov = f.copy()
    a = np.radians(ang)
    c, s = np.cos(a), np.sin(a)
    pts = np.array([[(-w / 2) * c - (-h / 2) * s + cx, (-w / 2) * s + (-h / 2) * c + cy],
                    [(w / 2) * c - (-h / 2) * s + cx, (w / 2) * s + (-h / 2) * c + cy],
                    [(w / 2) * c - (h / 2) * s + cx, (w / 2) * s + (h / 2) * c + cy],
                    [(-w / 2) * c - (h / 2) * s + cx, (-w / 2) * s + (h / 2) * c + cy]], np.int32)
    cv2.fillPoly(ov, [pts], color, cv2.LINE_AA)
    cv2.addWeighted(ov, alpha, f, 1 - alpha, 0, f)


# ------------------------------------------------------------------ A. GANCHO (0-4 s)
def esc_gancho(info):
    l1 = m.Cinetico("¡DALE A TUS ANIMALES", 84, 1000, m.NEGRA, m.BLANCO, VERDE_OSC, ORO, trazo=8, interlinea=1.05)
    l2 = m.Cinetico("LA *ALIMENTACIÓN*", 92, 1000, m.NEGRA, m.BLANCO, VERDE_OSC, ORO, trazo=8)
    l3 = m.Cinetico("QUE NECESITAN!", 92, 1000, m.NEGRA, m.ORO_CLARO, VERDE_OSC, ORO, trazo=8)
    info.sfx += [(0.0, "impacto", 1.0), (0.2, "golpe", 0.7), (0.62, "tick", 0.8), (1.25, "tick", 0.8), (1.9, "golpe", 0.8)]

    def fn(t):
        f = foto_pantalla("alfalfa", t, info.dur, (0.5, 0.62), (0.52, 0.4), 1.0, 1.45, 0, info.beat, 0.05, 0.7)
        degradado_abajo(f, 1100, 0.5)
        m.particulas(f, t, 9, n=26, tam=(5, 16), vel=(80, 190), intensidad=0.75)
        losa(f, W / 2, 860, 1500, 360 * ease_out_expo(prog(t, 0.0, 0.5)), -7, VERDE_OSC, 0.7)
        l1.draw(f, 650, t, 0.12, paso=0.09, desde="izq")
        l2.draw(f, 760, t, 0.55, paso=0.13, desde="der")
        l3.draw(f, 905, t, 1.3, paso=0.1, desde="abajo")
        m.barrido_luz(f, prog(t, 1.4, 0.9), 280, -18, 0.45, (0, 560, W, 1080))
        return f
    return fn


# ------------------------------------------------------------------ B. MAÍZ
def esc_maiz(info):
    word = m.Letras("MAÍZ", 330, m.NEGRA, ORO, trazo=10)
    sub = el.pastilla("Consultá presentaciones y precios", 44, CREMA, VERDE_OSC, m.EXTRA)
    info.sfx += [(0.0, "golpe", 1.0), (0.25, "pop", 0.8), (0.5, "tick", 0.7), (1.1, "brillo", 0.5), (1.9, "pop", 0.7)]

    def fn(t):
        f = foto_pantalla("maiz_entero", t, info.dur, (0.35, 0.7), (0.62, 0.3), 1.0, 1.5, 0, info.beat, 0.06, 0.78)
        degradado_abajo(f, 900, 0.7)
        # grano dorado flotando al frente (parallax: se mueve más rápido que el fondo)
        m.particulas(f, t * 1.8, 31, n=34, tam=(6, 20), vel=(110, 260), intensidad=0.8, color=m.ORO_CLARO)
        # barra diagonal que detrás de la palabra "sale" desde la izquierda
        losa(f, W / 2 - (1 - ease_out_expo(prog(t, 0.05, 0.5))) * 1400, 690, 1400, 300, -6, VERDE_OSC, 0.82)
        word.draw(f, W / 2, 690, t, 0.1, paso=0.07, caida=260, escala0=2.0)
        m.barrido_luz(f, prog(t, 1.0, 0.9), 300, -18, 0.55, (40, 520, W - 40, 860))
        q = prog(t, 0.95, 0.5)
        m.blit(f, sub, W / 2, 1010 + (1 - ease_out_cubic(q)) * 60, alpha=ease_out_cubic(q * 2), centro=True,
               escala=0.85 + 0.15 * ease_out_back(q, 1.7))
        return f
    return fn


# ------------------------------------------------------------------ C. ALFALFA (revelado por máscara diagonal)
def esc_alfalfa(info):
    word = m.Letras("ALFALFA", 184, m.NEGRA, CREMA, trazo=10)
    sub = el.pastilla("Consultá por disponibilidad", 44, ORO, VERDE_OSC, m.EXTRA)
    info.sfx += [(0.0, "whoosh_corto", 0.9), (0.35, "golpe", 1.0), (0.7, "pop", 0.8), (1.2, "brillo", 0.5)]

    def fn(t):
        f = foto_pantalla("alfalfa_fardos", t, info.dur, (0.35, 0.55), (0.62, 0.4), 1.05, 1.5, -1.0 + 2 * prog(t, 0, info.dur), info.beat, 0.05, 0.8)
        # fondo previo (crema) que la foto "corta" en diagonal
        base_ = np.zeros_like(f)
        base_[:] = CREMA
        d = (np.arange(W, dtype=np.float32)[None, :] * 0.5 + np.arange(H, dtype=np.float32)[:, None] * 0.866) / (W * 0.5 + H * 0.866)
        borde = ease_out_expo(prog(t, 0.0, 0.55)) * 1.4 - 0.2
        mk = (d < borde)[..., None]
        out = np.where(mk, f, base_)
        banda = (d >= borde) & (d < borde + 0.05)
        out[banda] = ORO
        degradado_abajo(out, 860, 0.66)
        m.particulas(out, t * 1.5, 41, n=26, tam=(5, 14), vel=(70, 170), intensidad=0.6, color=(190, 235, 150))
        losa(out, W / 2, 690, 1500, 290 * ease_out_expo(prog(t, 0.4, 0.4)), 5, VERDE_OSC, 0.86)
        word.draw(out, W / 2, 690, t, 0.45, paso=0.07, caida=200, escala0=1.8)
        m.barrido_luz(out, prog(t, 1.2, 0.9), 300, -18, 0.55, (40, 520, W - 40, 860))
        q = prog(t, 1.0, 0.5)
        m.blit(out, sub, W / 2, 1010 + (1 - ease_out_cubic(q)) * 60, alpha=ease_out_cubic(q * 2), centro=True,
               escala=0.85 + 0.15 * ease_out_back(q, 1.7))
        return out
    return fn


# ------------------------------------------------------------------ D. COMPLEMENTARIOS (cada uno con su plano)
COMP = [("PELLET DE TRIGO", "pellet_trigo", (0.3, 0.4), (0.7, 0.6), -4),
        ("MEZCLAS PARA CABALLOS", "mezcla_caballo", (0.6, 0.7), (0.4, 0.3), 3),
        ("AFRECHO", "afrecho_maiz", (0.7, 0.4), (0.3, 0.6), -3),
        ("PELLET DE ALFA", "pellet_alfa", (0.4, 0.7), (0.6, 0.3), 4)]


def esc_comp(info):
    n = len(COMP)
    seg = info.dur / n
    tags = [m.Cinetico(nm, 86 if len(nm) < 14 else 70, 980, m.NEGRA, VERDE_OSC, VERDE_OSC, ORO, interlinea=1.05) for nm, *_ in COMP]
    for i in range(n):
        info.sfx += [(i * seg + 0.02, "whoosh_corto", 0.8), (i * seg + 0.1, "golpe", 0.8), (i * seg + 0.28, "pop", 0.7)]

    def fn(t):
        i = min(int(t / seg), n - 1)
        tl = t - i * seg
        nm, foto, a, b, ang = COMP[i]
        f = foto_pantalla(foto, tl, seg + 0.5, a, b, 1.0, 1.38, 0, info.beat, 0.05, 0.8)
        degradado_abajo(f, 820, 0.62)
        m.particulas(f, t, 50 + i, n=20, tam=(5, 13), vel=(60, 150), intensidad=0.55)
        # número grande y etiqueta sobre losa dorada inclinada
        q = ease_out_back(prog(tl, 0.05, 0.5), 1.5)
        losa(f, W / 2 + (1 - q) * 1300, 1090, 1240, 210, ang, ORO, 1.0)
        losa(f, W / 2 + (1 - q) * 1300 + 12, 1108, 1240, 210, ang, VERDE_OSC, 0.45)
        tags[i].draw(f, 1045 if len(nm) < 14 else 1055, tl, 0.18, paso=0.07, desde="der")
        num = m.spr_texto(f"0{i + 1}", 150, ORO, m.NEGRA, 8, VERDE_OSC, True)
        m.blit(f, num, 170, 430, alpha=clamp01(q * 2), escala=0.7 + 0.3 * q, centro=True)
        m.blit(f, m.spr_texto(f"/ 0{n}", 52, m.CREMA, m.EXTRA, 5, VERDE_OSC, True), 330, 470, alpha=clamp01(q * 2), centro=True)
        m.barrido_luz(f, prog(tl, 0.3, 0.7), 240, -18, 0.4, (60, 930, W - 60, 1250))
        return f
    return fn


# ------------------------------------------------------------------ E. MONTAJE "VARIEDAD, CALIDAD Y ATENCIÓN"
MONT = ["maiz_entero", "alfalfa", "pellet_trigo", "perros_gatos", "mezcla_caballo", "ponedora",
        "afrecho_maiz", "perros_sabrositos", "cerdo_mezcla", "sal", "pellet_alfa", "virutas"]


def esc_montaje(info):
    banda1 = m.Cinetico("VARIEDAD,", 124, 1000, m.NEGRA, m.BLANCO, VERDE_OSC, ORO, trazo=9)
    banda2 = m.Cinetico("*CALIDAD*", 144, 1000, m.NEGRA, m.BLANCO, VERDE_OSC, ORO, trazo=0)
    banda3 = m.Cinetico("Y ATENCIÓN", 124, 1000, m.NEGRA, m.BLANCO, VERDE_OSC, ORO, trazo=9)
    tambien = el.pastilla("También: avena · expeller de soja · polenta · legumbres", 33, VERDE_OSC, CREMA, m.EXTRA, 30, 12)
    n = len(MONT)
    paso = info.beat / 2
    info.sfx += [(k * paso, "tick", 0.55) for k in range(n)] + [(0.0, "golpe", 1.0), (info.beat * 2, "brillo", 0.6)]
    cols, filas = 3, 4
    tw, th = 340, 340

    def fn(t):
        f = np.zeros((H, W, 3), np.uint8)
        f[:] = VERDE_OSC
        for k, nom in enumerate(MONT):
            r, c = divmod(k, cols)
            tt = t - k * paso
            if tt < 0:
                continue
            q = ease_out_back(prog(tt, 0, 0.32), 1.6)
            cx = 60 + tw / 2 + c * (tw + 10) + 4
            cy = 150 + th / 2 + r * (th + 10)
            img = m.Foto(nom).ventana(tw, th, 0.5, 0.5, 1.0 + 0.2 * prog(t, 0, info.dur), 0)
            m.poner_tarjeta(f, img, cx, cy, 0.7 + 0.3 * q, (1 - q) * 14, clamp01(q * 3), r=26, borde=6, sombra=False)
        ov = f.copy()
        losa(ov, W / 2, 790, 1500, 560 * ease_out_expo(prog(t, 0.2, 0.5)), -5, VERDE_OSC, 1.0)
        cv2.addWeighted(ov, 0.82, f, 0.18, 0, f)
        banda1.draw(f, 590, t, 0.3, paso=0.1, desde="izq")
        banda2.draw(f, 735, t, info.beat * 1.0, paso=0.1, desde="der")
        banda3.draw(f, 905, t, info.beat * 2.0, paso=0.1, desde="izq")
        q = prog(t, info.beat * 3, 0.4)
        m.blit(f, tambien, W / 2, 1120, alpha=ease_out_cubic(q), centro=True, escala=0.9 + 0.1 * ease_out_back(q, 1.4))
        m.barrido_luz(f, prog(t, info.beat * 2.5, 0.9), 260, -18, 0.4, (40, 560, W - 40, 1010))
        return f
    return fn


# ------------------------------------------------------------------ F. CIERRE ("ticket" con todos los datos)
def esc_cierre(info):
    lg = el.logo(380)
    marca = m.Cinetico("*FORRALITAS*", 120, 1000, m.NEGRA, VERDE_OSC, VERDE_OSC, ORO)
    slogan = m.Cinetico("Alimentos de calidad para cada animal", 44, 1000, m.SEMI, VERDE_OSC, VERDE_OSC, ORO)
    cta = el.pastilla("Consultá por nuestros productos", 44, VERDE_OSC, CREMA, m.NEGRA)
    ciudad = m.spr_texto("Las Talitas, Tucumán", 48, VERDE, m.EXTRA, 0, CREMA, False)
    filas = [
        (el.tarjeta_dato("telefono", tuple(D["tel"]), 980, 150, VERDE_OSC, CREMA, m.ORO_CLARO, 46), 2.6),
        (el.tarjeta_dato("reloj", tuple(D["horario"]), 980, 130, VERDE_OSC, CREMA, m.ORO_CLARO, 38), 3.4),
        (el.tarjeta_dato("ubicacion", ("Ruta 305 km 7,5 · Las Talitas", "Envíos según la zona · Venta por mayor y menor"), 980, 130, VERDE_OSC, CREMA, m.ORO_CLARO, 38), 4.2),
    ]
    pagos = [("efectivo", "Efectivo"), ("transferencia", "Transferencia"), ("debito", "Débito"), ("credito", "Crédito")]
    chips = [el.chip(i, n, None, 76, VERDE_OSC, CREMA, 30) for i, n in pagos]
    gap_c = (980 - sum(c.shape[1] for c in chips)) / 3
    info.sfx += [(0.05, "impacto", 1.0), (0.4, "brillo", 0.8), (2.6, "pop", 0.8), (3.4, "pop", 0.8), (4.2, "pop", 0.8), (5.0, "pop", 0.8), (6.0, "campana", 0.8)]

    def fn(t):
        f = np.zeros((H, W, 3), np.uint8)
        f[:] = CREMA
        losa(f, W / 2, 230, 1800, 520, -8, ORO, 1.0)
        losa(f, W / 2 + 40, 560, 1800, 70, -8, VERDE, 1.0)
        ov = f.copy()
        m.particulas(ov, t, 61, n=22, tam=(5, 13), vel=(30, 90), intensidad=0.4, color=ORO)
        f = ov
        q = prog(t, 0.0, 0.55)
        s = 3.2 - 2.2 * ease_out_expo(q)
        sh = 1 + 0.18 * np.exp(-max(t - 0.5, 0) * 6) * np.sin(max(t - 0.5, 0) * 26)
        m.blit(f, lg, W / 2, 330, alpha=clamp01(q * 4), escala=s * sh, centro=True)
        el.anillo(f, W / 2, 330, 212, ease_out_cubic(prog(t, 0.4, 0.9)), VERDE_OSC, 8, giro=-90 + 20 * t)
        marca.draw(f, 620, t, 0.6, paso=0.07)
        slogan.draw(f, 760, t, 1.2, paso=0.07)
        m.blit(f, ciudad, W / 2, 850, alpha=ease_out_cubic(prog(t, 1.7, 0.5)), centro=True)
        m.blit(f, cta, W / 2, 940, alpha=ease_out_cubic(prog(t, 2.0, 0.4)),
               escala=(0.85 + 0.15 * ease_out_back(prog(t, 2.0, 0.4), 1.6)) * (1 + 0.025 * np.sin(t * 6)), centro=True)
        y = 1030
        for spr, t0 in filas:
            qq = prog(t, t0, 0.5)
            m.blit(f, spr, W / 2, y + spr.shape[0] / 2 + (1 - ease_out_expo(qq)) * 500, alpha=clamp01(qq * 3), centro=True)
            y += spr.shape[0] + 14
        xc = 50.0
        for i, c in enumerate(chips):
            qq = prog(t, 5.0 + i * 0.12, 0.4)
            m.blit(f, c, xc + c.shape[1] / 2, y + 40, alpha=clamp01(qq * 3), escala=0.7 + 0.3 * ease_out_back(qq, 1.8), centro=True)
            xc += c.shape[1] + gap_c
        return f
    return fn


GUION = [
    dict(nombre="gancho", min_beats=8, hold=0.4, voz=[("¡Dale a tus animales la alimentación que necesitan!", 0.1)], fabrica=esc_gancho, impacto="impacto"),
    dict(nombre="maiz", min_beats=12, hold=0.3, voz=[("Maíz.", 0.35), ("Consultá presentaciones y precios.", 0.5)], fabrica=esc_maiz),
    dict(nombre="alfalfa", min_beats=12, hold=0.3, voz=[("Alfalfa.", 0.35), ("Consultá por disponibilidad.", 0.5)], fabrica=esc_alfalfa),
    dict(nombre="complementarios", min_beats=18, hold=0.2, voz=[("Pellet de trigo, mezclas para caballos, afrecho y pellet de alfa.", 0.35)], fabrica=esc_comp),
    dict(nombre="montaje", min_beats=8, hold=0.4, voz=[("Variedad, calidad y atención.", 0.2)], fabrica=esc_montaje),
    dict(nombre="cierre", min_beats=22, hold=1.3,
         voz=[("Forralitas. Consultá por nuestros productos.", 0.45),
              ("Llamanos al tres ocho uno, seis tres tres, cuatro tres cuatro cuatro.", 0.12),
              ("Lunes a sábado. Aceptamos todos los medios de pago.", 0.12)],
         fabrica=esc_cierre, impacto="impacto"),
]


def main():
    plan, beat, total = base.planificar(BPM, GUION, ritmo=0.88)
    print("duración", round(total, 2), "s | escenas:", [(e["nombre"], round(e["dur"], 2)) for e in plan])
    trans = [lambda a, b, p: m.tr_whip(a, b, p, "izq"),
             lambda a, b, p: m.tr_diagonal(a, b, p, ORO, VERDE_OSC),
             lambda a, b, p: m.tr_whip(a, b, p, "arriba"),
             lambda a, b, p: m.tr_flash(a, b, p),
             lambda a, b, p: m.tr_persianas(a, b, p)]
    tl = base.construir_linea(plan, trans)
    pal = base.palabras_globales(plan)
    subs = m.Subtitulos(pal, y=1500, activo=m.ORO_CLARO)
    c = plan[-1]
    sin_subs = [(c["ini"] + 0.3, total + 1)] + [(plan[i]["ini"] + 0.1, plan[i]["ini"] + plan[i]["dur"] + 0.2) for i in (1, 2)]
    if "--frames" in sys.argv:
        ts = [float(x) for x in sys.argv[sys.argv.index("--frames") + 1:]]
        base.vista_previa(tl, subs, sin_subs, ts, str(base.SALIDA / "miniaturas/_prev_v2"), grado="vivo")
        return
    wav = base.audio(plan, total, "energico", BPM, NOMBRE)
    salida = base.SALIDA / f"videos/{NOMBRE}.mp4"
    base.renderizar(tl, subs, sin_subs, total, wav, salida, grado="vivo")
    print("listo", salida)


if __name__ == "__main__":
    main()
