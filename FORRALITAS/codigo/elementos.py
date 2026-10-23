"""Elementos gráficos reutilizables: tarjetas de datos con ícono, chips de pago, espigas decorativas, logo."""
import math
import sys
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import motor as m  # noqa: E402
from efectos import caja, icono, logo_redondo, sobre  # noqa: E402

PADT = m.PADT


@lru_cache(maxsize=None)
def logo(lado):
    """Logo original FORRALITAS (recorte circular del archivo oficial, sin deformar)."""
    return logo_redondo(lado)


@lru_cache(maxsize=None)
def tarjeta_dato(nombre_icono, lineas, w, h, fondo=m.VERDE_OSC, color=m.BLANCO, color2=m.ORO_CLARO, tam=46, op=0.96, r=34,
                 ic_fondo=m.ORO, ic_tinta=m.VERDE_OSC):
    """lineas: tupla de textos. La primera en `color`, las demás en `color2`."""
    base = caja(w, h, r, fondo, op)
    lado = min(h - 36, 120)
    base = sobre(base, icono(nombre_icono, lado, ic_fondo, ic_tinta), 24, (h - lado) // 2)
    n = len(lineas)
    alto = tam * 1.2
    y0 = (h - n * alto) / 2 - 18
    for i, tx in enumerate(lineas):
        t = m.spr_texto(tx, tam if i == 0 else int(tam * 0.9), color if i == 0 else color2, m.EXTRA if i == 0 else m.SEMI, 0, m.VERDE_OSC, False)
        base = sobre(base, t, 24 + lado + 22 - PADT, int(y0 + i * alto) - 6)
    return base


@lru_cache(maxsize=None)
def chip(nombre_icono, texto, w=None, h=84, fondo=m.VERDE_OSC, color=m.BLANCO, tam=34):
    w = w or int(m.ancho(texto, tam, m.EXTRA)) + (h - 20) + 10 + 8 + 26
    base = caja(w, h, h // 2, fondo, 0.96)
    lado = h - 20
    base = sobre(base, icono(nombre_icono, lado, m.ORO, m.VERDE_OSC), 10, 10)
    t = m.spr_texto(texto, tam, color, m.EXTRA, 0, m.VERDE_OSC, False)
    return sobre(base, t, 10 + lado + 8 - PADT, (h - int(tam * 1.35)) // 2 - PADT + 2)


@lru_cache(maxsize=None)
def pastilla(texto, tam, fondo=m.ORO, color=m.VERDE_OSC, ruta=m.NEGRA, px=34, py=14):
    t = m.spr_texto(texto, tam, color, ruta, 0, m.VERDE_OSC, False)
    w, h = int(m.ancho(texto, tam, ruta)) + 2 * px, int(tam * 1.2) + 2 * py
    base = caja(w, h, h // 2, fondo, 1.0)
    return sobre(base, t, px - PADT, py - PADT + int(tam * 0.04))


def espiga(f, cx, cy, esc=1.0, ang=0.0, color=m.ORO, alpha=1.0):
    """Espiga de trigo simple (tallo + granos) como decoración."""
    ov = f.copy()
    a = math.radians(ang)
    dx, dy = math.sin(a), -math.cos(a)
    nx, ny = -dy, dx
    largo = 260 * esc
    cv2.line(ov, (int(cx - dx * 90 * esc), int(cy - dy * 90 * esc)), (int(cx + dx * largo), int(cy + dy * largo)),
             color, max(2, int(5 * esc)), cv2.LINE_AA)
    for i in range(8):
        d = (40 + i * 26) * esc
        for s in (-1, 1):
            gx, gy = cx + dx * d + nx * s * 16 * esc, cy + dy * d + ny * s * 16 * esc
            cv2.ellipse(ov, (int(gx), int(gy)), (int(9 * esc), int(22 * esc)), ang + s * 28, 0, 360, color, -1, cv2.LINE_AA)
    cv2.ellipse(ov, (int(cx + dx * (largo + 18 * esc)), int(cy + dy * (largo + 18 * esc))), (int(8 * esc), int(22 * esc)), ang, 0, 360, color, -1, cv2.LINE_AA)
    cv2.addWeighted(ov, alpha, f, 1 - alpha, 0, f)


def anillo(f, cx, cy, r, p, color=m.ORO, grosor=10, giro=0.0):
    """Arco dorado que se dibuja alrededor de un círculo (p: 0 → 1)."""
    if p <= 0:
        return
    cv2.ellipse(f, (int(cx), int(cy)), (int(r), int(r)), giro, 0, 360 * p, color, grosor, cv2.LINE_AA)
