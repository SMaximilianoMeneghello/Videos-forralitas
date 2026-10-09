"""Genera el video publicitario vertical (1080x1920) de Forralitas.

Uso:
    python crear_video.py            # genera videos_salida/forralitas.mp4

Las fotos van en ./fotos (se usan en orden alfabético) y el logo en
assets/logo.jpg. Los textos de cada foto, el teléfono, etc. se editan en
CONFIG, abajo.
"""
from pathlib import Path

import numpy as np
from moviepy import VideoClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont, ImageOps

ANCHO, ALTO = 1080, 1920
FPS = 30
VERDE = (11, 77, 35)
VERDE_OSCURO = (6, 48, 21)
AMARILLO = (255, 213, 64)
BLANCO = (255, 255, 255)
FUENTE = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

CONFIG = {
    "nombre": "FORRALITAS",
    "rubro": "Forrajería y Semillería",
    "direccion": "Ruta 305 km 7,5 · Las Talitas",
    "telefonos": ["381 526 9004", "381 633 4344"],
    "horarios": ["Lunes a viernes: 8:00 a 19:00", "Sábados: 8:30 a 19:00"],
    "extras": ["Envíos según la zona", "Venta por mayor y menor"],
    "segundos_por_foto": 2.6,
    "salida": "videos_salida/forralitas.mp4",
    # texto que se muestra sobre cada foto (clave: nombre del archivo)
    "frases": {
        "01_perros_sabrositos.jpg": ("Alimento para perros", "Y para todas las mascotas"),
        "02_perros_gatos.jpg": ("Perros y gatos", "Todas las marcas y tamaños"),
        "03_alfalfa.jpg": ("Fardos de alfalfa", "Calidad para tus animales"),
        "04_semillas_aves.jpg": ("Semillas para aves", "Mezclas para cada especie"),
        "05_sal_lamer.jpg": ("Sal tónica para lamer", "Para caballos y ganado"),
        "06_sal_bloque.jpg": ("Sal en bloque", "Mineral y natural"),
        "07_balanceado.jpg": ("Balanceados", "Para todo tipo de animales"),
        "08_maiz_partido.jpg": ("Maíz partido", "Fresco y de primera"),
        "09_pellets_maiz.jpg": ("Pellets y maíz", "Rendidor y económico"),
        "10_afrechillo.jpg": ("Afrechillo y mezclas", "Por kilo o por bolsa"),
    },
}


def fuente(tam):
    return ImageFont.truetype(FUENTE, tam)


def ancho_texto(draw, txt, f):
    return draw.textlength(txt, font=f)


def texto_centrado(draw, txt, y, tam, color, sombra=True, max_ancho=ANCHO - 100):
    f = fuente(tam)
    while ancho_texto(draw, txt, f) > max_ancho and tam > 20:
        tam -= 2
        f = fuente(tam)
    x = (ANCHO - ancho_texto(draw, txt, f)) / 2
    if sombra:
        draw.text((x + 3, y + 3), txt, font=f, fill=(0, 0, 0), stroke_width=0)
    draw.text((x, y), txt, font=f, fill=color)
    return y + tam


def logo_redondo(lado):
    """Recorta el logo en círculo (el original tiene fondo blanco)."""
    im = Image.open("assets/logo.jpg").convert("RGB")
    mascara = Image.new("L", im.size, 0)
    ImageDraw.Draw(mascara).ellipse((55, 55, im.width - 55, im.height - 55), fill=255)
    im.putalpha(mascara)
    return im.crop((55, 55, im.width - 55, im.height - 55)).resize((lado, lado), Image.LANCZOS)


def fondo_verde():
    """Degradé vertical verde."""
    t = np.linspace(0, 1, ALTO)[:, None, None]
    a, b = np.array(VERDE, float), np.array(VERDE_OSCURO, float)
    col = a * (1 - t) + b * t
    return Image.fromarray(np.repeat(col, ANCHO, axis=1).astype("uint8"))


