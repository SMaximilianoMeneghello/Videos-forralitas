"""Prepara las imágenes de Alma de Mujer a partir de las capturas de los estados de WhatsApp.

Uso:
    python alma_prep.py CARPETA_CON_CAPTURAS

Recorta la foto de cada captura (sin la interfaz de WhatsApp) y la guarda en assets/alma/fotos/.
Del flyer "Buenos días" saca el logo como máscara (assets/alma/logo_mascara.png) y del sticker
"Entrega inmediata" saca el círculo con fondo transparente (assets/alma/entrega_inmediata.png).
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

A = Path(__file__).parent / "assets/alma"

# captura -> nombre de la foto recortada
FOTOS = {
    "32e488a5": "conjunto_blanco_rojo",
    "bfa967e6": "conjunto_crema_fucsia",
    "b392c429": "armado_verde",
    "28731cb8": "colaless_lunares",
    "f738170f": "armado_morley",
    "3529c021": "colaless_estampadas",
    "add0eec8": "colaless_lunares_2",
    "6a1a7ecd": "armado_negro",
    "b7d448af": "regulables_algodon",
    "f93e738b": "armado_durazno",
    "52cba0e5": "armado_celeste",
    "ffd8bc85": "armados_varios",
    "d5429622": "conjunto_negro_flores",
    "bbb94d09": "regulables_elastico_ancho",
}
LOGO = "305630e6"
ENTREGA = "e8a76ffd"
CAJA_FOTO = (4, 502, 1076, 1933)      # zona de la foto en las capturas 1080x2436


def buscar(carpeta, clave):
    return next(Path(carpeta).glob(f"{clave}*"))


def logo_mascara(carpeta):
    im = np.asarray(Image.open(buscar(carpeta, LOGO)).convert("L"), np.float32)
    im = im[680:1044, 226:872]
    fondo = cv2.GaussianBlur(cv2.dilate(im, np.ones((31, 31), np.uint8)), (0, 0), 12)
    a = np.clip((fondo - im - 10) / 72, 0, 1)
    a[a < 0.08] = 0
    # quita restos de las flores del borde izquierdo
    a[:220, :62] = 0
    a[:, :7] = 0
    izq = a[:, :70]
    izq[izq < 0.4] = 0
    n, lab, stats, _ = cv2.connectedComponentsWithStats((a > 0.3).astype(np.uint8))
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] < 25:
            a[lab == i] = 0
    a = cv2.resize(a, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).save(A / "logo_mascara.png")


def entrega(carpeta):
    im = Image.open(buscar(carpeta, ENTREGA)).convert("RGB").crop((26, 698, 1050, 1722))
    yy, xx = np.mgrid[:1024, :1024]
    d = np.hypot(xx - 512, yy - 510)
    a = np.clip((511 - d) / 2.5, 0, 1)
    rgba = np.dstack([np.asarray(im), (a * 255).astype(np.uint8)])
    Image.fromarray(rgba, "RGBA").save(A / "entrega_inmediata.png")


def main(carpeta):
    (A / "fotos").mkdir(parents=True, exist_ok=True)
    for clave, nombre in FOTOS.items():
        Image.open(buscar(carpeta, clave)).convert("RGB").crop(CAJA_FOTO).save(
            A / "fotos" / f"{nombre}.jpg", quality=95)
    logo_mascara(carpeta)
    entrega(carpeta)
    print("Listo:", A)


if __name__ == "__main__":
    main(sys.argv[1])
