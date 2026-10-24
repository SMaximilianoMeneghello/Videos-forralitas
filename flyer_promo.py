"""Flyer de precios mayoristas con el diseño "promo": fila grande de bolsas arriba, grilla "También tenemos"
y pie con entrega a domicilio.

Uso:  python flyer_promo.py     ->  flyer/flyer_promo_mayorista.jpg  (2048 x 3072)

Productos y precios: lista HERO y GRILLA (abajo). Fotos reales en fotos_presentacion/, assets/ y flyer/.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

from efectos import icono

W, H = 2048, 3072
INTER = "/usr/share/fonts/opentype/inter/"
BLK, XB, SB = INTER + "Inter-Black.otf", INTER + "Inter-ExtraBold.otf", INTER + "Inter-SemiBold.otf"
SERIF_BI = "/usr/share/fonts/truetype/crosextra/Caladea-BoldItalic.ttf"
PAPEL = (243, 232, 208)
CREMA = (253, 247, 230)
VERDE, VERDE_OSC = (24, 70, 40), (14, 44, 25)
MADERA, MADERA_OSC = (112, 74, 40), (70, 45, 24)
AMARILLO, TINTA = (247, 196, 52), (24, 44, 30)
SALIDA = "flyer/flyer_promo_mayorista.jpg"

# nombre (2 líneas), precio, tipo de imagen, ruta
HERO = [
    (("MAÍZ ENTERO", "40 KG"), "$12.500", "bolsa", "assets/bolsas/maiz40_gc.png"),
    (("MAÍZ ENTERO", "50 KG"), "$15.500", "bolsa", "assets/bolsas/maiz50_gc.png"),
    (("FARDO DE", "ALFA VERDE"), "$6.000", "foto", "assets/nuevas/n08.jpg"),
    (("AVENA", "30 KG"), "$15.500", "bolsa", "assets/bolsas/avena_gc.png"),
    (("MEZCLA PARA", "CABALLO 35 KG"), "$14.500", "bolsa", "assets/bolsas/mezcla_gc.png"),
]
P = "fotos_presentacion/"
PESOS = {1: [0.27, 0.27, 0.46]}
GRILLA = [
    [("MAÍZ QUEBRADO", "40 KG", "$14.500", "foto", P + "06_maiz_quebrado.jpg"),
     ("AFRECHO DE MAÍZ", "40 KG", "$11.500", "foto", P + "09_afrecho_maiz.jpg"),
     ("AFRECHO DE TRIGO", "30 KG", "$6.500", "foto", P + "08_afrecho_trigo.jpg")],
    [("PELLET DE ALFA", "30 KG", "$13.500", "foto", P + "04_pellet_alfa.jpg"),
     ("PELLET DE TRIGO", "30 KG", "$13.000", "foto", P + "07_pellet_trigo.jpg"),
     "HERRADURAS"],
    [("CLAVOS PARA HERRAR", "E2 · E4 · E5 · E6", "$150 c/u", "clavos", None),
     ("PIEDRA DE SAL ROSADA", "", "$9.500", "sal_rosada", "assets/flyer/sal_cilindro.png"),
     ("PIEDRA DE SAL GRIS", "", "$8.000", "sal_gris", "assets/flyer/sal_bloque_rosada.png"),
     ("VIRUTA", "", "$6.000", "foto", P + "14_virutas.jpg")],
]


# ------------------------------------------------------------ utilidades
def f(ruta, tam):
    return ImageFont.truetype(ruta, tam)


def mascara_redonda(w, h, r, ss=3):
    m = Image.new("L", (w * ss, h * ss), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w * ss - 1, h * ss - 1), r * ss, fill=255)
    return m.resize((w, h), Image.LANCZOS)


def caja(img, xy, r, fill, borde=None, ancho=0):
    x0, y0, x1, y1 = xy
    w, h = x1 - x0, y1 - y0
    capa = Image.new("RGB", (w, h), borde or fill)
    img.paste(capa, (x0, y0), mascara_redonda(w, h, r))
    if borde and ancho:
        interior = Image.new("RGB", (w - 2 * ancho, h - 2 * ancho), fill)
        img.paste(interior, (x0 + ancho, y0 + ancho), mascara_redonda(w - 2 * ancho, h - 2 * ancho, max(r - ancho, 1)))


def sombra(img, alfa_img, x, y, off=(10, 16), blur=14, op=0.38):
    a = alfa_img.getchannel("A")
    pad = blur * 3
    s = Image.new("L", (a.width + 2 * pad, a.height + 2 * pad), 0)
    s.paste(a, (pad, pad))
    s = s.filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * op))
    img.paste(Image.new("RGB", s.size, (70, 50, 30)), (x - pad + off[0], y - pad + off[1]), s)


def texto_c(d, xy, txt, fuente, color, ancla="mm"):
    d.text(xy, txt, font=fuente, fill=color, anchor=ancla)


def ajustar(d, txt, ruta, tam, max_w, minimo=24):
    while d.textlength(txt, font=f(ruta, tam)) > max_w and tam > minimo:
        tam -= 2
    return f(ruta, tam)


def envolver(d, txt, ruta, tam, max_w, max_lineas=3, minimo=30):
    """Parte `txt` en líneas que entren en max_w, achicando la letra si hace falta."""
    pal = txt.split()
    while True:
        fu = f(ruta, tam)
        lineas, act = [], ""
        for p in pal:
            prueba = (act + " " + p).strip()
            if d.textlength(prueba, font=fu) <= max_w:
                act = prueba
            else:
                if act:
                    lineas.append(act)
                act = p
        lineas.append(act)
        ok = len(lineas) <= max_lineas and all(d.textlength(l, font=fu) <= max_w for l in lineas)
        if ok or tam <= minimo:
            return fu, lineas
        tam -= 2


def foto_cuadrada(ruta, lado, foco=(0.5, 0.5), borde=7):
    src = Image.open(ruta).convert("RGB")
    s = min(src.size)
    cx, cy = int(src.width * foco[0]), int(src.height * foco[1])
    x0 = min(max(cx - s // 2, 0), src.width - s)
    y0 = min(max(cy - s // 2, 0), src.height - s)
    c = src.crop((x0, y0, x0 + s, y0 + s)).resize((lado, lado), Image.LANCZOS)
    c = ImageEnhance.Contrast(ImageEnhance.Color(c).enhance(1.06)).enhance(1.04).filter(ImageFilter.UnsharpMask(1.4, 50, 2))
    out = Image.new("RGBA", (lado + 2 * borde, lado + 2 * borde), (0, 0, 0, 0))
    marco = Image.new("RGB", out.size, (255, 252, 242))
    out.paste(marco, (0, 0), mascara_redonda(out.width, out.height, 34))
    out.paste(c, (borde, borde), mascara_redonda(lado, lado, 28))
    return out


def foto_vertical(ruta, w, h, borde=8):
    src = Image.open(ruta).convert("RGB")
    esc = max(w / src.width, h / src.height)
    src = src.resize((int(src.width * esc) + 1, int(src.height * esc) + 1), Image.LANCZOS)
    x0, y0 = (src.width - w) // 2, int((src.height - h) * 0.92)
    c = src.crop((x0, y0, x0 + w, y0 + h))
    c = ImageEnhance.Contrast(ImageEnhance.Color(c).enhance(1.08)).enhance(1.05).filter(ImageFilter.UnsharpMask(1.4, 50, 2))
    out = Image.new("RGBA", (w + 2 * borde, h + 2 * borde), (0, 0, 0, 0))
    out.paste(Image.new("RGB", out.size, (255, 252, 242)), (0, 0), mascara_redonda(out.width, out.height, 40))
    out.paste(c, (borde, borde), mascara_redonda(w, h, 34))
    return out


def recorte(ruta, alto=None, ancho=None, gris=False):
    p = Image.open(ruta).convert("RGBA") if isinstance(ruta, str) else ruta
    bb = p.getchannel("A").point(lambda v: 255 if v > 20 else 0).getbbox()
    p = p.crop(bb)
    if gris:                       # el bloque salió rosado en la foto pero es gris
        rgb = np.asarray(p.convert("RGB")).astype(np.float32)
        L = np.clip((0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2] - 30) * 0.62 + 55, 0, 255)
        g = Image.fromarray(np.clip(np.stack([L + 3, L + 1, L - 2], -1), 0, 255).astype(np.uint8)).convert("RGBA")
        g.putalpha(p.getchannel("A"))
        p = g
    esc = min((alto or 10 ** 6) / p.height, (ancho or 10 ** 6) / p.width)
    p = p.resize((max(1, int(p.width * esc)), max(1, int(p.height * esc))), Image.LANCZOS)
    p.putalpha(p.getchannel("A").filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.9)))
    return p


def clavos_recortados():
    """Los clavos vienen en una imagen sobre fondo crema: se separa el fondo por color."""
    base = Image.open("flyer/flyer_original.jpg").convert("RGB").crop((24, 2128, 496, 2320))
    a = np.asarray(base).astype(int)
    dist = np.abs(a - np.array(CREMA)).sum(2)
    m = (dist > 55).astype(np.uint8) * 255
    mi = Image.fromarray(m).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.2))
    rgba = base.convert("RGBA")
    rgba.putalpha(mi)
    return rgba


def herraduras_foto(lado):
    src = Image.open("assets/flyer/herraduras_corona.jpg").convert("RGB").rotate(90, expand=True)
    c = src.crop((1250, 380, 3350, 2480)).resize((lado, lado), Image.LANCZOS)
    c = ImageEnhance.Contrast(ImageEnhance.Color(c).enhance(1.06)).enhance(1.04).filter(ImageFilter.UnsharpMask(1.4, 50, 2))
    borde = 7
    out = Image.new("RGBA", (lado + 2 * borde, lado + 2 * borde), (0, 0, 0, 0))
    out.paste(Image.new("RGB", out.size, (255, 252, 242)), (0, 0), mascara_redonda(out.width, out.height, 34))
    out.paste(c, (borde, borde), mascara_redonda(lado, lado, 28))
    return out


# ------------------------------------------------------------ fondo y encabezado
def fondo():
    rng = np.random.default_rng(4)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.hypot(xx - W / 2, yy - H / 2) / np.hypot(W / 2, H / 2)
    base = np.array(PAPEL, np.float32) * (1 - 0.10 * r ** 2)[..., None]
    ruido = rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
    ruido = np.asarray(Image.fromarray(ruido).resize((W, H), Image.BICUBIC))
    return Image.fromarray(np.clip(base + ruido[..., None] * 2.6, 0, 255).astype(np.uint8))


def encabezado(img):
    hd = Image.open("flyer/flyer_corregido_3.jpg").convert("RGB").crop((0, 0, W, 706))
    img.paste(hd, (0, 0))
    # desvanece el borde inferior hacia el papel
    fade = 46
    a = np.asarray(img).astype(np.float32)
    papel = np.asarray(fondo_cache).astype(np.float32)
    t = np.linspace(0, 1, fade)[:, None, None]
    zona = slice(706 - fade, 706)
    a[zona] = a[zona] * (1 - t) + papel[zona] * t
    img.paste(Image.fromarray(a.astype(np.uint8)))


# ------------------------------------------------------------ fila grande de bolsas
def fila_hero(img, d):
    y_art, alto_art = 760, 560
    ancho_col = (W - 80) / len(HERO)
    for i, (nombre, precio, tipo, ruta) in enumerate(HERO):
        cx = int(40 + ancho_col * (i + 0.5))
        if tipo == "bolsa":
            p = recorte(ruta, alto=alto_art, ancho=int(ancho_col - 30))
        else:
            p = foto_vertical(ruta, int(ancho_col - 70), alto_art - 30)
        x, y = cx - p.width // 2, y_art + alto_art - p.height
        # sombra de contacto en el piso
        el = Image.new("L", (p.width + 80, 60), 0)
        ImageDraw.Draw(el).ellipse((20, 14, p.width + 60, 46), fill=120)
        el = el.filter(ImageFilter.GaussianBlur(11))
        img.paste(Image.new("RGB", el.size, (70, 50, 30)), (x - 40, y_art + alto_art - 34), el)
        sombra(img, p, x, y, off=(8, 10), blur=12, op=0.30)
        img.paste(p, (x, y), p)
        # cartel de precio
        tw, th = int(ancho_col - 36), 232
        x0, y0 = cx - tw // 2, y_art + alto_art + 24
        caja(img, (x0 + 4, y0 + 8, x0 + tw + 4, y0 + th + 8), 30, (170, 150, 120))
        caja(img, (x0, y0, x0 + tw, y0 + th), 30, VERDE_OSC, borde=(230, 205, 120), ancho=3)
        for k, linea in enumerate(nombre):
            fu = ajustar(d, linea, XB, 44, tw - 40)
            texto_c(d, (cx, y0 + 40 + k * 50), linea, fu, (236, 244, 232))
        fu = ajustar(d, precio, BLK, 106, tw - 30)
        texto_c(d, (cx, y0 + 168), precio, fu, (255, 255, 255))


# ------------------------------------------------------------ "También tenemos"
def banner_tambien(img, d, y):
    x0, x1 = 56, 800
    poli = [(x0, y), (x1 - 34, y), (x1, y + 38), (x1 - 34, y + 76), (x0, y + 76)]
    sombra_p = Image.new("L", (W, 120), 0)
    img_s = Image.new("RGB", img.size)
    caja(img, (x0 + 4, y + 8, x1 - 24, y + 84), 8, (150, 125, 90))
    capa = Image.new("L", (W, 90), 0)
    ImageDraw.Draw(capa).polygon([(px, py - y) for px, py in poli], fill=255)
    rng = np.random.default_rng(9)
    gr = np.clip(np.array(MADERA, np.float32)[None, None, :] + rng.normal(0, 7, (90, W, 1)) +
                 np.sin(np.arange(W)[None, :, None] / 38.0 + rng.normal(0, 0.4, (90, 1, 1))) * 6, 0, 255).astype(np.uint8)
    img.paste(Image.fromarray(gr), (0, y), capa)
    texto_c(d, (x0 + 30, y + 40), "TAMBIÉN TENEMOS:", f(BLK, 50), (250, 238, 212), ancla="lm")


def celda_texto(d, x, y, w, h, nombre, detalle, precio):
    """Nombre en 1-3 líneas, detalle y precio, centrado verticalmente en la celda."""
    fu, lineas = envolver(d, nombre, XB, 46, w, 3, 30)
    tam_n = fu.size
    alto = len(lineas) * int(tam_n * 1.12) + (int(tam_n * 0.95) if detalle else 0) + 96
    ty = y + (h - alto) // 2
    for l in lineas:
        d.text((x, ty), l, font=fu, fill=VERDE, anchor="la")
        ty += int(tam_n * 1.12)
    if detalle:
        fd = ajustar(d, detalle, SB, 38, w)
        d.text((x, ty + 2), detalle, font=fd, fill=(70, 80, 66), anchor="la")
        ty += int(tam_n * 0.95)
    fp = ajustar(d, precio, BLK, 84, w)
    d.text((x, ty + 8), precio, font=fp, fill=TINTA, anchor="la")


def grilla(img, d, y0, y1):
    x0, x1 = 56, W - 56
    caja(img, (x0 + 4, y0 + 8, x1 + 4, y1 + 8), 26, (176, 156, 124))
    caja(img, (x0, y0, x1, y1), 26, CREMA, borde=(150, 128, 94), ancho=4)
    filas = len(GRILLA)
    alto_f = (y1 - y0) / filas
    linea = (205, 190, 160)
    for r, fila in enumerate(GRILLA):
        yy0 = int(y0 + r * alto_f)
        if r > 0:
            d.line((x0 + 22, yy0, x1 - 22, yy0), fill=linea, width=3)
        n = len(fila)
        pesos = PESOS.get(r, [1] * n)
        tot = sum(pesos)
        bordes = [x0 + (x1 - x0) * sum(pesos[:k]) / tot for k in range(n + 1)]
        for c, cel in enumerate(fila):
            xx0, ancho_c = int(bordes[c]), bordes[c + 1] - bordes[c]
            if c > 0:
                d.line((xx0, yy0 + 24, xx0, int(yy0 + alto_f - 24)), fill=linea, width=3)
            lado = int(alto_f - 70) if n == 3 else int(alto_f - 98)
            cx_img = xx0 + 30 + lado // 2
            cy_img = int(yy0 + alto_f / 2)
            ancho_txt = int(ancho_c - lado - 30 - 46 - 24)
            if cel == "HERRADURAS":
                ph = herraduras_foto(lado)
                sombra(img, ph, cx_img - ph.width // 2, cy_img - ph.height // 2, off=(6, 10), blur=10, op=0.30)
                img.paste(ph, (cx_img - ph.width // 2, cy_img - ph.height // 2), ph)
                tx = xx0 + 30 + lado + 36
                d.text((tx, yy0 + 30), "HERRADURAS", font=f(XB, 48), fill=VERDE, anchor="la")
                d.text((tx + d.textlength("HERRADURAS", font=f(XB, 48)) + 18, yy0 + 38), "(juego de 4)", font=f(SB, 32),
                       fill=(70, 80, 66), anchor="la")
                for k, (marca, precio) in enumerate((("CORONA", "$16.200"), ("JK PLUS", "$18.000"))):
                    yk = yy0 + 110 + k * 92
                    d.text((tx, yk + 40), marca, font=f(XB, 46), fill=VERDE, anchor="lm")
                    d.text((tx + ancho_txt, yk + 40), precio, font=f(BLK, 80), fill=TINTA, anchor="rm")
                    if k == 0:
                        d.line((tx, yk + 84, tx + ancho_txt, yk + 84), fill=(205, 190, 160), width=3)
                continue
            nombre, detalle, precio, tipo, ruta = cel
            if tipo == "foto":
                p = foto_cuadrada(ruta, lado)
            elif tipo == "clavos":
                p = recorte(clavos_recortados(), alto=lado, ancho=lado + 20)
            else:
                p = recorte(ruta, alto=lado, ancho=lado, gris=(tipo == "sal_gris"))
            px, py = cx_img - p.width // 2, cy_img - p.height // 2
            sombra(img, p, px, py, off=(6, 10), blur=10, op=0.30)
            img.paste(p, (px, py), p)
            celda_texto(d, xx0 + 30 + lado + 36, yy0, ancho_txt, alto_f, nombre, detalle, precio)


# ------------------------------------------------------------ pie
def pie(img, d, y0):
    y_f = H - 84
    # franja inferior
    d.rectangle((0, y_f, W, H), fill=MADERA_OSC)
    texto_c(d, (W / 2, y_f + 42), "★  CALIDAD EN FORRAJES Y ALIMENTACIÓN PARA TUS ANIMALES  ★",
            ajustar(d, "★  CALIDAD EN FORRAJES Y ALIMENTACIÓN PARA TUS ANIMALES  ★", BLK, 42, W - 120), (250, 238, 212))
    # bloque verde (entrega)
    d.rectangle((0, y0, 1060, y_f), fill=VERDE_OSC)
    d.rectangle((0, y0, 1060, y0 + 8), fill=(230, 190, 70))
    ic = icono("camion", 250, (250, 247, 235), VERDE_OSC)
    ic_img = Image.fromarray((ic[..., :3] / np.maximum(ic[..., 3:4], 1e-3)).clip(0, 255).astype(np.uint8))
    ic_a = Image.fromarray((ic[..., 3] * 255).clip(0, 255).astype(np.uint8))
    img.paste(ic_img, (70, y0 + (y_f - y0 - 250) // 2 + 6), ic_a)
    fe = ajustar(d, "A DOMICILIO!", BLK, 104, 640)
    d.text((350, y0 + 96), "¡ENTREGA", font=fe, fill=AMARILLO, anchor="ls")
    d.text((350, y0 + 96 + int(fe.size * 1.04)), "A DOMICILIO!", font=fe, fill=AMARILLO, anchor="ls")
    d.text((352, y0 + 282), "Llegamos hasta tu campo", font=ajustar(d, "Llegamos hasta tu campo", SERIF_BI, 56, 660), fill=(245, 236, 214), anchor="ls")
    # bloque crema (dirección y teléfonos)
    d.rectangle((1060, y0, W, y_f), fill=(238, 226, 198))
    d.rectangle((1060, y0, W, y0 + 8), fill=(230, 190, 70))
    pin = icono("ubicacion", 84, VERDE_OSC, (238, 226, 198))
    pa = Image.fromarray((pin[..., 3] * 255).clip(0, 255).astype(np.uint8))
    pi = Image.fromarray((pin[..., :3] / np.maximum(pin[..., 3:4], 1e-3)).clip(0, 255).astype(np.uint8))
    img.paste(pi, (1100, y0 + 50), pa)
    d.text((1208, y0 + 92), "RUTA 305 KM 7,5 - LAS TALITAS", font=ajustar(d, "RUTA 305 KM 7,5 - LAS TALITAS", BLK, 62, 790),
           fill=VERDE_OSC, anchor="lm")
    for k, num in enumerate(("381-526-9004", "381-633-4344")):
        cy = y0 + 188 + k * 102
        wa = icono("telefono", 86, (37, 190, 96), (255, 255, 255))
        wa_a = Image.fromarray((wa[..., 3] * 255).clip(0, 255).astype(np.uint8))
        wa_i = Image.fromarray((wa[..., :3] / np.maximum(wa[..., 3:4], 1e-3)).clip(0, 255).astype(np.uint8))
        img.paste(wa_i, (1100, cy - 43), wa_a)
        d.text((1214, cy), num, font=f(BLK, 96), fill=VERDE_OSC, anchor="lm")


def main():
    global fondo_cache
    fondo_cache = fondo()
    img = fondo_cache.copy()
    encabezado(img)
    d = ImageDraw.Draw(img)
    fila_hero(img, d)
    d = ImageDraw.Draw(img)
    banner_tambien(img, d, 1630)
    d = ImageDraw.Draw(img)
    grilla(img, d, 1730, 2650)
    d = ImageDraw.Draw(img)
    pie(img, d, 2664)
    img.save(SALIDA, quality=95, subsampling=0)
    print("Listo:", SALIDA, img.size)


if __name__ == "__main__":
    main()
