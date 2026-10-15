"""Mejora fotos de celular/cámara con poca luz: quita ruido, aclara, da contraste y color, afila y sube la resolución.

Uso: python mejorar_fotos.py entrada.jpg salida.jpg [escala]
"""
import sys

import cv2
import numpy as np


def mejorar(im, escala=2.0, brillo=1.0, color=1.18):
    im = cv2.fastNlMeansDenoisingColored(im, None, 5, 5, 7, 21)
    lab = cv2.cvtColor(im, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    # aclara las zonas oscuras sin quemar las claras
    lf = l.astype(np.float32) / 255
    gamma = 0.72 / brillo
    lf = lf ** gamma
    l = np.clip(lf * 255, 0, 255).astype(np.uint8)
    l = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8, 8)).apply(l)
    im = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[..., 1] = np.clip(hsv[..., 1] * color, 0, 255)
    im = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    if escala != 1:
        im = cv2.resize(im, None, fx=escala, fy=escala, interpolation=cv2.INTER_LANCZOS4)
    blur = cv2.GaussianBlur(im, (0, 0), 2.0)
    return cv2.addWeighted(im, 1.6, blur, -0.6, 0)


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    cv2.imwrite(dst, mejorar(cv2.imread(src), float(sys.argv[3]) if len(sys.argv) > 3 else 2.0), [cv2.IMWRITE_JPEG_QUALITY, 95])
