"""Amplía con IA (Real-ESRGAN, CPU) los tramos elegidos y guarda cada cuadro como JPG (se puede reanudar).

python ampliar_tramos.py [parte nparte]   → procesa los cuadros i con i % nparte == parte
"""
import os
import sys

import cv2
import torch

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "forralitas_video_final", "proyecto"))
from upscale_ia import ampliar, cargar_modelo  # noqa: E402

# (nombre, archivo, desde (s), hasta (s))
TRAMOS = [
    ("llenado", "fuente/largo.mp4", 0.5, 8.4),     # parte 1 del video largo: llenando las bolsas
    ("pilas", "fuente/largo.mp4", 37.5, 46.5),     # parte 3 del video largo: pilas de bolsas
    ("calidad", "fuente/corto.mp4", 1.0, 7.0),     # video corto: el grano de cerca
]
ANCHO, ALTO = 1080, 1920


def cuadros_fuente(arch, a, b):
    cap = cv2.VideoCapture(os.path.join(AQUI, arch))
    fps = cap.get(cv2.CAP_PROP_FPS)
    i0, i1 = round(a * fps), round(b * fps)
    i = 0
    while True:
        ok, f = cap.read()
        if not ok or i >= i1:
            break
        if i >= i0:
            yield i - i0, f
        i += 1


def main():
    parte, n = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (0, 1)
    torch.set_num_threads(max(1, os.cpu_count() // n))
    net = cargar_modelo()
    for nombre, arch, a, b in TRAMOS:
        d = os.path.join(AQUI, "cache", nombre)
        os.makedirs(d, exist_ok=True)
        for j, f in cuadros_fuente(arch, a, b):
            if j % n != parte:
                continue
            p = os.path.join(d, f"{j:04d}.jpg")
            if os.path.exists(p):
                continue
            up = ampliar(net, cv2.cvtColor(f, cv2.COLOR_BGR2RGB))
            out = cv2.resize(up, (ANCHO, ALTO), interpolation=cv2.INTER_AREA)
            cv2.imwrite(p + ".tmp.jpg", cv2.cvtColor(out, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 95])
            os.replace(p + ".tmp.jpg", p)
            if j % 30 == parte:
                print(nombre, j, flush=True)
    print("listo parte", parte)


if __name__ == "__main__":
    main()
