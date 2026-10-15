"""Folletos (imagen única, para compartir por WhatsApp) de la casa y la cabaña.

Reutiliza fotos/fotogramas ya extraídos de los videos y las mismas
identidades visuales que casa_rivadavia.py (grafito+dorado) y
cabana_tafi.py (bosque+terracota).

Uso:
    source .venv/bin/activate
    python folletos.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

W = 1080
FUENTE_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FUENTE_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
OUT = Path("videos_salida")
OUT.mkdir(exist_ok=True)


def fuente(tam, bold=True):
    return ImageFont.truetype(FUENTE_B if bold else FUENTE_R, tam)


def fit_cover(im, w, h, bias_y=0.5):
    """bias_y: 0 = ancla arriba (recorta abajo), 1 = ancla abajo, 0.5 = centrado."""
    im = im.convert("RGB")
    s = max(w / im.width, h / im.height)
    im = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)
    x0 = (im.width - w) // 2
    y0 = int((im.height - h) * bias_y)
    return im.crop((x0, y0, x0 + w, y0 + h))


def fit_contain(im, w, h, bg):
    im = im.convert("RGB")
    s = min(w / im.width, h / im.height)
    nw, nh = max(1, round(im.width * s)), max(1, round(im.height * s))
    im = im.resize((nw, nh), Image.LANCZOS)
    fondo = Image.new("RGB", (w, h), bg)
    fondo.paste(im, ((w - nw) // 2, (h - nh) // 2))
    return fondo


def redondear(im, radio):
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), radio, fill=255)
    out = im.convert("RGBA")
    out.putalpha(m)
    return out


def pegar(base, im, x, y):
    base.paste(im, (int(x), int(y)), im)


def texto_centrado(d, cx, y, txt, tam, color, bold=True):
    f = fuente(tam, bold)
    bbox = d.textbbox((0, 0), txt, font=f)
    w = bbox[2] - bbox[0]
    d.text((cx - w / 2 - bbox[0], y), txt, font=f, fill=color)
    return y + tam * 1.22


def envolver(d, txt, tam, max_w, bold=False):
    f = fuente(tam, bold)
    palabras = txt.split()
    lineas, actual = [], ""
    for p in palabras:
        prueba = (actual + " " + p).strip()
        if d.textlength(prueba, font=f) <= max_w:
            actual = prueba
        else:
            lineas.append(actual)
            actual = p
    if actual:
        lineas.append(actual)
    return lineas, f


def bullet(d, x, y, max_w, txt, tam, color_txt, color_check, bold=False):
    r = tam * 0.34
    cy = y + tam * 0.62
    d.ellipse((x, cy - r, x + 2 * r, cy + r), fill=color_check)
    f_chk = fuente(int(r * 1.1))
    d.text((x + r * 0.38, cy - r * 0.95), "✓", font=f_chk, fill=(255, 255, 255))
    lineas, f = envolver(d, txt, tam, max_w - 2.6 * r, bold)
    yy = y
    for ln in lineas:
        d.text((x + 2.6 * r, yy), ln, font=f, fill=color_txt)
        yy += tam * 1.28
    return max(yy, y + 2.2 * r)


def degrade_vertical(w, h, c_top, c_bot):
    im = Image.new("RGB", (w, h), c_top)
    px = im.load()
    for y in range(h):
        t = y / max(h - 1, 1)
        col = tuple(int(c_top[i] * (1 - t) + c_bot[i] * t) for i in range(3))
        for x in range(0, w, 4):
            for xx in range(x, min(x + 4, w)):
                px[xx, y] = col
    return im


def grano_sutil(im, color_acc, alpha=10):
    import random
    rng = random.Random(7)
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for _ in range(26):
        r = rng.randint(2, 7)
        x = rng.randint(0, im.width)
        y = rng.randint(0, im.height)
        d.ellipse((x - r, y - r, x + r, y + r), fill=color_acc + (alpha,))
    return Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")


# ------------------------------------------------------------ folleto genérico
def armar_folleto(ruta_salida, paleta, titulo, subtitulo, hero_path, miniaturas, features,
                   extra_titulo, extra_lineas, telefono, pie, hero_bias=0.22):
    fondo1, fondo2, dorado, panel, texto_c, gris = paleta
    alto = 3400  # lienzo generoso; se recorta al contenido real al final
    im = degrade_vertical(W, alto, fondo1, fondo2)
    im = grano_sutil(im, dorado, alpha=8)
    d = ImageDraw.Draw(im)

    y = 56
    y = texto_centrado(d, W / 2, y, titulo, 72, dorado) + 6
    y = texto_centrado(d, W / 2, y, subtitulo, 40, texto_c, bold=False) + 24
    d.rectangle((W / 2 - 160, y, W / 2 + 160, y + 6), fill=dorado)
    y += 34

    # foto principal: llena todo el recuadro, con el recorte sesgado hacia
    # arriba para no perder el techo/la puerta.
    hero_h = 720
    hero = fit_cover(Image.open(hero_path), W - 80, hero_h, bias_y=hero_bias)
    hero = redondear(hero, 28)
    pegar(im, hero, 40, y)
    y += hero_h + 26

    # grilla de miniaturas (3 columnas)
    cols = 3
    gap = 14
    cell_w = (W - 80 - gap * (cols - 1)) / cols
    cell_h = 220
    for i, mp in enumerate(miniaturas):
        cx = 40 + (i % cols) * (cell_w + gap)
        cy = y + (i // cols) * (cell_h + gap)
        th = fit_cover(Image.open(mp), int(cell_w), cell_h)
        th = redondear(th, 20)
        pegar(im, th, cx, cy)
    filas = -(-len(miniaturas) // cols)
    y += filas * (cell_h + gap) + 36

    # separador
    d.rectangle((40, y, W - 40, y + 2), fill=panel)
    y += 34

    # características
    y = texto_centrado(d, W / 2, y, "CARACTERÍSTICAS", 38, dorado) + 24
    for feat in features:
        y = bullet(d, 70, y, W - 70 - 60, feat, 34, texto_c, dorado) + 14
    y += 20

    # separador
    d.rectangle((40, y, W - 40, y + 2), fill=panel)
    y += 34

    y = texto_centrado(d, W / 2, y, extra_titulo, 38, dorado) + 24
    for ln in extra_lineas:
        y = bullet(d, 70, y, W - 70 - 60, ln, 32, gris, dorado) + 10
    y += 30

    # pie de características cortas
    lineas_pie, f_pie = envolver(d, pie, 28, W - 120, bold=False)
    for ln in lineas_pie:
        y = texto_centrado(d, W / 2, y, ln, 28, gris, bold=False) + 4
    y += 24

    # tarjeta de contacto
    cw, ch = W - 80, 190
    cx0, cy0 = 40, y
    d.rounded_rectangle((cx0, cy0, cx0 + cw, cy0 + ch), 36, fill=panel)
    icon_r = 62
    icx, icy = cx0 + 100, cy0 + ch / 2
    d.ellipse((icx - icon_r, icy - icon_r, icx + icon_r, icy + icon_r), fill=dorado)
    fi = fuente(58)
    bbox = d.textbbox((0, 0), "☎", font=fi)
    d.text((icx - (bbox[2] - bbox[0]) / 2, icy - (bbox[3] - bbox[1]) / 2 - bbox[1]), "☎", font=fi, fill=panel)
    f_tel = fuente(62)
    d.text((icx + icon_r + 36, icy - 24), telefono, font=f_tel, fill=(255, 255, 255))
    y = cy0 + ch + 40

    im = im.crop((0, 0, W, int(y)))
    im.save(ruta_salida, quality=92)
    print("Listo:", ruta_salida, im.size)


# ------------------------------------------------------------ paletas (iguales a los videos)
PALETA_CASA = ((36, 32, 27), (12, 11, 10), (203, 166, 86), (14, 13, 13), (236, 232, 224), (190, 186, 178))
PALETA_CABANA = ((26, 38, 28), (9, 14, 11), (196, 110, 61), (13, 16, 13), (238, 227, 203), (205, 198, 182))

F = "/tmp/folleto_frames"


def main():
    armar_folleto(
        OUT / "folleto_casa.jpg",
        PALETA_CASA,
        "PH EN VENTA",
        "Rivadavia 2647",
        f"{F}/casa_003.5.jpg",
        [f"{F}/casa_014.0.jpg", f"{F}/casa_037.5.jpg", f"{F}/casa_044.0.jpg",
         f"{F}/casa_067.0.jpg", f"{F}/casa_072.0.jpg", f"{F}/casa_083.0.jpg",
         f"{F}/casa_097.0.jpg"],
        ["2 dormitorios grandes", "Living comedor", "Cocina", "Living estar adicional",
         "Baño completo", "Lavadero propio", "Terraza"],
        "UBICACIÓN",
        ["A 50 m de Av. Francisco de Aguirre", "4 líneas de colectivos a la puerta",
         "Escuela a 100 m", "Todo tipo de comercios cerca"],
        "381 526 9004",
        "Consultanos por WhatsApp o llamada",
        hero_bias=0.47,
    )
    armar_folleto(
        OUT / "folleto_cabana.jpg",
        PALETA_CABANA,
        "CABAÑA EN VENTA",
        "Club de Campo Taficillo · Tafí Viejo",
        f"{F}/cabana_048.0.jpg",
        ["assets_cabana/01_living.webp", "assets_cabana/02_dormitorio.webp",
         "assets_cabana/03_piscina_dia.webp", "assets_cabana/04_piscina_atardecer.webp",
         "assets_cabana/05_piscina_noche.webp", f"{F}/cabana_027.5.jpg"],
        ["Living comedor y cocina integrados, con hogar a leña", "2 dormitorios", "Baño",
         "Galería al costado", "Lavadero", "2 cisternas de 1000 L con bomba",
         "Piscina 7 x 3 x 1,50 m con hidromasaje y cascada"],
        "TERRENO Y SERVICIOS",
        ["Terreno de 20 x 30 m", "Luz y WiFi", "Se entrega con escritura"],
        "381 585 9396",
        "Consultanos por WhatsApp o llamada",
    )


if __name__ == "__main__":
    main()
