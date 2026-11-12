"""Extrae el cuadro más nítido de cada montículo del video y lo amplía con IA (Real-ESRGAN).

    python preparar_cuadros.py   → cache/f6_ia.png (Calidad 1, $6.000) y cache/f5_ia.png (Calidad 2, $5.000)
"""
import os
import sys

import cv2

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "forralitas_video_final", "proyecto"))
import upscale_ia as u  # noqa: E402


def main():
    cap = cv2.VideoCapture(os.path.join(AQUI, "material", "video.mp4"))
    fr = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        fr.append(f)
    nit = lambda f: cv2.Laplacian(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()
    i6 = max(range(55, 75), key=lambda i: nit(fr[i]))      # ~2.5 s: los dos montículos del principio
    i5 = max(range(190, len(fr)), key=lambda i: nit(fr[i]))  # final: el último montículo
    net = u.cargar_modelo()
    os.makedirs(os.path.join(AQUI, "cache"), exist_ok=True)
    up = u.ampliar(net, cv2.cvtColor(fr[i6], cv2.COLOR_BGR2RGB))
    cv2.imwrite(os.path.join(AQUI, "cache", "f6_ia.png"),
                cv2.cvtColor(cv2.resize(up, (3840, 2160), interpolation=cv2.INTER_AREA), cv2.COLOR_RGB2BGR))
    sub = fr[i5][:, :1050]                                    # sin las bolsas de la derecha
    up = u.ampliar(net, cv2.cvtColor(sub, cv2.COLOR_BGR2RGB))
    cv2.imwrite(os.path.join(AQUI, "cache", "f5_ia.png"),
                cv2.cvtColor(cv2.resize(up, (2100, 2160), interpolation=cv2.INTER_AREA), cv2.COLOR_RGB2BGR))
    print("cuadros:", i6, i5)


if __name__ == "__main__":
    main()
