"""Copia las fotos originales elegidas a FORRALITAS/fotos_originales (sin tocarlas) y genera la versión
preparada para video en FORRALITAS/fotos_preparadas: tamaño ≤ 2400 px, contraste local suave y nitidez.
No cambia colores ni el aspecto real del producto (sin saturación extra).

Uso (desde la raíz del repositorio):  python FORRALITAS/codigo/preparar_fotos.py
"""
import shutil
from pathlib import Path

import cv2
import numpy as np

RAIZ = Path(__file__).resolve().parents[2]
ORIG, PREP = RAIZ / "FORRALITAS/fotos_originales", RAIZ / "FORRALITAS/fotos_preparadas"

# nombre de trabajo -> foto original del proyecto
FOTOS = {
    "maiz_entero": "fotos_presentacion/05_maiz_entero.jpg",
    "maiz_quebrado": "fotos_presentacion/06_maiz_quebrado.jpg",
    "alfalfa": "assets/nuevas/n08.jpg",
    "alfalfa_fardos": "fotos_presentacion/01_alfa.jpg",
    "alfalfa_pila": "fotos/03_alfa.jpg",
    "pellet_alfa": "fotos_presentacion/04_pellet_alfa.jpg",
    "pellet_trigo": "fotos_presentacion/07_pellet_trigo.jpg",
    "mezcla_caballo": "fotos_presentacion/03_mezcla_caballo.jpg",
    "mezcla_caballo2": "assets/nuevas/n10.jpg",
    "cerdo_mezcla": "fotos_presentacion/02_engorde_cerdo.jpg",
    "ponedora": "fotos_presentacion/10_ponedora.jpg",
    "afrecho_trigo": "fotos_presentacion/08_afrecho_trigo.jpg",
    "afrecho_maiz": "assets/nuevas/n13.jpg",
    "perros_sabrositos": "fotos/01_perros_sabrositos.jpg",
    "perros_gatos": "fotos/02_perros_gatos.jpg",
    "perro_gato_sacos": "fotos_presentacion/13_perro_gato.jpg",
    "sal": "fotos/05_sal_lamer.jpg",
    "virutas": "fotos_presentacion/14_virutas.jpg",
    "galpon_1": "assets/nuevas/n05.png",
    "galpon_2": "assets/nuevas/n06.png",
    "fachada": "assets/nuevas/n04.png",
    "gallina": "assets/nuevas/n01.png",
    "cerdo": "assets/nuevas/n02.png",
    "caballo": "assets/nuevas/n03.png",
    "dron_1": "assets/dron/dron1.jpg",
    "dron_2": "assets/dron/dron2.jpg",
}


def preparar(im, largo=2400):
    h, w = im.shape[:2]
    s = largo / max(h, w)
    if s < 1:
        im = cv2.resize(im, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    lab = cv2.cvtColor(im, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    l = cv2.createCLAHE(clipLimit=1.4, tileGridSize=(8, 8)).apply(l)
    im = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)
    blur = cv2.GaussianBlur(im, (0, 0), 1.6)
    return cv2.addWeighted(im, 1.35, blur, -0.35, 0)


def main():
    ORIG.mkdir(parents=True, exist_ok=True)
    PREP.mkdir(parents=True, exist_ok=True)
    for nombre, ruta in FOTOS.items():
        src = RAIZ / ruta
        shutil.copy2(src, ORIG / f"{nombre}{src.suffix.lower()}")
        im = cv2.imread(str(src))
        out = preparar(im, 2400 if im.shape[1] > 1500 or im.shape[0] > 1500 else max(im.shape[:2]))
        cv2.imwrite(str(PREP / f"{nombre}.jpg"), out, [cv2.IMWRITE_JPEG_QUALITY, 94])
        print(nombre, im.shape[1], "x", im.shape[0], "->", out.shape[1], "x", out.shape[0])


if __name__ == "__main__":
    main()