def pegar_logo(base, lado, y):
    logo = logo_redondo(lado)
    base.paste(logo, ((ANCHO - lado) // 2, y), logo)


def escena_estatica(imagen, dur):
    arr = np.array(imagen.convert("RGB"))
    return VideoClip(lambda t: arr, duration=dur).with_fps(FPS)


def pantalla_portada(dur=3):
    im = fondo_verde()
    pegar_logo(im, 820, 330)
    d = ImageDraw.Draw(im)
    texto_centrado(d, CONFIG["nombre"], 1230, 130, BLANCO)
    texto_centrado(d, CONFIG["rubro"], 1390, 62, AMARILLO)
    texto_centrado(d, "Todo para tus animales", 1530, 50, BLANCO)
    return escena_estatica(im, dur)


def pantalla_cierre(dur=6):
    im = fondo_verde()
    pegar_logo(im, 360, 110)
    d = ImageDraw.Draw(im)
    y = texto_centrado(d, "¡Te esperamos!", 530, 100, AMARILLO)
    y = texto_centrado(d, CONFIG["nombre"], y + 25, 80, BLANCO)
    y += 55
    for e in CONFIG["extras"]:
        y = texto_centrado(d, e, y + 15, 52, AMARILLO)
    y += 55
    y = texto_centrado(d, "WhatsApp / Llamanos", y, 46, BLANCO)
    for tel in CONFIG["telefonos"]:
        y = texto_centrado(d, tel, y + 12, 78, AMARILLO)
    y += 55
    y = texto_centrado(d, "Ruta 305 km 7,5", y, 62, BLANCO)
    y = texto_centrado(d, "Las Talitas", y + 8, 62, BLANCO)
    y += 55
    for h in CONFIG["horarios"]:
        y = texto_centrado(d, h, y + 10, 44, BLANCO)
    return escena_estatica(im, dur)


def escena_foto(ruta, dur, linea1, linea2):
    # foto rellenando la pantalla, con 15% extra para poder hacer zoom
    escala = 1.15
    w, h = int(ANCHO * escala), int(ALTO * escala)
    foto = ImageOps.fit(Image.open(ruta).convert("RGB"), (w, h), Image.LANCZOS)

    # degradé oscuro abajo para que se lea el texto + franja superior con marca
    arr = np.array(foto, dtype=np.float32)
    grad = np.clip((np.linspace(0, 1, h) - 0.55) / 0.45, 0, 1)[:, None, None]
    arr = arr * (1 - 0.72 * grad)
    top = np.clip((0.12 - np.linspace(0, 1, h)) / 0.12, 0, 1)[:, None, None]
    arr = arr * (1 - 0.55 * top)
    foto = Image.fromarray(arr.astype("uint8"))
    base = np.array(foto)

    def frame(t):
        p = t / dur
        # paneo suave: ventana ANCHOxALTO que se desplaza dentro del 115%
        x = int((w - ANCHO) * (0.2 + 0.6 * p))
        y = int((h - ALTO) * (0.7 - 0.4 * p))
        return base[y:y + ALTO, x:x + ANCHO]

    clip = VideoClip(frame, duration=dur).with_fps(FPS)

    # capa de texto fija, dibujada una sola vez
    capa = Image.new("RGBA", (ANCHO, ALTO), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    texto_centrado(d, CONFIG["nombre"], 70, 58, BLANCO)
    texto_centrado(d, linea1, ALTO - 480, 96, AMARILLO)
    texto_centrado(d, linea2, ALTO - 350, 52, BLANCO)
    texto_centrado(d, "Ruta 305 km 7,5 · Las Talitas", ALTO - 150, 40, BLANCO)
    capa_arr = np.array(capa)
    alfa = capa_arr[:, :, 3:4].astype(np.float32) / 255
    rgb = capa_arr[:, :, :3].astype(np.float32)

    def con_texto(get_frame, t):
        f = get_frame(t).astype(np.float32)
        return (f * (1 - alfa) + rgb * alfa).astype("uint8")

    return clip.transform(con_texto)


def main():
    fotos = sorted(Path("fotos").glob("*.jp*g")) + sorted(Path("fotos").glob("*.png"))
    fotos = sorted(fotos, key=lambda p: p.name)
    dur = CONFIG["segundos_por_foto"]

    escenas = [pantalla_portada()]
    for p in fotos:
        l1, l2 = CONFIG["frases"].get(p.name, (p.stem.replace("_", " ").title(), ""))
        escenas.append(escena_foto(p, dur, l1, l2))
    escenas.append(pantalla_cierre())

    video = concatenate_videoclips(escenas, method="chain")
    Path(CONFIG["salida"]).parent.mkdir(exist_ok=True)
    video.write_videofile(CONFIG["salida"], fps=FPS, codec="libx264",
                          audio=False, preset="veryfast", logger=None)
    print("Listo:", CONFIG["salida"], f"({video.duration:.0f} s)")


if __name__ == "__main__":
    main()
