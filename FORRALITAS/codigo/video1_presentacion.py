"""VIDEO 1 — PRESENTACIÓN DE FORRALITAS ("Todo lo que tus animales necesitan, en un solo lugar").
Dirección de arte: verde profundo cinematográfico, oro, parallax y tipografía cinética.
Uso (desde la raíz del repositorio):
    python FORRALITAS/codigo/video1_presentacion.py [--frames t1 t2 ...]
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

NOMBRE = "FORRALITAS_PRESENTACION"
BPM = 96
D = m.datos()

# ------------------------------------------------------------------ fondo común
_FONDO = m.degradado(m.VERDE_MED, m.VERDE_OSC, 0.5, 0.35, 1.0)


def fondo(t, semilla=1, rayos=True):
    f = _FONDO.copy()
    if rayos:                                   # haces de luz suaves que se desplazan lento
        ov = np.zeros((H // 4, W // 4), np.float32)
        for i, (x0, ang) in enumerate(((0.2, -24), (0.62, -20), (0.95, -28))):
            xs = np.arange(W // 4, dtype=np.float32)[None, :]
            ys = np.arange(H // 4, dtype=np.float32)[:, None]
            c = (x0 + 0.05 * np.sin(t * 0.35 + i)) * W / 4
            d = (xs - c) + ys * np.tan(np.radians(ang))
            ov += np.exp(-(d / 34) ** 2) * (0.05 + 0.02 * i)
        ov = cv2.resize(ov, (W, H))[..., None]
        f = np.clip(f + (255 - f) * ov * 0.9, 0, 255).astype(np.uint8)
    m.particulas(f, t, semilla, n=30, tam=(4, 12), intensidad=0.5)
    return f


def oscurecer(img, k):
    return (img.astype(np.float32) * k).astype(np.uint8)


# ------------------------------------------------------------------ A. GANCHO (0-3 s)
def esc_gancho(info):
    ph = m.Foto("maiz_entero")
    l1 = m.Letras("CALIDAD", 232, m.NEGRA, m.ORO_CLARO, trazo=0)
    l2 = m.Cinetico("*PARA TUS* ANIMALES", 94, 960, m.NEGRA, m.BLANCO, m.VERDE_OSC, m.ORO, interlinea=1.1)
    info.sfx += [(0.0, "impacto", 1.0), (0.18, "pop", 0.8), (0.55, "tick", 0.8), (1.0, "pop", 0.6)]

    def fn(t):
        p = m.rampa(prog(t, 0, info.dur), 0.5, 2.2)
        cx, cy, z = m.camara(p, 1.0, 1.55, (0.45, 0.62), (0.52, 0.38), ease=lambda x: x)
        f = ph.ventana(W, H, cx, cy, z, rot=-1.5 + 3 * p)
        f = oscurecer(f, 0.62 - 0.1 * (1 - ease_out_cubic(prog(t, 0, 0.4))))
        s = 1 + 0.045 * np.exp(-((t * 1.0) % (info.beat)) * 7)        # pulso al compás
        f = cv2.resize(f, None, fx=s, fy=s)[int((H * s - H) / 2):int((H * s - H) / 2) + H, int((W * s - W) / 2):int((W * s - W) / 2) + W]
        f = np.ascontiguousarray(f)
        m.particulas(f, t, 5, n=22, tam=(5, 14), vel=(60, 160), intensidad=0.7)
        l1.draw(f, W / 2, 760, t, 0.1, paso=0.055, caida=220, escala0=1.9)
        l2.draw(f, 905, t, 0.62, paso=0.14)
        m.barrido_luz(f, prog(t, 0.9, 0.9), 300, -18, 0.5, (0, 640, W, 1130))
        return f
    return fn


# ------------------------------------------------------------------ B. PRESENTACIÓN DEL LOGO (3-10 s)
def esc_logo(info):
    lg = el.logo(560)
    slogan = m.Cinetico("Alimentos de *calidad* para cada animal", 56, 1010, m.SERIF, m.BLANCO, m.VERDE_OSC, m.ORO)
    cards = [("pellet_trigo", -7, 250, 0.00, 2.1), ("alfalfa", 3, 540, 0.00, 2.5), ("perros_gatos", 7, 830, 0.00, 2.9)]
    info.sfx += [(0.25, "brillo", 1.0), (0.2, "subida", 0.6), (2.0, "pop", 0.8), (2.4, "pop", 0.8), (2.8, "pop", 0.8)]

    def fn(t):
        f = fondo(t, 3)
        cx, cy = W / 2, 585
        q = prog(t, 0.1, 0.9)
        e = ease_out_back(q, 1.5)
        # onda de luz detrás del logo
        r = int(440 * ease_out_expo(prog(t, 0.1, 1.0)))
        ov = f.copy()
        cv2.circle(ov, (int(cx), int(cy)), r, m.ORO_CLARO, -1, cv2.LINE_AA)
        cv2.addWeighted(ov, 0.22 * (1 - prog(t, 0.9, 1.0) * 0.6), f, 1 - 0.22 * (1 - prog(t, 0.9, 1.0) * 0.6), 0, f)
        el.anillo(f, cx, cy, 330, ease_out_cubic(prog(t, 0.2, 1.0)), m.ORO, 9, giro=-90 + 40 * t)
        el.anillo(f, cx, cy, 352, ease_out_cubic(prog(t, 0.35, 1.0)), m.ORO_CLARO, 3, giro=90 - 30 * t)
        m.blit(f, lg, cx, cy + 14 * np.sin(t * 1.7), alpha=clamp01(q * 2.5), escala=0.5 + 0.5 * e, centro=True)
        m.barrido_luz(f, prog(t, 0.9, 0.8), 240, -18, 0.55, (int(cx - 300), int(cy - 300), int(cx + 300), int(cy + 300)))
        slogan.draw(f, 925, t, 1.0, paso=0.1)
        for nombre, rot, x, t0, ti in cards:                                    # tarjetas con parallax
            qa = prog(t, ti, 0.7)
            if qa <= 0:
                continue
            y = 1215 + (1 - ease_out_back(qa, 1.3)) * 520 + 8 * np.sin(t * 1.3 + x)
            img = m.Foto(nombre).ventana(300, 340, 0.5, 0.5, 1.12 + 0.05 * np.sin(t * 0.8 + x), 0)
            m.poner_tarjeta(f, img, x, y, 1.0, rot + 2 * np.sin(t * 0.9 + x), clamp01(qa * 2.5), r=28, borde=8)
        return f
    return fn


# ------------------------------------------------------------------ C. PRODUCTOS (10-24 s)
PRODUCTOS = [("MAÍZ", "maiz_entero", (0.5, 0.45), (0.5, 0.6)),
             ("ALFALFA", "alfalfa", (0.5, 0.35), (0.5, 0.62)),
             ("AVENA", None, None, None),
             ("EXPELLER DE SOJA", None, None, None),
             ("BALANCEADOS", "perros_sabrositos", (0.5, 0.7), (0.5, 0.3))]


def esc_productos(info):
    ini = [v[0] - 0.12 for v in info.voces]
    ini[0] = 0.0
    fin = ini[1:] + [info.dur + 1]
    tit = [m.Letras(n, 108 if len(n) < 9 else 78, m.NEGRA, m.BLANCO, trazo=0) for n, *_ in PRODUCTOS]
    sub = {2: "Consultá disponibilidad", 3: "Consultá disponibilidad", 0: "Consultá presentaciones y precios",
           1: "Consultá disponibilidad", 4: "Wenuy · Manada · Sabrositos"}
    for i, v in enumerate(info.voces):
        info.sfx += [(ini[i] + 0.05, "pop", 0.9), (ini[i] + 0.1, "tick", 0.7)]

    def fn(t):
        f = fondo(t, 8)
        # tarjeta activa y la anterior saliendo
        for i, (nombre, foto, a, b) in enumerate(PRODUCTOS):
            if not (ini[i] - 0.4 <= t < fin[i] + 0.55):
                continue
            tl = t - ini[i]
            ent = ease_out_back(prog(tl, 0, 0.55), 1.2)
            sal = ease_in_out(prog(t - fin[i], 0.0, 0.5))
            x = W / 2 + (1 - ent) * 900 - sal * 1000
            rot = (1 - ent) * 14 - sal * 10 + 2.0 * np.sin(t * 1.2 + i)
            cy = 735 + 10 * np.sin(t * 1.5 + i)
            if foto:
                pp = prog(tl, 0, fin[i] - ini[i] + 0.3)
                cx_, cy_, z = m.camara(pp, 1.0, 1.28, a, b)
                img = m.Foto(foto).ventana(900, 960, cx_, cy_, z, 0)
            else:                                           # tarjeta tipográfica (sin foto de producto disponible)
                img = np.zeros((960, 900, 3), np.uint8)
                img[:] = m.degradado(m.VERDE_MED, m.VERDE_OSC, 0.5, 0.45, 0.8)[:960, :900]
                pp = prog(tl, 0, 2.4)
                for k, (ex, ea, es) in enumerate(((220, -18, 1.55), (450, 0, 1.9), (680, 18, 1.55))):
                    el.espiga(img, ex, 640 + 20 * np.sin(t * 1.4 + k), es, ea + 3 * np.sin(t * 1.1 + k), m.ORO, 0.85)
            m.poner_tarjeta(f, img, x, cy, 1.0, rot, 1.0, r=44, borde=10)
            if foto:
                m.barrido_luz(f, prog(tl, 0.35, 0.7), 220, -18, 0.35, (60, 250, 1020, 1210))
            # nombre + subtítulo
            if abs(x - W / 2) < 300:
                q = prog(tl, 0.18, 0.5)
                tit[i].draw(f, W / 2, 1368, tl, 0.15, paso=0.04, caida=90, escala0=1.35)
                pv = el.pastilla(sub[i], 40, m.ORO, m.VERDE_OSC, m.EXTRA)
                m.blit(f, pv, W / 2, 1262, alpha=ease_out_cubic(prog(tl, 0.4, 0.4)), escala=0.85 + 0.15 * ease_out_back(prog(tl, 0.4, 0.4), 1.6), centro=True)
        return f
    return fn


# ------------------------------------------------------------------ D. DIFERENCIACIÓN (24-33 s)
def esc_diferencia(info):
    info.sfx += [(0.15, "pop", 0.8), (0.55, "pop", 0.8), (3.2, "brillo", 0.7)]
    t1 = el.pastilla("ANIMALES DE CAMPO", 46, m.ORO, m.VERDE_OSC, m.NEGRA)
    t2 = el.pastilla("TUS MASCOTAS", 46, m.ORO, m.VERDE_OSC, m.NEGRA)
    ult = m.Cinetico("Todo en un *solo lugar*", 78, 1000, m.NEGRA, m.BLANCO, m.VERDE_OSC, m.ORO, trazo=0)

    def fn(t):
        f = fondo(t, 11, rayos=False)
        ent1 = ease_out_back(prog(t, 0.1, 0.7), 1.1)
        ent2 = ease_out_back(prog(t, 0.45, 0.7), 1.1)
        a = m.Foto("alfalfa_fardos").ventana(980, 500, *m.camara(prog(t, 0, info.dur), 1.0, 1.25, (0.5, 0.6), (0.5, 0.4))[:2], m.camara(prog(t, 0, info.dur), 1.0, 1.25, (0.5, 0.6), (0.5, 0.4))[2])
        b = m.Foto("perros_gatos").ventana(980, 500, *m.camara(prog(t, 0.3, info.dur), 1.0, 1.3, (0.3, 0.45), (0.7, 0.5))[:2], m.camara(prog(t, 0.3, info.dur), 1.0, 1.3, (0.3, 0.45), (0.7, 0.5))[2])
        m.poner_tarjeta(f, a, W / 2 - (1 - ent1) * 1200, 530, 1.0, -2.2 * ent1, 1.0, r=40, borde=9)
        m.poner_tarjeta(f, b, W / 2 + (1 - ent2) * 1200, 1050, 1.0, 2.2 * ent2, 1.0, r=40, borde=9)
        m.blit(f, t1, 330, 320, alpha=clamp01(ent1 * 2), escala=0.8 + 0.2 * ent1, centro=True)
        m.blit(f, t2, 760, 835, alpha=clamp01(ent2 * 2), escala=0.8 + 0.2 * ent2, centro=True)
        # "+" central que conecta los dos mundos
        q = ease_out_back(prog(t, 1.2, 0.5), 2.2)
        cv2.circle(f, (W // 2, 790), int(46 * q), m.ORO, -1, cv2.LINE_AA)
        if q > 0.3:
            cv2.line(f, (W // 2 - int(22 * q), 790), (W // 2 + int(22 * q), 790), m.VERDE_OSC, 8, cv2.LINE_AA)
            cv2.line(f, (W // 2, 790 - int(22 * q)), (W // 2, 790 + int(22 * q)), m.VERDE_OSC, 8, cv2.LINE_AA)
        ult.draw(f, 1318, t, info.voces[-1][0] + 0.2, paso=0.13)
        return f
    return fn


# ------------------------------------------------------------------ E. CIERRE (33-40 s + datos)
def esc_cierre(info):
    lg = el.logo(430)
    slogan = m.Cinetico("Alimentos de *calidad* para cada animal", 56, 1010, m.SERIF, m.BLANCO, m.VERDE_OSC, m.ORO)
    cta = el.pastilla("¡Consultanos por nuestros productos!", 42, m.ORO, m.VERDE_OSC, m.NEGRA)
    ciudad = m.spr_texto("Las Talitas, Tucumán", 48, m.ORO_CLARO, m.SEMI, 0, m.VERDE_OSC, False)
    filas = [
        (el.tarjeta_dato("telefono", tuple(D["tel"]), 980, 150, tam=46), 2.5),
        (el.tarjeta_dato("reloj", tuple(D["horario"]), 980, 130, tam=38), 3.3),
        (el.tarjeta_dato("ubicacion", ("Ruta 305 km 7,5 · Las Talitas", "Envíos según la zona · Venta por mayor y menor"), 980, 130, tam=38), 4.1),
    ]
    pagos = [("efectivo", "Efectivo"), ("transferencia", "Transferencia"), ("debito", "Débito"), ("credito", "Crédito")]
    chips = [el.chip(i, n, None, 76, tam=30) for i, n in pagos]
    gap_c = (980 - sum(c.shape[1] for c in chips)) / 3
    info.sfx += [(0.2, "brillo", 1.0), (2.5, "pop", 0.8), (3.3, "pop", 0.8), (4.1, "pop", 0.8), (4.9, "pop", 0.8), (6.2, "campana", 0.9)]

    def fn(t):
        f = fondo(t, 21)
        q = prog(t, 0.0, 0.8)
        cx, cy = W / 2, 400
        el.anillo(f, cx, cy, 236, ease_out_cubic(prog(t, 0.1, 1.0)), m.ORO, 8, giro=-90 + 30 * t)
        m.blit(f, lg, cx, cy, alpha=clamp01(q * 2.5), escala=0.6 + 0.4 * ease_out_back(q, 1.4), centro=True)
        m.barrido_luz(f, prog(t, 0.8, 0.8), 220, -18, 0.5, (int(cx - 220), int(cy - 220), int(cx + 220), int(cy + 220)))
        slogan.draw(f, 700, t, 0.9, paso=0.1)
        m.blit(f, ciudad, W / 2, 830, alpha=ease_out_cubic(prog(t, 1.6, 0.5)), centro=True)
        m.blit(f, cta, W / 2, 925, alpha=ease_out_cubic(prog(t, 2.0, 0.4)),
               escala=(0.85 + 0.15 * ease_out_back(prog(t, 2.0, 0.4), 1.6)) * (1 + 0.02 * np.sin(t * 5)), centro=True)
        y = 1030
        for spr, t0 in filas:
            qq = prog(t, t0, 0.5)
            m.blit(f, spr, W / 2 + (1 - ease_out_back(qq, 1.2)) * 1100, y + spr.shape[0] / 2, alpha=clamp01(qq * 3), centro=True)
            y += spr.shape[0] + 14
        xc = 50.0
        for i, c in enumerate(chips):                          # medios de pago
            qq = prog(t, 4.9 + i * 0.12, 0.4)
            m.blit(f, c, xc + c.shape[1] / 2, y + 40, alpha=clamp01(qq * 3), escala=0.7 + 0.3 * ease_out_back(qq, 1.8), centro=True)
            xc += c.shape[1] + gap_c
        return f
    return fn


# ------------------------------------------------------------------ guion
GUION = [
    dict(nombre="gancho", min_beats=5, hold=0.35, voz=[("¿Buscás buenos alimentos para tus animales?", 0.12)], fabrica=esc_gancho, impacto="impacto"),
    dict(nombre="logo", min_beats=11, hold=0.5, voz=[("En Forralitas encontrás una gran variedad de alimentos, para cada necesidad.", 0.55)], fabrica=esc_logo, impacto="impacto"),
    dict(nombre="productos", min_beats=20, hold=0.9,
         voz=[("Maíz.", 0.1), ("Alfalfa.", 1.9), ("Avena.", 2.0), ("Expeller de soja.", 1.7), ("Y balanceados.", 1.8)], fabrica=esc_productos),
    dict(nombre="diferencia", min_beats=15, hold=0.4,
         voz=[("Desde alimentos para animales de campo, hasta balanceados para tus mascotas.", 0.3), ("Encontrá lo que necesitás, en un solo lugar.", 0.5)],
         fabrica=esc_diferencia),
    dict(nombre="cierre", min_beats=17, hold=1.3,
         voz=[("Forralitas. ¡Consultanos por nuestros productos!", 0.45),
              ("Llamanos al tres ocho uno, cinco dos seis, nueve cero cero cuatro.", 0.12),
              ("Lunes a sábado.", 0.12)],
         fabrica=esc_cierre, impacto="impacto"),
]


def main():
    plan, beat, total = base.planificar(BPM, GUION)
    print("duración", round(total, 2), "s | escenas:", [(e["nombre"], round(e["dur"], 2)) for e in plan])
    trans = [lambda a, b, p: m.tr_zoom(a, b, p),
             lambda a, b, p: m.tr_circulo(a, b, p, W / 2, 780),
             lambda a, b, p: m.tr_whip(a, b, p, "izq"),
             lambda a, b, p: m.tr_flash(a, b, p)]
    tl = base.construir_linea(plan, trans)
    pal = base.palabras_globales(plan)
    subs = m.Subtitulos(pal, y=1475)
    cierre = plan[-1]
    prod = plan[2]
    sin_subs = [(cierre["ini"] + 0.3, total + 1), (prod["ini"] + 0.1, prod["ini"] + prod["dur"] + 0.2)]
    if "--frames" in sys.argv:
        ts = [float(x) for x in sys.argv[sys.argv.index("--frames") + 1:]]
        base.vista_previa(tl, subs, sin_subs, ts, str(base.SALIDA / f"miniaturas/_prev_v1"))
        return
    wav = base.audio(plan, total, "inspirador", BPM, NOMBRE)
    salida = base.SALIDA / f"videos/{NOMBRE}.mp4"
    base.renderizar(tl, subs, sin_subs, total, wav, salida)
    print("listo", salida)


if __name__ == "__main__":
    main()
