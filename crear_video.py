"""Video publicitario vertical (1080x1920) de Forralitas.

Uso:
    python crear_video.py                  # genera videos_salida/forralitas.mp4
    python crear_video.py --frames 5 12 30 # guarda esos segundos como PNG (vista previa)

Fotos en ./fotos (orden alfabético), logo en assets/logo.jpg.
Los textos de cada foto, datos de contacto y duraciones se editan en CONFIG.
Si ponés un mp3 en CONFIG["musica"] se usa en lugar de la música generada.
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from moviepy import AudioFileClip, VideoClip

import audio
from efectos import (AMARILLO, BLANCO, DIAGONAL, FONDO_VERDE, H, MAPA_GRADIENTE,
                     VERDE, VERDE_OSCURO, W, Foto, ancho_texto, blit, caja, clamp01,
                     ease_in_out, ease_out_back, ease_out_cubic, fondo_animado, icono,
                     logo_redondo, prog, rotar_sprite, sobre, texto, tr_destello,
                     tr_diagonal, tr_empuje_arriba, tr_empuje_der, tr_empuje_izq,
                     tr_iris, tr_zoom)

FPS = 30
TR = 0.55            # duración de cada transición (s)
D_INTRO, D_FOTO, D_CIERRE = 3.8, 2.9, 10.5
PAD = 26             # margen interno de los sprites de texto

CONFIG = {
    "salida": "videos_salida/forralitas.mp4",
    "musica": None,   # ej: "musica.mp3"
    "nombre": "FORRALITAS",
    "rubro": "Forrajería y Semillería",
    "slogan": "Todo para tus animales",
    "direccion": ("Ruta 305 km 7,5", "Las Talitas"),
    "telefonos": ("381 526 9004", "381 633 4344"),
    "horarios": ("Lunes a viernes 8:00 a 19:00", "Sábados 8:30 a 19:00"),
    "servicios": ("Envíos según la zona", "Venta por mayor y menor"),
    "pagos": ("Efectivo", "Transferencia", "Débito", "Crédito"),
    # archivo -> (título, subtítulo). Las palabras con * salen en amarillo.
    "fotos": {
        "01_perros_sabrositos.jpg": ("Alimento para *perros*", "Sabrositos, Wenüy y más marcas"),
        "02_perros_gatos.jpg": ("Perros y *gatos*", "Bolsas de 10, 15 y 22 kg"),
        "03_alfa.jpg": ("Fardos de *alfa*", "Ideal para tus animales de campo"),
        "04_semillas.jpg": ("Semillas para *aves*", "Mezclas listas para dar"),
        "05_sal_lamer.jpg": ("Piedra de sal *iodada*", ""),
        "06_sal_bloque.jpg": ("Piedra de sal *gris*", ""),
        "07_pellets.jpg": ("Pellet de *trigo*", "Bolsa x 30 kg y suelto"),
        "08_balanceado_mix.jpg": ("Mezcla de *caballo*", "Bolsa x 35 kg y suelto"),
        "09_maiz_partido.jpg": ("Maíz *quebrado*", "Bolsa x 40 kg y suelto"),
        "10_pellets_maiz.jpg": ("Engorde de *cerdo*", "Bolsa x 30 kg y suelto"),
        "11_afrecho.jpg": ("Ponedora para *gallinas*", "Por bolsa y suelto"),
        "12_maiz_molido.jpg": ("Afrecho de *maíz*", "Por bolsa y suelto"),
    },
}

# (zoom inicial, zoom final, foco inicial, foco final): movimientos de cámara
CAMARAS = [
    (1.00, 1.24, (0.5, 0.65), (0.5, 0.25)),
    (1.25, 1.02, (0.4, 0.35), (0.55, 0.55)),
    (1.04, 1.22, (0.10, 0.5), (0.90, 0.5)),
    (1.22, 1.04, (0.90, 0.5), (0.15, 0.5)),
    (1.00, 1.26, (0.5, 0.2), (0.5, 0.7)),
    (1.24, 1.00, (0.6, 0.6), (0.4, 0.3)),
]
TRANSICIONES = [tr_zoom, tr_empuje_izq, tr_iris, tr_empuje_arriba, tr_destello, tr_diagonal,
                tr_zoom, tr_empuje_der, tr_iris, tr_empuje_izq, tr_diagonal, tr_empuje_arriba,
                tr_zoom]


# ------------------------------------------------------------ utilidades de texto
def fila_palabras(marcado, tam, max_w, color=BLANCO):
    """Devuelve (sprites, x de cada palabra, ancho total) para una línea centrada."""
    pal = [(p.strip("*"), p.startswith("*")) for p in marcado.split()]
    while True:
        gap = tam * 0.3
        anchos = [ancho_texto(p, tam) for p, _ in pal]
        total = sum(anchos) + gap * (len(pal) - 1)
        if total <= max_w or tam <= 36:
            break
        tam -= 4
    sprites = [texto(p, tam, AMARILLO if d else color) for p, d in pal]
    x, xs = (W - total) / 2, []
    for a in anchos:
        xs.append(x - PAD)
        x += a + gap
    return sprites, xs, tam


def texto_ajustado(txt, tam, max_w, color=BLANCO, sombra=False):
    while ancho_texto(txt, tam) > max_w and tam > 20:
        tam -= 2
    return texto(txt, tam, color, sombra)


def dibujar_palabras(f, sprites, xs, y, t, inicio, paso=0.11, dur=0.45):
    for i, (s, x) in enumerate(zip(sprites, xs)):
        p = prog(t, inicio + paso * i, dur)
        e = ease_out_back(p)
        blit(f, s, x + s.shape[1] * (1 - 0.7 - 0.3 * e) / 2,
             y + (1 - ease_out_cubic(p)) * 55, alpha=ease_out_cubic(p * 1.6),
             escala=0.7 + 0.3 * e)


# ------------------------------------------------------------ escenas
def escena_intro():
    logo = logo_redondo(640)
    nombre = CONFIG["nombre"]
    tam = 128
    letras = [texto(c, tam, BLANCO) for c in nombre]
    x0 = (W - ancho_texto(nombre, tam)) / 2
    xs = [x0 + ancho_texto(nombre[:i], tam) - PAD for i in range(len(nombre))]
    rubro = texto(CONFIG["rubro"], 66, AMARILLO)
    slogan = texto(CONFIG["slogan"], 48, BLANCO)

    def fn(t):
        f = fondo_animado(t, semilla=3)
        for k in range(3):                              # ondas de pulso detrás del logo
            pk = prog(t, 0.35 + 0.28 * k, 1.5)
            if 0 < pk < 1:
                ov = f.copy()
                cv2.circle(ov, (W // 2, 700), int(300 + 620 * ease_out_cubic(pk)),
                           AMARILLO, 5, cv2.LINE_AA)
                f = cv2.addWeighted(ov, 0.55 * (1 - pk), f, 1 - 0.55 * (1 - pk), 0)
        p = prog(t, 0.15, 0.95)
        blit(f, rotar_sprite(logo, -28 * (1 - ease_out_cubic(p))), W / 2, 700,
             alpha=clamp01(p * 3), escala=ease_out_back(p), centro=True)
        for i, (s, x) in enumerate(zip(letras, xs)):
            q = prog(t, 1.15 + 0.07 * i, 0.5)
            e = ease_out_back(q)
            blit(f, s, x, 1125 + (1 - ease_out_cubic(q)) * 90, alpha=ease_out_cubic(q * 1.5),
                 escala=0.6 + 0.4 * e)
        blit(f, rubro, (W - rubro.shape[1]) / 2, 1290, wipe=ease_out_cubic(prog(t, 2.0, 0.7)))
        blit(f, slogan, (W - slogan.shape[1]) / 2, 1400 + (1 - ease_out_cubic(prog(t, 2.5, 0.6))) * 30,
             alpha=ease_out_cubic(prog(t, 2.5, 0.6)))
        return f
    return fn


def escena_producto(ruta, titulo, sub, cam):
    foto = Foto(ruta)
    z0, z1, a, b = cam
    spr_t, xs, tam = fila_palabras(titulo, 112, W - 110)
    pastilla = None
    if sub:
        s_sub = texto(sub, 50, BLANCO, sombra=False)
        pastilla = sobre(caja(s_sub.shape[1] + 30, s_sub.shape[0], 59, VERDE_OSCURO, 0.9), s_sub, 15, 0)
    logo = logo_redondo(120)
    marca = texto(CONFIG["nombre"], 44, BLANCO)
    rubro = texto(CONFIG["rubro"], 28, AMARILLO)
    pie_icono = icono("ubicacion", 56)
    pie = texto(f"{CONFIG['direccion'][0]} · {CONFIG['direccion'][1]}", 36, BLANCO)
    y_t = 1180
    delay = 0.38
    gmax = float(DIAGONAL.max())

    def fn(t):
        p = t / D_FOTO
        f = foto.frame(p, z0, z1, a, b).astype(np.float32) * MAPA_GRADIENTE
        # destello de luz que cruza la foto al entrar
        ps = prog(t, 0.05, 0.8)
        if 0 < ps < 1:
            pos = ease_in_out(ps) * (gmax + 400) - 200
            f += np.exp(-(((DIAGONAL - pos) / 110) ** 2))[..., None] * 70
        f = np.clip(f, 0, 255).astype(np.uint8)
        td = t - delay

        # cabecera: logo + marca
        ph = ease_out_cubic(prog(t, 0.15, 0.5))
        blit(f, logo, 60 - (1 - ph) * 200, 150, alpha=ph)
        blit(f, marca, 196 - (1 - ph) * 200, 143, alpha=ph)
        blit(f, rubro, 196 - (1 - ph) * 200, 208, alpha=ph)

        # franja amarilla que se abre desde el centro
        wbar = int(300 * ease_out_cubic(prog(td, 0, 0.45)))
        if wbar > 0:
            cv2.rectangle(f, (W // 2 - wbar // 2, y_t - 22), (W // 2 + wbar // 2, y_t - 10),
                          AMARILLO, -1, cv2.LINE_AA)
        dibujar_palabras(f, spr_t, xs, y_t, td, 0.08)

        # subtítulo en pastilla que se despliega
        ps2 = prog(td, 0.12 * len(spr_t) + 0.2, 0.55)
        if pastilla is not None:
            blit(f, pastilla, (W - pastilla.shape[1]) / 2, y_t + 190 + (1 - ease_out_cubic(ps2)) * 25,
                 alpha=ease_out_cubic(ps2 * 2), wipe=ease_out_cubic(ps2))

        # pie con la dirección
        pf = ease_out_cubic(prog(td, 0.9, 0.6))
        total = 56 + 14 + pie.shape[1] - 2 * PAD
        xi = (W - total) / 2
        blit(f, pie_icono, xi, 1500 + (1 - pf) * 20, alpha=pf)
        blit(f, pie, xi + 56 + 14 - PAD, 1500 - 6 + (1 - pf) * 20, alpha=pf)
        return f
    return fn


# tiempos (s, locales al cierre) en que aparece cada elemento
T_TEL, T_HORA, T_UBIC, T_ENVIO, T_MAYOR, T_PAGOS = 1.3, 2.0, 2.7, 3.2, 3.8, 4.5
T_CHIPS = (4.8, 5.0, 5.2, 5.4)
T_TIMBRE0, PERIODO_TIMBRE = T_TEL + 0.5, 1.8


def dibujar_reloj(f, cx, cy, r, t, t0):
    """Reloj animado: las agujas giran rápido y se clavan en las 8:00."""
    cv2.circle(f, (cx, cy), r + int(5 * (0.5 + 0.5 * np.sin(t * 5))), AMARILLO, 3, cv2.LINE_AA)
    cv2.circle(f, (cx, cy), r, AMARILLO, -1, cv2.LINE_AA)
    cv2.circle(f, (cx, cy), r - 8, (250, 245, 215), -1, cv2.LINE_AA)
    for k in range(12):
        a = np.radians(k * 30)
        r0 = r - 8 - (11 if k % 3 == 0 else 6)
        cv2.line(f, (int(cx + r0 * np.sin(a)), int(cy - r0 * np.cos(a))),
                 (int(cx + (r - 10) * np.sin(a)), int(cy - (r - 10) * np.cos(a))),
                 VERDE_OSCURO, 3 if k % 3 == 0 else 2, cv2.LINE_AA)
    giro = (1 - ease_out_cubic(prog(t, t0 + 0.35, 1.9))) * 360 * 4
    ang_min = np.radians(giro)
    ang_hor = np.radians(240 + giro / 12)
    for ang, largo, grosor in ((ang_hor, 0.5, 6), (ang_min, 0.76, 4)):
        cv2.line(f, (cx, cy), (int(cx + r * largo * np.sin(ang)), int(cy - r * largo * np.cos(ang))),
                 VERDE_OSCURO, grosor, cv2.LINE_AA)
    if t > t0 + 2.2:                                     # segundero
        ang = np.radians((t - t0 - 2.2) * 120)
        cv2.line(f, (cx, cy), (int(cx + r * 0.8 * np.sin(ang)), int(cy - r * 0.8 * np.cos(ang))),
                 (200, 40, 30), 2, cv2.LINE_AA)
    cv2.circle(f, (cx, cy), 6, VERDE_OSCURO, -1, cv2.LINE_AA)


def escena_cierre():
    logo = logo_redondo(210)
    spr_t, xs, _ = fila_palabras("¡TE *ESPERAMOS!*", 92, W - 100)
    c = CONFIG
    tarjeta = lambda h: caja(940, h, 38, (3, 34, 14), 0.86)

    # teléfono: dos números grandes
    n1 = texto_ajustado(c["telefonos"][0], 64, 700, AMARILLO, True)
    n2 = texto_ajustado(c["telefonos"][1], 64, 700, AMARILLO, True)
    card_tel = sobre(sobre(tarjeta(180), n1, 190 - PAD, 2), n2, 190 - PAD, 84)
    ic_tel = icono("telefono", 124)
    # horarios
    h1 = texto_ajustado(c["horarios"][0], 46, 690, BLANCO)
    h2 = texto_ajustado(c["horarios"][1], 46, 690, (205, 235, 205))
    card_hora = sobre(sobre(tarjeta(180), h1, 190 - PAD, 14), h2, 190 - PAD, 86)
    # ubicación
    u1 = texto_ajustado(c["direccion"][0], 46, 690, BLANCO)
    u2 = texto_ajustado(c["direccion"][1], 42, 690, (205, 235, 205))
    card_ubic = sobre(sobre(sobre(tarjeta(140), icono("ubicacion", 96), 32, 22), u1, 170 - PAD, 2), u2, 170 - PAD, 66)
    # envíos
    e1 = texto_ajustado(c["servicios"][0], 50, 700, BLANCO)
    card_env = sobre(sobre(tarjeta(140), icono("camion", 96), 32, 22), e1, 170 - PAD, 8)
    # venta por mayor y menor
    banner = caja(940, 112, 56, AMARILLO)
    tb = texto_ajustado("VENTA POR MAYOR Y MENOR", 52, 860, VERDE_OSCURO)
    banner = sobre(banner, tb, (940 - tb.shape[1]) // 2, (112 - tb.shape[0]) // 2)
    # medios de pago
    titulo_pago = texto_ajustado("Aceptamos todos los medios de pago", 42, 940, BLANCO, True)
    chips = []
    for nom, etq in zip(("efectivo", "transferencia", "debito", "credito"), c["pagos"]):
        ch = sobre(caja(450, 112, 30, (3, 34, 14), 0.9), icono(nom, 80), 22, 16)
        t = texto_ajustado(etq, 42, 300, BLANCO)
        chips.append(sobre(ch, t, 118 - PAD, (112 - t.shape[0]) // 2))

    y_tel, y_hora, y_ubic, y_env, y_may = 410, 606, 802, 958, 1114
    y_pago, y_chip = 1236, 1352

    def entra(t, t0, dur=0.65):
        q = prog(t, t0, dur)
        return q, ease_out_cubic(q)

    def fn(t):
        f = fondo_animado(t, semilla=5)
        p = prog(t, 0.2, 0.8)
        blit(f, logo, W / 2, 195, alpha=clamp01(p * 3), escala=ease_out_back(p), centro=True)
        dibujar_palabras(f, spr_t, xs, 295, t, 0.7, paso=0.1)

        # --- teléfono: la tarjeta entra, los números se "tipean" y el ícono vibra con ondas
        q, e = entra(t, T_TEL)
        x = 70 + (1 - e) * W
        blit(f, card_tel, x, y_tel, alpha=clamp01(q * 2.5))
        if q > 0:
            cx, cy = x + 32 + 62, y_tel + 90
            fase = (t - T_TIMBRE0) % PERIODO_TIMBRE if t >= T_TIMBRE0 else 99
            env = max(0.0, 1 - fase / 0.62)
            if env > 0:
                for k in range(3):
                    r = 74 + 30 * k + fase * 90
                    ov = f.copy()
                    cv2.circle(ov, (int(cx), int(cy)), int(r), AMARILLO, 4, cv2.LINE_AA)
                    a = env * (1 - k * 0.28) * 0.55
                    f[:] = cv2.addWeighted(ov, a, f, 1 - a, 0)
            ang = 20 * np.sin(fase * 52) * env if env > 0 else 0
            blit(f, rotar_sprite(ic_tel, ang), cx, cy, alpha=clamp01(q * 2.5),
                 escala=1 + 0.08 * env, centro=True)
        # brillo de "tipeo" sobre los números
        qn = prog(t, T_TEL + 0.55, 0.9)
        if 0 < qn < 1:
            pos = int(x + 190 + qn * 560)
            ov = f.copy()
            cv2.rectangle(ov, (pos - 10, y_tel + 18), (pos + 10, y_tel + 160), (255, 255, 255), -1)
            f[:] = cv2.addWeighted(ov, 0.35, f, 0.65, 0)

        # --- horarios con reloj animado
        q, e = entra(t, T_HORA)
        x = 70 + (1 - e) * W
        blit(f, card_hora, x, y_hora, alpha=clamp01(q * 2.5))
        if q > 0.05:
            dibujar_reloj(f, int(x + 32 + 62), y_hora + 90, 58, t, T_HORA)

        # --- ubicación y envíos
        for card, t0, y in ((card_ubic, T_UBIC, y_ubic), (card_env, T_ENVIO, y_env)):
            q, e = entra(t, t0)
            blit(f, card, 70 - (1 - e) * W, y, alpha=clamp01(q * 2.5))

        # --- banner mayor y menor con destello
        q = prog(t, T_MAYOR, 0.7)
        bx = 70 + (1 - ease_out_back(q, 1.4)) * (-W)
        blit(f, banner, bx, y_may, alpha=clamp01(q * 3))
        if q >= 1:
            pos = ((t - T_MAYOR - 0.7) % 2.2) * 1700 - 400
            x0, y0 = 70, y_may
            reg = f[y0:y0 + 112, x0:x0 + 940].astype(np.float32)
            reg += (np.exp(-(((DIAGONAL[y0:y0 + 112, x0:x0 + 940] - pos) / 45) ** 2))
                    * banner[:, :, 3])[..., None] * 140
            f[y0:y0 + 112, x0:x0 + 940] = np.clip(reg, 0, 255).astype(np.uint8)

        # --- medios de pago
        qt = prog(t, T_PAGOS, 0.6)
        blit(f, titulo_pago, (W - titulo_pago.shape[1]) / 2, y_pago + (1 - ease_out_cubic(qt)) * 25,
             alpha=ease_out_cubic(qt))
        for i, (ch, t0) in enumerate(zip(chips, T_CHIPS)):
            q = prog(t, t0, 0.55)
            idle = 1 + 0.015 * np.sin(t * 3 + i) if q >= 1 else 1
            cx = 70 + (i % 2) * 490 + 225
            cy = y_chip + (i // 2) * 128 + 56
            blit(f, ch, cx, cy, alpha=clamp01(q * 3), escala=max(ease_out_back(q, 2.4), 0.01) * idle,
                 centro=True)
        return f
    return fn


# ------------------------------------------------------------ línea de tiempo
def construir():
    fotos = sorted(Path("fotos").glob("*.jp*g"), key=lambda p: p.name)
    segs = [(D_INTRO, escena_intro())]
    for i, ruta in enumerate(fotos):
        titulo, sub = CONFIG["fotos"].get(ruta.name, (ruta.stem.replace("_", " ").title(), ""))
        segs.append((D_FOTO, escena_producto(ruta, titulo, sub, CAMARAS[i % len(CAMARAS)])))
    segs.append((D_CIERRE, escena_cierre()))

    inicios, t = [], 0.0
    for d, _ in segs:
        inicios.append(t)
        t += d - TR
    total = inicios[-1] + segs[-1][0]
    return segs, inicios, total


def hacer_frame_fn(segs, inicios, total):
    n_fotos = len(segs) - 2
    t_ini_fotos = inicios[1] + TR
    t_fin_fotos = inicios[-1]

    def make_frame(t):
        t = min(t, total - 1e-3)
        activos = [i for i, (s, (d, _)) in enumerate(zip(inicios, segs)) if s <= t < s + d]
        if len(activos) == 1:
            i = activos[0]
            f = segs[i][1](t - inicios[i])
        else:
            a, b = activos[0], activos[-1]
            fa = segs[a][1](t - inicios[a])
            fb = segs[b][1](t - inicios[b])
            f = TRANSICIONES[a % len(TRANSICIONES)](fa, fb, (t - inicios[b]) / TR)
        # barra de progreso estilo "stories" durante los productos
        if t_ini_fotos - 0.2 <= t <= t_fin_fotos + 0.2 and n_fotos:
            f = np.ascontiguousarray(f)
            x0, x1, y = 60, W - 60, 62
            q = clamp01((t - t_ini_fotos) / (t_fin_fotos - t_ini_fotos))
            ov = f.copy()
            cv2.line(ov, (x0, y), (x1, y), (255, 255, 255), 8, cv2.LINE_AA)
            f = cv2.addWeighted(ov, 0.28, f, 0.72, 0)
            cv2.line(f, (x0, y), (int(x0 + (x1 - x0) * q), y), AMARILLO, 8, cv2.LINE_AA)
        return f
    return make_frame


def main():
    segs, inicios, total = construir()
    make_frame = hacer_frame_fn(segs, inicios, total)

    if "--frames" in sys.argv:
        segundos = [float(x) for x in sys.argv[sys.argv.index("--frames") + 1:]]
        Path("videos_salida").mkdir(exist_ok=True)
        from PIL import Image
        for s in segundos:
            Image.fromarray(make_frame(s)).save(f"videos_salida/prev_{s:05.1f}.png")
        print("duración total:", round(total, 2), "s")
        return

    Path(CONFIG["salida"]).parent.mkdir(exist_ok=True)
    musica = CONFIG["musica"]
    if not (musica and Path(musica).exists()):
        musica = audio.generar(
            total,
            t_transiciones=[inicios[i] - 0.07 for i in range(1, len(segs))],
            t_drop=inicios[1] + TR,
            t_golpes=[0.25, inicios[-1] + 0.2],
            t_dings=[inicios[-1] + o + 0.15 for o in (T_HORA, T_UBIC, T_ENVIO, T_MAYOR, T_PAGOS, *T_CHIPS)],
            t_timbres=[inicios[-1] + T_TIMBRE0 + k * PERIODO_TIMBRE for k in range(4)])
    pista = AudioFileClip(musica).subclipped(0, total)
    video = VideoClip(make_frame, duration=total).with_audio(pista)
    video.write_videofile(CONFIG["salida"], fps=FPS, codec="libx264", audio_codec="aac",
                          audio_bitrate="192k", preset="medium",
                          ffmpeg_params=["-crf", "18", "-pix_fmt", "yuv420p",
                                         "-movflags", "+faststart"])
    print("Listo:", CONFIG["salida"], f"({total:.1f} s)")


if __name__ == "__main__":
    main()
