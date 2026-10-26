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

CLIPS = [  # (entrada, salida, desde, duración, tramos usados en segundos del original)
    ("material/clip1_maiz_tolva.mp4", "cache/clip1_ia.mp4", 0.0, None, [(0.0, 1.6), (4.85, 7.05)]),
    ("material/clip3_manos_bolsa.mp4", "cache/clip3_ia.mp4", 1.5, 9.0, [(2.0, 4.4), (6.0, 9.4), (10.15, 10.45)]),
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


def ampliar_clip(ent, sal, ss, t, tramos):
    """Amplía con IA solo los cuadros de los tramos usados, guardando cada cuadro (se puede retomar);
    el resto del clip se completa con Lanczos para mantener la línea de tiempo."""
    carpeta = sal.replace(".mp4", "_cuadros")
    os.makedirs(carpeta, exist_ok=True)
    cap = cv2.VideoCapture(ent)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    cuadros = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        cuadros.append(f)
    i0 = int(round(ss * fps))
    i1 = len(cuadros) if t is None else min(len(cuadros), i0 + int(round(t * fps)))
    usados = sorted({i for a, b in tramos for i in range(int(a * fps), int(b * fps) + 1) if i0 <= i < i1})
    net = upscale_ia.cargar_modelo()
    for n, i in enumerate(usados):
        ruta = f"{carpeta}/{i:05d}.png"
        if os.path.exists(ruta):
            continue
        rgb = cv2.cvtColor(cuadros[i], cv2.COLOR_BGR2RGB)
        up = cv2.resize(upscale_ia.ampliar(net, rgb), (1080, 1944), interpolation=cv2.INTER_AREA)
        cv2.imwrite(ruta + ".tmp.png", cv2.cvtColor(up, cv2.COLOR_RGB2BGR))
        os.replace(ruta + ".tmp.png", ruta)
        print(f"{sal}: {n + 1}/{len(usados)}", flush=True)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "1080x1944", "-r", str(fps),
           "-i", "-", "-c:v", "libx264", "-crf", "10", "-preset", "slow", "-pix_fmt", "yuv420p", sal + ".tmp.mp4"]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(i0, i1):
        ruta = f"{carpeta}/{i:05d}.png"
        f = cv2.imread(ruta) if os.path.exists(ruta) else cv2.resize(cuadros[i], (1080, 1944), interpolation=cv2.INTER_LANCZOS4)
        p.stdin.write(f.tobytes())
    p.stdin.close()
    p.wait()
    os.replace(sal + ".tmp.mp4", sal)
    print("clip listo:", sal)


def main():
    os.makedirs("cache", exist_ok=True)
    for ent, sal, ss, t, tramos in CLIPS:
        if not os.path.exists(sal) or os.path.getsize(sal) < 10000:
            ampliar_clip(ent, sal, ss, t, tramos)
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
