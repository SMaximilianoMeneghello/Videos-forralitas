"""Flyer "Precios mayoristas" rehecho: mismo diseño y mismos precios del flyer original, pero con las fotos reales del proyecto
(nítidas, a 2048 x 3072) y el logo original en alta resolución.
Las fotos que el proyecto no tiene (avena, herraduras, clavos) se recortan del flyer original.

Uso (desde la raíz del repositorio):  python FORRALITAS/codigo/flyer_precios.py
"""
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

RAIZ = Path(__file__).resolve().parents[2]
PREP = RAIZ / "FORRALITAS/fotos_preparadas"
ORIG = RAIZ / "FORRALITAS/flyer/flyer_original.png"
SALIDA = RAIZ / "FORRALITAS/flyer"
S = 2                                           # el diseño está en 1024 x 1536; se dibuja al doble
F = "/usr/share/fonts/opentype/inter/"
NEGRA, EXTRA, SEMI = F + "InterDisplay-Black.otf", F + "InterDisplay-ExtraBold.otf", F + "InterDisplay-SemiBold.otf"
VERDE_OSC, VERDE, ORO, CREMA = (6, 54, 27), (11, 77, 35), (236, 178, 38), (252, 246, 228)


def fnt(ruta, tam):
    return ImageFont.truetype(ruta, int(tam * S))


def px(v):
    return int(round(v * S))


def redondo(w, h, r):
    m = Image.new("L", (px(w) * 3, px(h) * 3), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, px(w) * 3 - 1, px(h) * 3 - 1), px(r) * 3, fill=255)
    return m.resize((px(w), px(h)), Image.LANCZOS)


def recorte(img, w, h, fx=0.5, fy=0.5, zoom=1.0):
    """Recorta img a la proporción w:h alrededor del punto (fx, fy) y lo escala a (w, h) en px finales."""
    iw, ih = img.size
    ar = w / h
    cw = iw / zoom
    ch = cw / ar
    if ch > ih / zoom:
        ch = ih / zoom
        cw = ch * ar
    x0 = min(max(fx * iw - cw / 2, 0), iw - cw)
    y0 = min(max(fy * ih - ch / 2, 0), ih - ch)
    return img.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((w, h), Image.LANCZOS)


def texto_centrado(d, caja, txt, fuente, color, trazo=0, trazo_color=None):
    x0, y0, x1, y1 = caja
    b = d.textbbox((0, 0), txt, font=fuente, stroke_width=trazo)
    d.text(((x0 + x1) / 2 - (b[0] + b[2]) / 2, (y0 + y1) / 2 - (b[1] + b[3]) / 2), txt, font=fuente, fill=color,
           stroke_width=trazo, stroke_fill=trazo_color)


# (línea 1, línea 2, medida, precio, foto, punto de foco (x, y), zoom)   — foto: nombre en fotos_preparadas o ("flyer", caja)
ITEMS = [
    ("MAÍZ", "ENTERO", "40 kg", "$12.500", "maiz_entero", (0.5, 0.5), 1.5),
    ("MAÍZ", "ENTERO", "50 kg", "$15.500", "maiz_entero", (0.35, 0.3), 1.9),
    ("FARDO DE", "ALFA VERDE", "", "$6.000", "alfalfa_pila", (0.5, 0.45), 1.15),
    ("AVENA", "", "30 kg", "$15.500", ("flyer", (790, 430, 1012, 534)), None, 1),
    ("MEZCLA PARA", "CABALLO", "35 kg", "$14.500", "mezcla_caballo", (0.5, 0.5), 1.4),
    ("MAÍZ", "QUEBRADO", "40 kg", "$14.500", "maiz_quebrado", (0.5, 0.45), 1.5),
    ("AFRECHO", "DE MAÍZ", "40 kg", "$11.500", "afrecho_maiz", (0.5, 0.5), 1.3),
    ("AFRECHO", "DE TRIGO", "30 kg", "$6.500", "afrecho_trigo", (0.5, 0.5), 1.6),
    ("PELLET", "DE ALFA", "30 kg", "$13.500", "pellet_alfa", (0.5, 0.45), 1.5),
    ("PELLET", "DE TRIGO", "30 kg", "$13.000", "pellet_trigo", (0.5, 0.5), 1.3),
    ("HERRADURAS", "CORONA", "Juego de 4", "$16.200", ("flyer", (522, 858, 626, 990)), None, 1),
    ("HERRADURAS", "JK PLUS", "Juego de 4", "$18.000", ("flyer", (776, 858, 880, 990)), None, 1),
    ("CLAVOS PARA HERRAR", "", "E2 · E4 · E5 · E6", "$150 c/u", ("flyer", (6, 1088, 122, 1200)), None, 1),
    ("PIEDRA DE", "SAL ROSADA", "", "$9.500", "sal", (0.5, 0.42), 1.45),
    ("PIEDRA DE", "SAL GRIS", "", "$8.000", "sal_gris", (0.5, 0.5), 1.35),
    ("VIRUTA", "", "", "$6.000", "virutas", (0.5, 0.5), 1.5),
]


