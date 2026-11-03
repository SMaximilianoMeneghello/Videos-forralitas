"""Corrección de color selectiva para la alfa: lleva los tonos amarillentos de los fardos hacia un verde
natural y les da más vida, sin tocar el suelo, la piel, el autoelevador, el camión rojo ni el cielo."""
import cv2
import numpy as np

# tonos en unidades de OpenCV (0-180 = 0-360°)
H_MIN, H_MAX = 15.0, 48.0        # rango de la alfa (amarillo verdoso)
H_OBJETIVO = 40.0                # ~80°: verde alfa
FUERZA_TONO = 0.75
SAT_EXTRA = 0.45
LUZ_EXTRA = 0.10


def _rampa(x, a, b):
    return np.clip((x - a) / (b - a), 0, 1)


def verde_lindo(rgb, fuerza=1.0):
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV).astype(np.float32)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    # máscara suave: dentro del rango de tono, con algo de saturación y sin ser casi negro
    m = _rampa(h, H_MIN, H_MIN + 5) * (1 - _rampa(h, H_MAX - 6, H_MAX))
    m *= _rampa(s, 18, 45) * _rampa(v, 25, 60) * (1 - _rampa(s, 125, 165))   # no toca amarillos intensos (autoelevador)
    m = cv2.GaussianBlur(m, (0, 0), 2.0) * fuerza
    h2 = h + m * FUERZA_TONO * np.clip(H_OBJETIVO - h, 0, None)
    s2 = np.clip(s * (1 + SAT_EXTRA * m), 0, 255)
    v2 = np.clip(v * (1 + LUZ_EXTRA * m), 0, 255)
    out = np.stack([h2, s2, v2], -1).astype(np.uint8)
    return cv2.cvtColor(out, cv2.COLOR_HSV2RGB)
