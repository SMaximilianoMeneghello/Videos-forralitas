"""Piezas comunes de los dos videos de maíz: tramos de video (ampliados con IA) y acceso a la base de categorías."""
import os
import sys

import cv2
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "forralitas_categorias"))
import base  # noqa: E402

base.SALIDA = os.path.join(AQUI, "videos")
W, H, FPS = base.W, base.H, base.FPS
MUSICA = os.path.join(AQUI, "musica")

# mismos tramos que ampliar_tramos.py
TRAMOS = {
    "llenado": ("fuente/largo.mp4", 0.5, 8.4),     # parte 1 del video largo: llenando las bolsas
    "pilas": ("fuente/largo.mp4", 37.5, 46.5),     # parte 3: pilas de bolsas en el depósito
    "calidad": ("fuente/corto.mp4", 1.0, 7.0),     # video corto: el grano de cerca
}


class Tramo:
    """Cuadros 1080x1920 del tramo: los ampliados con IA (cache/<nombre>/NNNN.jpg) o, si faltan, Lanczos."""

    def __init__(self, nombre):
        self.nombre = nombre
        arch, a, b = TRAMOS[nombre]
        self.n = int(round((b - a) * FPS))
        self.dur = self.n / FPS
        self.dir = os.path.join(AQUI, "cache", nombre)
        self._fuente = None
        self._a = a
        self._arch = os.path.join(AQUI, arch)
        self._ult = (None, None)

    def _lanczos(self, i):
        if self._fuente is None:
            cap = cv2.VideoCapture(self._arch)
            cap.set(cv2.CAP_PROP_POS_MSEC, self._a * 1000)
            self._fuente = []
            for _ in range(self.n):
                ok, f = cap.read()
                if not ok:
                    break
                self._fuente.append(f)
        f = self._fuente[min(i, len(self._fuente) - 1)]
        f = cv2.resize(f, (W, H), interpolation=cv2.INTER_LANCZOS4)
        return cv2.cvtColor(f, cv2.COLOR_BGR2RGB)

    def cuadro(self, t):
        """t en segundos desde el inicio del tramo (se limita al tramo)."""
        i = int(np.clip(round(t * FPS), 0, self.n - 1))
        if self._ult[0] == i:
            return self._ult[1]
        p = os.path.join(self.dir, f"{i:04d}.jpg")
        f = cv2.imread(p) if os.path.exists(p) else None
        f = cv2.cvtColor(f, cv2.COLOR_BGR2RGB) if f is not None else self._lanczos(i)
        self._ult = (i, f)
        return f

    def completo(self):
        return all(os.path.exists(os.path.join(self.dir, f"{i:04d}.jpg")) for i in range(self.n))


def encuadre(img, w, h, cx=0.5, cy=0.5, z=1.0):
    """Recorte tipo 'cover' con zoom (para Ken Burns sobre el video)."""
    return base.cover(img, w, h, cx, cy, z)