def foto_item(clave, foco, zoom, w, h, flyer):
    if isinstance(clave, tuple):
        x0, y0, x1, y1 = clave[1]
        arr = cv2.cvtColor(np.asarray(flyer.crop((x0, y0, x1, y1)).convert("RGB")), cv2.COLOR_RGB2BGR)
        esc = min(px(w) / arr.shape[1], px(h) / arr.shape[0])
        arr = cv2.resize(arr, (int(arr.shape[1] * esc), int(arr.shape[0] * esc)), interpolation=cv2.INTER_CUBIC)
        blur = cv2.GaussianBlur(arr, (0, 0), 2.0)
        arr = cv2.addWeighted(arr, 1.6, blur, -0.6, 0)
        base = Image.new("RGB", (px(w), px(h)), CREMA)
        im = Image.fromarray(cv2.cvtColor(arr, cv2.COLOR_BGR2RGB))
        base.paste(im, ((px(w) - im.width) // 2, (px(h) - im.height) // 2))
        return base
    im = Image.open(PREP / f"{clave}.jpg").convert("RGB")
    return recorte(im, px(w), px(h), foco[0], foco[1], zoom)


def main():
    flyer = Image.open(ORIG).convert("RGB")
    W, H = 1024 * S, 1536 * S
    lienzo = Image.new("RGB", (W, H), VERDE_OSC)

    # --- encabezado: el arte original (paisaje, gaucho y títulos) ampliado y afinado, con el logo real encima
    cab = flyer.crop((0, 0, 1024, 366))
    arr = cv2.cvtColor(np.asarray(cab), cv2.COLOR_RGB2BGR)
    arr = cv2.resize(arr, (W, px(366)), interpolation=cv2.INTER_CUBIC)
    arr = cv2.fastNlMeansDenoisingColored(arr, None, 3, 3, 5, 15)
    blur = cv2.GaussianBlur(arr, (0, 0), 2.4)
    arr = cv2.addWeighted(arr, 1.55, blur, -0.55, 0)
    lienzo.paste(Image.fromarray(cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)), (0, 0))
    logo = Image.open(RAIZ / "assets/logo.jpg").convert("RGB")
    lado = px(296)
    logo = logo.crop((55, 55, logo.width - 55, logo.height - 55)).resize((lado, lado), Image.LANCZOS)
    m = Image.new("L", (lado * 3, lado * 3), 0)
    ImageDraw.Draw(m).ellipse((0, 0, lado * 3 - 1, lado * 3 - 1), fill=255)
    m = m.resize((lado, lado), Image.LANCZOS)
    cx, cy = px(190), px(177)
    lienzo.paste(logo, (cx - lado // 2, cy - lado // 2), m)

    # --- cuadrícula de productos
    d = ImageDraw.Draw(lienzo)
    cw, chh, gap, x_ini, y_ini = 248, 224, 6, 6, 368
    for i, (l1, l2, med, precio, clave, foco, zoom) in enumerate(ITEMS):
        r, c = divmod(i, 4)
        x, y = x_ini + c * (cw + gap), y_ini + r * (chh + gap)
        tarjeta = Image.new("RGB", (px(cw), px(chh)), CREMA)
        lienzo.paste(tarjeta, (px(x), px(y)), redondo(cw, chh, 14))
        # foto
        fw, fh = cw - 12, 96
        im = foto_item(clave, foco, zoom, fw, fh, flyer)
        lienzo.paste(im, (px(x + 6), px(y + 6)), redondo(fw, fh, 10))
        # nombre y medida
        ty = y + 6 + fh + 3
        d.text((px(x + cw / 2), px(ty)), l1, font=fnt(EXTRA, 20 if len(l1) < 13 else 16), fill=VERDE_OSC, anchor="ma")
        if l2:
            d.text((px(x + cw / 2), px(ty + 21)), l2, font=fnt(EXTRA, 20), fill=VERDE_OSC, anchor="ma")
        if med:
            d.text((px(x + cw / 2), px(ty + (42 if l2 else 22))), med, font=fnt(SEMI, 17), fill=(70, 80, 60), anchor="ma")
        # precio
        py0 = y + chh - 50
        d.rounded_rectangle((px(x + 6), px(py0), px(x + cw - 6), px(y + chh - 6)), px(10), fill=VERDE_OSC)
        texto_centrado(d, (px(x + 6), px(py0), px(x + cw - 6), px(y + chh - 6)), precio, fnt(NEGRA, 40 if len(precio) < 8 else 34), (255, 255, 255))

    # --- pie
    fy0 = y_ini + 4 * (chh + gap) + 2
    d.rectangle((0, px(fy0), W, H), fill=VERDE_OSC)
    d.rectangle((0, px(fy0), W, px(fy0 + 3)), fill=ORO)
    # camión
    ox, oy = 58, fy0 + 100
    d.ellipse((px(ox - 46), px(oy - 46), px(ox + 46), px(oy + 46)), outline=ORO, width=px(4))
    d.rectangle((px(ox - 26), px(oy - 22), px(ox + 6), px(oy + 12)), fill=ORO)
    d.polygon([(px(ox + 9), px(oy - 12)), (px(ox + 24), px(oy - 12)), (px(ox + 34), px(oy)), (px(ox + 34), px(oy + 12)), (px(ox + 9), px(oy + 12))], fill=ORO)
    for wx in (ox - 14, ox + 22):
        d.ellipse((px(wx - 8), px(oy + 6), px(wx + 8), px(oy + 22)), fill=ORO, outline=VERDE_OSC, width=px(2))
    d.text((px(128), px(fy0 + 40)), "¡ENTREGA", font=fnt(NEGRA, 46), fill=ORO)
    d.text((px(128), px(fy0 + 86)), "A DOMICILIO!", font=fnt(NEGRA, 46), fill=ORO)
    d.text((px(128), px(fy0 + 142)), "Llegamos hasta tu campo", font=fnt(SEMI, 24), fill=(250, 244, 228))
    d.line((px(494), px(fy0 + 20), px(494), px(fy0 + 180)), fill=(80, 110, 80), width=px(2))
    # ubicación y teléfonos
    d.ellipse((px(520), px(fy0 + 26), px(548), px(fy0 + 54)), fill=ORO)
    d.text((px(562), px(fy0 + 21)), "Ruta 305 km 7,5 • Las Talitas", font=fnt(EXTRA, 30), fill=(255, 255, 255))
    for k, tel in enumerate(("381-526-9004", "381-633-4344")):
        yy = fy0 + 62 + k * 52
        d.ellipse((px(518), px(yy), px(566), px(yy + 48)), fill=(37, 190, 90))
        d.ellipse((px(528), px(yy + 10), px(556), px(yy + 38)), outline=(255, 255, 255), width=px(3))
        d.text((px(584), px(yy - 8)), tel, font=fnt(NEGRA, 52), fill=(255, 255, 255))
    d.line((px(40), px(fy0 + 218), px(200), px(fy0 + 218)), fill=ORO, width=px(2))
    d.line((px(824), px(fy0 + 218), px(984), px(fy0 + 218)), fill=ORO, width=px(2))
    d.text((px(512), px(fy0 + 218)), "CALIDAD EN FORRAJES Y ALIMENTOS PARA TUS ANIMALES", font=fnt(SEMI, 17), fill=(250, 244, 228), anchor="mm")

    lienzo.save(SALIDA / "FORRALITAS_PRECIOS_MAYORISTAS.png", optimize=True)
    lienzo.save(SALIDA / "FORRALITAS_PRECIOS_MAYORISTAS.jpg", quality=93, subsampling=0)
    print("listo", lienzo.size)


if __name__ == "__main__":
    main()
