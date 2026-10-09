"""Video de presentación de Forralitas: arranque con "dron", 14 productos y cierre.

Uso:
    python presentacion.py                  # genera videos_salida/forralitas_presentacion.mp4
    python presentacion.py --frames 2 6 12  # guarda esos segundos como PNG (vista previa)

Fotos de productos en ./fotos_presentacion (en orden), fotos aéreas en assets/dron.
Los datos de contacto, horarios y medios de pago se toman de CONFIG en crear_video.py.
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from moviepy import AudioFileClip, VideoClip
from PIL import Image, ImageOps

import audio
import crear_video as cv
from efectos import (AMARILLO, BLANCO, H, VERDE_OSCURO, W, ancho_texto, blit, caja,
                     clamp01, desde_pil, ease_in_out, ease_out_back, ease_out_cubic,
                     fondo_animado, icono, logo_redondo, prog, sobre, texto)

TR = cv.TR
FPS = cv.FPS
SALIDA = "videos_salida/forralitas_presentacion.mp4"
BAND_Y, BAND_H = 620, 700        # banda donde se ve la foto aérea nítida
D_DRON_A, D_DRON_B, D_PRODUCTO, D_MOSAICO = 4.8, 4.6, 2.4, 3.4

# (título, subtítulo) por producto, en el orden de las fotos. * = palabra en amarillo
PRODUCTOS = [
    ("*Alfa*", ""),
    ("Engorde de *cerdo*", "Bolsa x 30 kg y suelto"),
    ("Mezcla de *caballo*", "Bolsa x 35 kg y suelto"),
    ("Pellet de *alfa*", ""),
    ("Maíz *entero*", ""),
    ("Maíz *quebrado*", "Bolsa x 40 kg y suelto"),
    ("Pellet de *trigo*", "Bolsa x 30 kg y suelto"),
    ("Afrecho de *trigo*", ""),
    ("Afrecho de *maíz*", "Por bolsa y suelto"),
    ("Ponedora para *gallinas*", "Por bolsa y suelto"),
    ("Iniciador *parrillero*", ""),
    ("Engorde *terminador*", ""),
    ("Alimentos para *perro* y *gato*", ""),
    ("*Virutas*", ""),
]


# ------------------------------------------------------------ foto aérea tipo dron
class Dron:
    """Foto aérea en una banda nítida sobre su propio fondo desenfocado (vertical 9:16)."""

    def __init__(self, ruta):
        self.img = np.asarray(Image.open(ruta).convert("RGB"))
        self.ph, self.pw = self.img.shape[:2]
        s = max(W / self.pw, H / self.ph)
        grande = cv2.resize(self.img, (int(self.pw * s) + 2, int(self.ph * s) + 2),
                            interpolation=cv2.INTER_CUBIC)
        y0, x0 = (grande.shape[0] - H) // 2, (grande.shape[1] - W) // 2
        bg = cv2.GaussianBlur(grande[y0:y0 + H, x0:x0 + W], (0, 0), 38).astype(np.float32)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.hypot(xx - W / 2, yy - H / 2) / np.hypot(W / 2, H / 2)
        self.fondo = (bg * 0.5 * (1 - 0.45 * r ** 2)[..., None]).astype(np.uint8)
        m = np.ones(BAND_H, np.float32)
        m[:30] = np.linspace(0, 1, 30)
        m[-30:] = np.linspace(1, 0, 30)
        self.mascara = m[:, None, None]
        self.vig = (1 - 0.30 * r ** 2)[..., None].astype(np.float32)

    def frame(self, t, dur, z0, z1, a, b, roll0, roll1):
        e = ease_in_out(t / dur)
        z = z0 + (z1 - z0) * e
        hw, hh = W / (2 * z), BAND_H / (2 * z)
        cx = np.clip((a[0] + (b[0] - a[0]) * e) * self.pw, hw, self.pw - hw)
        cy = np.clip((a[1] + (b[1] - a[1]) * e) * self.ph, hh, self.ph - hh)
        roll = np.radians(roll0 + (roll1 - roll0) * e + 0.4 * np.sin(t * 1.9))
        c, s = np.cos(roll) / z, np.sin(roll) / z
        sway = 5 * np.sin(t * 2.3)                         # leve vaivén de dron
        dcx, dcy = W / 2, BAND_H / 2 + sway
        M = np.array([[c, -s, 0], [s, c, 0]], np.float32)
        M[:, 2] = np.array([cx, cy]) - M[:, :2] @ np.array([dcx, dcy])
        ventana = cv2.warpAffine(self.img, M, (W, BAND_H),
                                 flags=cv2.INTER_CUBIC | cv2.WARP_INVERSE_MAP,
                                 borderMode=cv2.BORDER_REFLECT)
        f = self.fondo.copy()
        reg = f[BAND_Y:BAND_Y + BAND_H].astype(np.float32)
        f[BAND_Y:BAND_Y + BAND_H] = (reg * (1 - self.mascara) + ventana * self.mascara).astype(np.uint8)
        f = np.clip(f.astype(np.float32) * self.vig, 0, 255).astype(np.uint8)
        self._hud(f, t, dur)
        return f

    @staticmethod
    def _hud(f, t, dur):
        """Marco de visor de dron: esquinas, REC parpadeante y altura que baja."""
        x0, x1, y0, y1, L = 26, W - 26, BAND_Y + 22, BAND_Y + BAND_H - 22, 54
        for (x, y, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
            cv2.line(f, (x, y), (x + dx * L, y), AMARILLO, 4, cv2.LINE_AA)
            cv2.line(f, (x, y), (x, y + dy * L), AMARILLO, 4, cv2.LINE_AA)
        if np.sin(t * 5) > -0.2:
            cv2.circle(f, (x0 + 40, y0 + 42), 10, (235, 40, 40), -1, cv2.LINE_AA)
        cv2.putText(f, "REC", (x0 + 62, y0 + 53), cv2.FONT_HERSHEY_DUPLEX, 1.0, BLANCO, 2, cv2.LINE_AA)
        alt = int(118 - 70 * ease_in_out(t / dur))
        txt = f"ALT {alt} m"
        (tw, _), _ = cv2.getTextSize(txt, cv2.FONT_HERSHEY_DUPLEX, 1.0, 2)
        cv2.putText(f, txt, (x1 - 40 - tw, y0 + 53), cv2.FONT_HERSHEY_DUPLEX, 1.0, BLANCO, 2, cv2.LINE_AA)


def escena_dron_a():
    dron = Dron("assets/dron/dron1.jpg")
    top, xs_t, _ = cv.fila_palabras("¿Sos de *Las* *Talitas*", 104, W - 90)
    l1, xs1, _ = cv.fila_palabras("y no sabés dónde comprar", 70, W - 90)
    l2, xs2, _ = cv.fila_palabras("*alimentos* para tus *animales?*", 74, W - 70)

    def fn(t):
        f = dron.frame(t, D_DRON_A, 1.26, 1.9, (0.5, 0.5), (0.22, 0.5), -2.0, 1.0)
        cv.dibujar_palabras(f, top, xs_t, 405, t, 0.5, paso=0.18)
        cv.dibujar_palabras(f, l1, xs1, 1375, t, 1.7, paso=0.12)
        cv.dibujar_palabras(f, l2, xs2, 1480, t, 2.4, paso=0.14)
        if t < 0.6:                                         # entrada desde negro
            f = (f.astype(np.float32) * ease_out_cubic(t / 0.6)).astype(np.uint8)
        return f
    return fn


def escena_dron_b():
    dron = Dron("assets/dron/dron2.jpg")
    logo = logo_redondo(220)
    presento, xs_p, _ = cv.fila_palabras("TE PRESENTO", 62, W - 100, AMARILLO)
    nombre = cv.CONFIG["nombre"]
    tam = 124
    letras = [texto(c, tam, BLANCO) for c in nombre]
    x0 = (W - ancho_texto(nombre, tam)) / 2
    xs_n = [x0 + ancho_texto(nombre[:i], tam) - cv.PAD for i in range(len(nombre))]
    pin = icono("ubicacion", 104)
    est = texto("Estamos ubicados en", 46, BLANCO)
    ruta, xs_r, _ = cv.fila_palabras("*Ruta 305 km 7,5*", 92, W - 80)
    talitas = texto("Las Talitas", 62, BLANCO)

    def fn(t):
        f = dron.frame(t, D_DRON_B, 1.26, 2.0, (0.5, 0.5), (0.42, 0.58), 1.5, -1.0)
        p = prog(t, 0.45, 0.8)
        blit(f, logo, W / 2, 205, alpha=clamp01(p * 3), escala=ease_out_back(p), centro=True)
        cv.dibujar_palabras(f, presento, xs_p, 305, t, 0.7, paso=0.12)
        for i, (s, x) in enumerate(zip(letras, xs_n)):
            q = prog(t, 1.0 + 0.06 * i, 0.5)
            blit(f, s, x, 400 + (1 - ease_out_cubic(q)) * 80, alpha=ease_out_cubic(q * 1.5),
                 escala=0.6 + 0.4 * ease_out_back(q))
        qp = prog(t, 1.9, 0.7)                              # el pin "cae" en el mapa
        blit(f, pin, W / 2, 1405 - (1 - ease_out_back(qp, 1.6)) * 260, alpha=clamp01(qp * 4), centro=True)
        blit(f, est, (W - est.shape[1]) / 2, 1445 + (1 - ease_out_cubic(prog(t, 2.2, 0.5))) * 25,
             alpha=ease_out_cubic(prog(t, 2.2, 0.5)))
        cv.dibujar_palabras(f, ruta, xs_r, 1495, t, 2.5, paso=0.12)
        qt = ease_out_cubic(prog(t, 3.1, 0.5))
        blit(f, talitas, (W - talitas.shape[1]) / 2, 1600 + (1 - qt) * 25, alpha=qt)
        return f
    return fn


# ------------------------------------------------------------ "¡Y mucho más!"
def escena_mosaico(rutas, dur):
    lado = 300
    tiles = []
    for r in rutas:
        im = ImageOps.fit(Image.open(r).convert("RGB"), (lado, lado), Image.LANCZOS)
        borde = caja(lado + 12, lado + 12, 40, AMARILLO)
        mascara = caja(lado, lado, 34, (255, 255, 255))[:, :, 3:4]
        interior = np.dstack([np.asarray(im, np.float32) * mascara, mascara[:, :, 0]])
        tiles.append(sobre(borde, interior, 6, 6))
    spr_t, xs_t, _ = cv.fila_palabras("¡Y *MUCHO* *MÁS!*", 110, W - 90)

    def fn(t):
        f = fondo_animado(t, semilla=9)
        cv.dibujar_palabras(f, spr_t, xs_t, 150, t, 0.2, paso=0.16)
        for i, tile in enumerate(tiles):
            col, fila = i % 3, i // 3
            q = prog(t, 0.55 + 0.1 * i, 0.55)
            cx = 70 + col * (lado + 28) + lado / 2 + 6
            cy = 400 + fila * (lado + 28) + lado / 2 + 6
            wob = 1 + 0.012 * np.sin(t * 3 + i) if q >= 1 else 1
            blit(f, tile, cx, cy, alpha=clamp01(q * 3), escala=max(ease_out_back(q, 2.3), 0.01) * wob,
                 centro=True)
        return f
    return fn


# ------------------------------------------------------------ línea de tiempo
def construir():
    fotos = sorted(Path("fotos_presentacion").glob("*.jp*g"), key=lambda p: p.name)
    assert len(fotos) == len(PRODUCTOS), f"{len(fotos)} fotos y {len(PRODUCTOS)} textos"
    segs = [(D_DRON_A, escena_dron_a()), (D_DRON_B, escena_dron_b())]
    for i, (ruta, (titulo, sub)) in enumerate(zip(fotos, PRODUCTOS)):
        segs.append((D_PRODUCTO, cv.escena_producto(ruta, titulo, sub, cv.CAMARAS[i % len(cv.CAMARAS)],
                                                    dur=D_PRODUCTO, kicker="TENEMOS")))
    elegidas = [fotos[i] for i in (0, 1, 2, 3, 4, 5, 6, 7, 9, 10, 12, 13)]
    segs.append((D_MOSAICO, escena_mosaico(elegidas, D_MOSAICO)))
    segs.append((cv.D_CIERRE, cv.escena_cierre()))

    inicios, t = [], 0.0
    for d, _ in segs:
        inicios.append(t)
        t += d - TR
    return segs, inicios, inicios[-1] + segs[-1][0]


def main():
    segs, inicios, total = construir()
    n = len(PRODUCTOS)
    barra = (inicios[2] + TR, inicios[2 + n])
    make_frame = cv.hacer_frame_fn(segs, inicios, total, barra)

    if "--frames" in sys.argv:
        Path("videos_salida").mkdir(exist_ok=True)
        for s in [float(x) for x in sys.argv[sys.argv.index("--frames") + 1:]]:
            Image.fromarray(make_frame(s)).save(f"videos_salida/prev_{s:05.1f}.png")
        print("duración total:", round(total, 2), "s | inicios:", [round(x, 1) for x in inicios])
        return

    Path(SALIDA).parent.mkdir(exist_ok=True)
    out = inicios[-1]
    musica = audio.generar(
        total,
        t_transiciones=[inicios[i] - 0.07 for i in range(1, len(segs))],
        t_drop=inicios[2] + TR,
        t_golpes=[inicios[1] + 1.0, out + 0.2],
        t_dings=[out + o + 0.15 for o in (cv.T_HORA, cv.T_UBIC, cv.T_ENVIO, cv.T_MAYOR, cv.T_PAGOS, *cv.T_CHIPS)],
        t_timbres=[out + cv.T_TIMBRE0 + k * cv.PERIODO_TIMBRE for k in range(4)])
    video = VideoClip(make_frame, duration=total).with_audio(AudioFileClip(musica).subclipped(0, total))
    video.write_videofile(SALIDA, fps=FPS, codec="libx264", audio_codec="aac", audio_bitrate="192k",
                          preset="medium",
                          ffmpeg_params=["-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart"])
    print("Listo:", SALIDA, f"({total:.1f} s)")


if __name__ == "__main__":
    main()
