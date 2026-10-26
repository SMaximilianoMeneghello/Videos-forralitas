"""Preparación del material (se corre una sola vez; los resultados quedan en cache/).

    python preparar.py

1. Upscaling con IA (Real-ESRGAN general x4v3) de los clips (480x864 → 1080x1944).
2. Upscaling con IA de las fotos de baja resolución.
3. Cámara lenta interpolada (minterpolate, 4x) de los tramos que van en slow motion.
Cada paso se saltea si su archivo ya existe.
"""
import os
import subprocess
import sys

import cv2
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
os.chdir(AQUI)
sys.path.insert(0, AQUI)
import upscale_ia  # noqa: E402

CLIPS = [  # (entrada, salida, desde, duración)
    ("material/clip1_maiz_tolva.mp4", "cache/clip1_ia.mp4", 0.0, None),
    ("material/clip3_manos_bolsa.mp4", "cache/clip3_ia.mp4", 1.5, 9.0),
]
FOTOS_BAJA = ["foto_bolsa_maiz.jpg", "foto_mano_punado.jpg", "foto_camion_galpon_a.jpg", "foto_camion_galpon_b.jpg"]
# tramos en cámara lenta: (video IA, salida, desde (s del video IA), duración)
LENTOS = [
    ("cache/clip1_ia.mp4", "cache/clip1_lento.mp4", 4.9, 2.1),     # granos cayendo de la mano
    ("cache/clip3_ia.mp4", "cache/clip3_lento.mp4", 4.6, 3.2),     # puñado (6.1–9.3 s del original)
]


def correr(cmd):
    print(">", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main():
    os.makedirs("cache", exist_ok=True)
    for ent, sal, ss, t in CLIPS:
        if not os.path.exists(sal) or os.path.getsize(sal) < 10000:
            args = [sys.executable, "upscale_ia.py", ent, sal, "--ss", str(ss)] + (["--t", str(t)] if t else [])
            correr(args)
    net = None
    for nombre in FOTOS_BAJA:
        sal = f"cache/ia_{nombre.replace('.jpg', '.png')}"
        if os.path.exists(sal):
            continue
        net = net or upscale_ia.cargar_modelo()
        rgb = cv2.cvtColor(cv2.imread(f"material/{nombre}"), cv2.COLOR_BGR2RGB)
        up = upscale_ia.ampliar(net, rgb)
        cv2.imwrite(sal, cv2.cvtColor(up, cv2.COLOR_RGB2BGR))
        print("foto IA:", sal, up.shape)
    for ent, sal, ss, t in LENTOS:
        if not os.path.exists(sal):
            correr(["ffmpeg", "-v", "error", "-y", "-ss", str(ss), "-t", str(t), "-i", ent, "-an", "-vf",
                    "minterpolate=fps=120:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1",
                    "-c:v", "libx264", "-crf", "12", "-preset", "medium", sal])
    print("preparación lista")


if __name__ == "__main__":
    main()
