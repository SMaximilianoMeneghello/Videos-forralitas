"""VIDEO 3 — PUBLICIDAD DE VENTA DIRECTA ("¿Necesitás abastecerte? En FORRALITAS te esperamos").
Dirección de arte: crema y verde con losas diagonales, tarjetas con rebote, categorías por animal y llamada a la acción fuerte.
Uso (desde la raíz del repositorio):
    python FORRALITAS/codigo/video3_publicidad.py [--frames t1 t2 ...]
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
from video2_productos import degradado_abajo, foto_pantalla, losa  # noqa: E402

NOMBRE = "FORRALITAS_PUBLICIDAD"
BPM = 110
D = m.datos()
CREMA, ORO, VERDE, VERDE_OSC, VERDE_MED = m.CREMA, m.ORO, m.VERDE, m.VERDE_OSC, m.VERDE_MED


def fondo_crema(t, semilla=3):
    f = np.zeros((H, W, 3), np.uint8)
    f[:] = CREMA
    # franjas diagonales muy suaves que se desplazan
    d = ((np.arange(W, dtype=np.float32)[None, :] * 0.5 + np.arange(H, dtype=np.float32)[:, None] * 0.866) / 160.0 - t * 0.35) % 2.0
    sombra = (d < 1.0).astype(np.float32)[..., None] * 9
    f = np.clip(f.astype(np.float32) - sombra, 0, 255).astype(np.uint8)
    m.particulas(f, t, semilla, n=18, tam=(5, 12), vel=(20, 60), intensidad=0.32, color=ORO, desenfoque=True)
    return f


# ------------------------------------------------------------------ A. GANCHO
def esc_gancho(info):
    l1 = m.Cinetico("¿TENÉS QUE", 104, 1000, m.NEGRA, m.BLANCO, VERDE_OSC, ORO, trazo=8)
    l2 = m.Letras("COMPRAR", 188, m.NEGRA, m.ORO_CLARO, trazo=10)
    l3 = m.Letras("ALIMENTO?", 160, m.NEGRA, m.BLANCO, trazo=9)
    info.sfx += [(0.0, "impacto", 1.0), (0.3, "golpe", 0.8), (0.75, "golpe", 0.9), (1.2, "golpe", 0.9), (1.6, "subida", 0.5)]

    def fn(t):
        sk = np.exp(-(t % info.beat) * 9) * 7
        f = foto_pantalla("perros_gatos", t, info.dur, (0.25, 0.5), (0.75, 0.5), 1.15, 1.55, 0, info.beat, 0.06, 0.55)
        if t < 1.7:                                      # tembleque corto con cada golpe
            M = np.float32([[1, 0, sk * np.sin(t * 90)], [0, 1, sk * np.cos(t * 70)]])
            f = cv2.warpAffine(f, M, (W, H), borderMode=cv2.BORDER_REFLECT)
        m.particulas(f, t, 70, n=22, tam=(5, 14), vel=(80, 200), intensidad=0.7)
        losa(f, W / 2, 800, 1600, 780 * ease_out_expo(prog(t, 0.0, 0.45)), -6, VERDE_OSC, 0.86)
        l1.draw(f, 505, t, 0.12, paso=0.1, desde="izq")
        l2.draw(f, W / 2, 780, t, 0.45, paso=0.06, caida=260, escala0=2.0)
        l3.draw(f, W / 2, 960, t, 0.95, paso=0.055, caida=220, escala0=1.8)
        m.barrido_luz(f, prog(t, 1.2, 0.9), 280, -18, 0.45, (0, 480, W, 1100))
        return f
    return fn


# ------------------------------------------------------------------ B. VARIOS PRODUCTOS
TILES = [("MAÍZ", "maiz_entero"), ("ALFALFA", "alfalfa"), ("PELLET DE TRIGO", "pellet_trigo"),
         ("MEZCLA PARA CABALLOS", "mezcla_caballo"), ("PONEDORA", "ponedora"), ("BALANCEADOS", "perros_sabrositos")]


def esc_varios(info):
    tw, th = 480, 360
    xs = (292, 788)
    ys = (505, 880, 1255)
    tags = [el.pastilla(nm, 30 if len(nm) < 17 else 27, VERDE_OSC, CREMA, m.EXTRA, 22, 10) for nm, _ in TILES]
    cab = m.Cinetico("*OPCIONES* PARA TODOS", 62, 1000, m.NEGRA, VERDE_OSC, VERDE_OSC, ORO)
    paso = info.beat * 0.75
    for k in range(len(TILES)):
        info.sfx += [(0.3 + k * paso, "pop", 0.85), (0.3 + k * paso + 0.02, "tick", 0.7)]

    def fn(t):
        f = fondo_crema(t, 5)
        cab.draw(f, 205, t, 0.05, paso=0.08, desde="der")
        for k, (nm, foto) in enumerate(TILES):
            r, c = divmod(k, 2)
            tt = t - (0.3 + k * paso)
            if tt < 0:
                continue
            q = ease_out_back(prog(tt, 0, 0.5), 1.7)
            cx, cy = xs[c], ys[r] - (1 - q) * 900
            rot = (-3 if (r + c) % 2 == 0 else 3) * (0.5 + 0.5 * np.sin(t * 1.1 + k)) + (1 - q) * (12 if c else -12)
            img = m.Foto(foto).ventana(tw, th, 0.5, 0.5, 1.08 + 0.06 * prog(tt, 0, 3), 0)
            m.poner_tarjeta(f, img, cx, cy, 1.0, rot, 1.0, r=30, borde=8)
            qt = ease_out_back(prog(tt, 0.35, 0.4), 1.8)
            m.blit(f, tags[k], cx, cy + th / 2 - 8, alpha=clamp01(qt * 2.5), escala=0.6 + 0.4 * qt, centro=True)
        return f
    return fn


# ------------------------------------------------------------------ C. CATEGORÍAS
CATS = [("CABALLOS", "mezcla_caballo2", VERDE, CREMA, ORO), ("GALLINAS", "ponedora", ORO, VERDE_OSC, VERDE_OSC),
        ("CERDOS", "cerdo_mezcla", VERDE_MED, CREMA, ORO), ("PERROS Y GATOS", "perros_gatos", ORO, VERDE_OSC, VERDE_OSC)]


def esc_categorias(info):
    ini = [v[0] - 0.2 for v in info.voces]
    ini[0] = 0.0
    fin = ini[1:] + [info.dur + 1]
    kick = [el.pastilla("PARA", 54, c[4] if c[4] != c[2] else CREMA, c[2] if c[4] != c[2] else VERDE_OSC, m.NEGRA, 40, 14) for c in CATS]
    tit = [m.Letras(c[0], 150 if len(c[0]) < 10 else 112, m.NEGRA, c[3], trazo=0) for c in CATS]
    for i in range(len(CATS)):
        info.sfx += [(ini[i] + 0.02, "whoosh_corto", 0.8), (ini[i] + 0.15, "golpe", 0.9), (ini[i] + 0.4, "pop", 0.7)]

    def fn(t):
        i = max(k for k in range(len(CATS)) if t >= ini[k] - 0.05)
        nm, foto, bg, tc, ac = CATS[i]
        tl = t - ini[i]
        f = np.zeros((H, W, 3), np.uint8)
        f[:] = bg
        # losa diagonal de color que "barre" el fondo al cambiar de categoría
        if i > 0:
            prev = CATS[i - 1][2]
            losa(f, W / 2 - ease_out_expo(prog(tl, 0, 0.45)) * 2200 + 1100, H / 2, 2400, 2600, 14, prev, 1.0)
        d = ((np.arange(W, dtype=np.float32)[None, :] * 0.5 + np.arange(H, dtype=np.float32)[:, None] * 0.866) / 200.0 - t * 0.5) % 2.0
        f = np.clip(f.astype(np.float32) + (d < 1.0).astype(np.float32)[..., None] * 10, 0, 255).astype(np.uint8)
        m.particulas(f, t, 80 + i, n=20, tam=(5, 13), vel=(30, 90), intensidad=0.4, color=m.ORO_CLARO)
        q = ease_out_back(prog(tl, 0.05, 0.6), 1.3)
        sal = ease_in_out(prog(t - fin[i], 0, 0.3))
        dirx = -1 if i % 2 == 0 else 1
        cx = W / 2 + dirx * (1 - q) * 1300 - dirx * sal * 400
        cy = 700 + 14 * np.sin(t * 1.4 + i)
        cam = m.camara(prog(tl, 0, fin[i] - ini[i] + 0.3), 1.0, 1.3, (0.4, 0.55), (0.62, 0.42))
        img = m.Foto(foto).ventana(900, 880, cam[0], cam[1], cam[2], 0)
        m.poner_tarjeta(f, img, cx, cy, 1.0, dirx * (1 - q) * 9 + 1.6 * np.sin(t * 1.2 + i), 1.0, r=44, borde=11)
        m.barrido_luz(f, prog(tl, 0.4, 0.7), 220, -18, 0.35, (80, 280, 1000, 1120))
        # etiqueta
        kq = ease_out_back(prog(tl, 0.2, 0.45), 1.7)
        m.blit(f, kick[i], 250, 1180 + (1 - kq) * 80, alpha=clamp01(kq * 2), escala=0.7 + 0.3 * kq, centro=True)
        tit[i].draw(f, W / 2, 1320, tl, 0.28, paso=0.055, caida=140, escala0=1.5)
        # contador de categorías (puntos)
        for k in range(len(CATS)):
            cv2.circle(f, (int(W / 2 + (k - 1.5) * 52), 1210 + 0), 10 if k != i else 16, tc if k == i else (tc if False else ac), -1 if k == i else 3, cv2.LINE_AA)
        return f
    return fn


# ------------------------------------------------------------------ D. UBICACIÓN + VARIEDAD
def esc_ubicacion(info):
    tit = m.Cinetico("*LAS* *TALITAS,* TUCUMÁN", 82, 1000, m.NEGRA, VERDE_OSC, VERDE_OSC, ORO)
    ruta = el.pastilla("Ruta 305 km 7,5", 46, VERDE_OSC, CREMA, m.EXTRA)
    marq = ["maiz_entero", "alfalfa", "pellet_trigo", "mezcla_caballo", "ponedora", "perros_sabrositos", "cerdo_mezcla", "afrecho_maiz", "sal"]
    info.sfx += [(0.2, "pop", 0.8), (0.95, "golpe", 0.9), (1.0, "pop", 0.8), (1.6, "brillo", 0.5)]

    def pin(f, cx, cy, esc, alpha):
        ov = f.copy()
        cv2.circle(ov, (int(cx), int(cy - 70 * esc)), int(42 * esc), VERDE_OSC, -1, cv2.LINE_AA)
        pts = np.array([[cx - 36 * esc, cy - 50 * esc], [cx + 36 * esc, cy - 50 * esc], [cx, cy]], np.int32)
        cv2.fillPoly(ov, [pts], VERDE_OSC, cv2.LINE_AA)
        cv2.circle(ov, (int(cx), int(cy - 70 * esc)), int(17 * esc), ORO, -1, cv2.LINE_AA)
        cv2.addWeighted(ov, alpha, f, 1 - alpha, 0, f)

    def fn(t):
        f = fondo_crema(t, 9)
        losa(f, W / 2, 140, 1800, 250, -3, VERDE, 1.0)
        tit.draw(f, 330, t, 0.1, paso=0.09)
        # foto aérea del lugar como tarjeta (sin ampliar más de 1:1)
        q = ease_out_back(prog(t, 0.15, 0.6), 1.2)
        cam = m.camara(prog(t, 0, info.dur), 1.0, 1.12, (0.5, 0.5), (0.55, 0.5))
        img = m.Foto("dron_2").ventana(1000, 538, cam[0], cam[1], cam[2], 0)
        m.poner_tarjeta(f, img, W / 2, 790 + (1 - q) * 600, 1.0, -1.5 * q, clamp01(q * 2), r=36, borde=10)
        # pin que cae sobre el lugar y rebota
        pq = prog(t, 0.9, 0.55)
        py = 800 - (1 - ease_out_back(pq, 2.4)) * 420
        pin(f, 560, py, 1.15, clamp01(pq * 3))
        if 0.9 < t < 1.9:
            r = int(160 * prog(t, 1.4, 0.5))
            if r > 2:
                cv2.circle(f, (560, 800), r, ORO, 5, cv2.LINE_AA)
        qr = prog(t, 1.2, 0.45)
        m.blit(f, ruta, W / 2, 1115, alpha=ease_out_cubic(qr * 2), escala=0.85 + 0.15 * ease_out_back(qr, 1.6), centro=True)
        # cinta de productos que se desplaza (variedad)
        off = (t * 210) % (len(marq) * 250)
        for k in range(len(marq) + 5):
            x = k * 250 - off
            nom = marq[k % len(marq)]
            img2 = m.Foto(nom).ventana(230, 230, 0.5, 0.5, 1.0, 0)
            if -250 < x < W + 20:
                m.poner_tarjeta(f, img2, x + 115, 1310, 1.0, 0, 1.0, r=26, borde=6, sombra=False)
        return f
    return fn


# ------------------------------------------------------------------ E. CIERRE: ¡HACÉ TU CONSULTA!
def esc_cierre(info):
    lg = el.logo(270)
    l1 = m.Letras("¡HACÉ TU", 128, m.NEGRA, m.BLANCO, trazo=0)
    l2 = m.Letras("CONSULTA!", 168, m.NEGRA, m.ORO_CLARO, trazo=0)
    marca = m.Cinetico("*FORRALITAS*", 92, 1000, m.NEGRA, m.BLANCO, VERDE_OSC, ORO)
    slogan = m.Cinetico("Alimentos de calidad para cada animal", 40, 1000, m.SEMI, m.CREMA, VERDE_OSC, ORO)
    filas = [
        (el.tarjeta_dato("telefono", tuple(D["tel"]), 980, 150, CREMA, VERDE_OSC, VERDE, 46, 0.97, 34, VERDE_OSC, ORO), 3.4),
        (el.tarjeta_dato("reloj", tuple(D["horario"]), 980, 130, CREMA, VERDE_OSC, VERDE, 38, 0.97, 34, VERDE_OSC, ORO), 4.1),
        (el.tarjeta_dato("ubicacion", ("Ruta 305 km 7,5 · Las Talitas, Tucumán", "Envíos según la zona · Venta por mayor y menor"), 980, 130, CREMA, VERDE_OSC, VERDE, 36, 0.97, 34, VERDE_OSC, ORO), 4.8),
    ]
    pagos = [("efectivo", "Efectivo"), ("transferencia", "Transferencia"), ("debito", "Débito"), ("credito", "Crédito")]
    chips = [el.chip(i, n, None, 76, CREMA, VERDE_OSC, 30) for i, n in pagos]
    gap_c = (980 - sum(c.shape[1] for c in chips)) / 3
    info.sfx += [(0.0, "impacto", 1.0), (0.3, "golpe", 0.9), (0.7, "golpe", 0.9), (1.9, "brillo", 0.8), (3.4, "pop", 0.8), (4.1, "pop", 0.8),
                 (4.8, "pop", 0.8), (5.5, "pop", 0.8), (info.dur - 3.2, "campana", 0.9), (info.dur - 3.2, "impacto", 0.7)]

    def fn(t):
        f = m.degradado(VERDE_MED, VERDE_OSC, 0.5, 0.2, 0.9)
        losa(f, W / 2, 1450, 2000, 260, -6, ORO, 0.12)
        m.particulas(f, t, 90, n=26, tam=(4, 12), vel=(40, 110), intensidad=0.5)
        sk = np.exp(-max(t - 0.0, 0) * 8) * 6
        l1.draw(f, W / 2, 305 + sk * np.sin(t * 80), t, 0.05, paso=0.05, caida=200, escala0=1.8)
        l2.draw(f, W / 2, 470 + sk * np.cos(t * 70), t, 0.45, paso=0.05, caida=240, escala0=1.9)
        m.barrido_luz(f, prog(t, 1.0, 0.9), 260, -18, 0.45, (0, 180, W, 540))
        pulso = 1 + 0.03 * np.sin(t * 6)
        q = prog(t, 1.9, 0.6)
        s = 2.2 - 1.2 * ease_out_expo(q)
        m.blit(f, lg, W / 2, 690, alpha=clamp01(q * 4), escala=s * pulso, centro=True)
        el.anillo(f, W / 2, 690, 156, ease_out_cubic(prog(t, 2.2, 0.8)), ORO, 7, giro=-90 + 30 * t)
        marca.draw(f, 845, t, 2.3, paso=0.07)
        slogan.draw(f, 950, t, 2.7, paso=0.05)
        y = 1020
        for k, (spr, t0) in enumerate(filas):
            qq = prog(t, t0, 0.5)
            m.blit(f, spr, W / 2 + (1 - ease_out_back(qq, 1.2)) * (1100 if k % 2 == 0 else -1100), y + spr.shape[0] / 2,
                   alpha=clamp01(qq * 3), centro=True)
            y += spr.shape[0] + 12
        xc = 50.0
        for i, c in enumerate(chips):
            qq = prog(t, 5.5 + i * 0.12, 0.4)
            m.blit(f, c, xc + c.shape[1] / 2, y + 40, alpha=clamp01(qq * 3), escala=0.7 + 0.3 * ease_out_back(qq, 1.8), centro=True)
            xc += c.shape[1] + gap_c
        # remate: barrido de luz final sobre el logo
        m.barrido_luz(f, prog(t, info.dur - 3.2, 0.8), 220, -18, 0.5, (W // 2 - 220, 480, W // 2 + 220, 840))
        return f
    return fn


GUION = [
    dict(nombre="gancho", min_beats=6, hold=0.4, voz=[("¿Necesitás alimento para tus animales?", 0.12)], fabrica=esc_gancho, impacto="impacto"),
    dict(nombre="varios", min_beats=14, hold=0.4, voz=[("En Forralitas tenemos opciones para distintos animales y necesidades.", 0.55)], fabrica=esc_varios),
    dict(nombre="categorias", min_beats=18, hold=0.9,
         voz=[("Para caballos.", 0.15), ("Para gallinas.", 1.35), ("Para cerdos.", 1.35), ("Para perros y gatos.", 1.2)], fabrica=esc_categorias),
    dict(nombre="ubicacion", min_beats=10, hold=0.6,
         voz=[("Estamos en Las Talitas, Tucumán, para ayudarte a encontrar lo que necesitás.", 0.45)], fabrica=esc_ubicacion),
    dict(nombre="cierre", min_beats=18, hold=2.4,
         voz=[("¡Hacé tu consulta! Forralitas.", 0.55),
              ("Llamanos al tres ocho uno, cinco dos seis, nueve cero cero cuatro.", 0.12),
              ("Lunes a sábado. Hacemos envíos según la zona.", 0.12)],
         fabrica=esc_cierre, impacto="impacto"),
]


def main():
    plan, beat, total = base.planificar(BPM, GUION, ritmo=0.9)
    print("duración", round(total, 2), "s | escenas:", [(e["nombre"], round(e["dur"], 2)) for e in plan])
    trans = [lambda a, b, p: m.tr_diagonal(a, b, p, ORO, VERDE_OSC),
             lambda a, b, p: m.tr_whip(a, b, p, "der"),
             lambda a, b, p: m.tr_persianas(a, b, p, 7),
             lambda a, b, p: m.tr_circulo(a, b, p, W / 2, 1000, ORO)]
    tl = base.construir_linea(plan, trans)
    pal = base.palabras_globales(plan)
    subs = m.Subtitulos(pal, y=1500, color=m.BLANCO, activo=m.ORO_CLARO)
    c, cat = plan[-1], plan[2]
    sin_subs = [(c["ini"] + 0.3, total + 1), (cat["ini"] + 0.1, cat["ini"] + cat["dur"] + 0.2)]
    if "--frames" in sys.argv:
        ts = [float(x) for x in sys.argv[sys.argv.index("--frames") + 1:]]
        base.vista_previa(tl, subs, sin_subs, ts, str(base.SALIDA / "miniaturas/_prev_v3"), grado="limpio")
        return
    wav = base.audio(plan, total, "publicitario", BPM, NOMBRE)
    salida = base.SALIDA / f"videos/{NOMBRE}.mp4"
    base.renderizar(tl, subs, sin_subs, total, wav, salida, grado="limpio")
    print("listo", salida)


if __name__ == "__main__":
    main()
