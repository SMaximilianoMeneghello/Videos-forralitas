"""Promo "¡Llegó maíz!" — versión 2, con el formato de marca de los videos anteriores.

- El video original va SIN filtros (color natural), dentro de un marco dorado sobre el fondo verde de Forralitas.
- Encabezado con logo, títulos animados debajo del video y subtítulos sincronizados con la voz.
- Placa final igual a los videos anteriores, con TODOS los datos leídos por la voz.
- Audio: solo voz en off (sin música, sin efectos, sin el audio original).

Uso:
    python maiz_promo2.py                  # genera videos_salida/maiz_promo2.mp4
    python maiz_promo2.py --frames 1 9 30  # vistas previas
"""
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from moviepy import AudioFileClip, VideoClip
from PIL import Image
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

import maiz_promo as mp
import oferta_gatos as og
import voz_tts
from crear_video import dibujar_reloj
from efectos import (DIAGONAL, blit, caja, clamp01, ease_in_out, ease_out_back, ease_out_cubic, icono,
                     logo_redondo, prog, rotar_sprite, sobre)

W, H, FPS = 1080, 1920, 30
SALIDA = "videos_salida/maiz_promo2.mp4"
SR = voz_tts.SR
VOZ, RATE = "es-AR-TomasNeural", "-4%"
MAIZ, ORO, BLANCO = mp.MAIZ, mp.ORO, mp.BLANCO
VERDE, VERDE_OSC = mp.VERDE, mp.VERDE_OSC
VERDE1, VERDE2 = (20, 96, 48), (3, 22, 10)
BLK, XB = mp.BLK, mp.XB
TR = 0.45

# marco del video
FX, FY, FW, FH = 60, 250, 960, 1200          # 4:5

GUION = {
    "L1": (1.4, "¡Llegó maíz de primera calidad a nuestra forrajería, Forralitas!",
           [("¡Llegó *maíz*", 2), ("de *primera calidad*", 3), ("a nuestra forrajería,", 3), ("*Forralitas!*", 1)]),
    "L2": (9.4, "Tenemos bolsas de cuarenta y de cincuenta kilos.",
           [("Tenemos bolsas", 2), ("de *40* y de *50 kilos*.", 6)]),
    "L3a": (17.0, "Te esperamos con los mejores productos al mejor precio.",
            [("Te esperamos", 2), ("con los *mejores productos*", 4), ("al *mejor precio*.", 3)]),
    "L3b": (21.2, "¡Visitanos!", [("*¡Visitanos!*", 1)]),
    "F1": (27.0, "Estamos en Ruta trescientos cinco, kilómetro siete coma cinco, Las Talitas.",
           [("Estamos en *Ruta 305*,", 5), ("kilómetro *7,5*,", 4), ("*Las Talitas*.", 2)]),
    "F2": (None, "Llamanos al tres ocho uno, cinco dos seis, nueve cero cero cuatro, "
                 "o al tres ocho uno, seis tres tres, cuatro tres cuatro cuatro.",
           [("Llamanos al", 2), ("*381 526 9004*", 10), ("o al", 2), ("*381 633 4344*.", 10)]),
    "F3": (None, "Atendemos de lunes a viernes, de ocho a diecinueve horas, y los sábados, de ocho y treinta a diecinueve horas.",
           [("Atendemos de *lunes a viernes*,", 5), ("de *8 a 19 horas*,", 5), ("y los *sábados*,", 3),
            ("de *8:30 a 19 horas*.", 7)]),
    "F4": (None, "Hacemos envíos según la zona.", [("Hacemos *envíos*", 2), ("según la zona.", 3)]),
    "F5": (None, "Venta por mayor y menor.", [("Venta por *mayor y menor*.", 5)]),
    "F6": (None, "Aceptamos todos los medios de pago: efectivo, transferencia, débito y crédito.",
           [("Aceptamos *todos los medios de pago*:", 6), ("*efectivo, transferencia,*", 2), ("*débito y crédito*.", 3)]),
    "F7": (None, "Forralitas, Forrajería y Semillería.", [("*Forralitas*,", 1), ("Forrajería y Semillería.", 3)]),
}
ORDEN_FINAL = ["F1", "F2", "F3", "F4", "F5", "F6", "F7"]
PAUSA = 0.55
T_INTRO, T_PRES, T_TOLVA, T_MANOS, T_PLACA = (0, 8), (8, 16), (16, 22), (22, 26), 26.0


# ------------------------------------------------------------ voz y subtítulos
def preparar_voz():
    L = {}
    for k, (t0, txt, chunks) in GUION.items():
        x, tiempos = voz_tts.clip_palabras(txt, voz=VOZ, rate=RATE)
        assert sum(n for _, n in chunks) == len(txt.split()), k
        L[k] = dict(audio=x, tiempos=tiempos, dur=len(x) / SR, chunks=chunks, inicio=t0, txt=txt)
    for a, b in zip(ORDEN_FINAL, ORDEN_FINAL[1:]):
        L[b]["inicio"] = L[a]["inicio"] + L[a]["dur"] + PAUSA
    return L


def t_palabra(Li, palabra, n=0):
    pal = [w.strip("¡!¿?,.:").lower() for w in Li["txt"].split()]
    idx = [i for i, p in enumerate(pal) if p == palabra][n]
    return Li["inicio"] + Li["tiempos"][idx]


def subtitulos(L):
    subs = []
    for Li in L.values():
        idx, st = 0, []
        for txt, n in Li["chunks"]:
            st.append((Li["inicio"] + Li["tiempos"][idx] - 0.05, txt))
            idx += n
        for i, (s, txt) in enumerate(st):
            e = st[i + 1][0] if i + 1 < len(st) else Li["inicio"] + Li["dur"] + 0.35
            subs.append((s, e, txt))
    return sorted(subs)


# ------------------------------------------------------------ video dentro del marco (sin filtros)
def encuadre(frame, cx, cy, w, ow=FW, oh=FH):
    h = w * oh / ow
    s = ow / w
    M = np.array([[s, 0, -(cx - w / 2) * s], [0, s, -(cy - h / 2) * s]], np.float32)
    return cv2.warpAffine(frame, M, (ow, oh), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT)


MASCARA = caja(FW, FH, 40, (255, 255, 255))[:, :, 3:4]
MARCO = caja(FW + 16, FH + 16, 46, MAIZ)
SOMBRA = og.pad(np.dstack([np.zeros((FH, FW, 3), np.float32), cv2.GaussianBlur(MASCARA[..., 0], (0, 0), 1) * 0.55]), 0.06)
SOMBRA = np.dstack([SOMBRA[..., :3], cv2.GaussianBlur(SOMBRA[..., 3], (0, 0), 22)])


def sprite_video(img):
    return np.dstack([img.astype(np.float32) * MASCARA, MASCARA[..., 0]])


# ------------------------------------------------------------ fondo y marca
def fondo(t):
    f = og.fondo(t * 0.6, VERDE1, VERDE2, rayos=0.8)
    return og.chispas(f, t * 0.6, MAIZ, 40, 0.35)


def cabecera():
    logo = logo_redondo(116)
    n = mp.sprite_texto([("FORRALITAS", BLANCO)], 66, BLK, 0, sombra=False)
    r = mp.sprite_texto([("Forrajería y Semillería", MAIZ)], 34, XB, 0, sombra=False)
    w = 116 + 24 + max(n.shape[1], r.shape[1]) - 60
    base = np.zeros((130, w, 4), np.float32)
    base = sobre(base, logo, 0, 7)
    base = sobre(base, n, 140 - 30, -14)
    return sobre(base, r, 142 - 30, 58)


CABECERA = cabecera()


# ------------------------------------------------------------ escenas
class Promo:
    def __init__(self):
        self.L = preparar_voz()
        self.dur = round(self.L["F7"]["inicio"] + self.L["F7"]["dur"] + 2.2, 2)
        self.subs = subtitulos(self.L)
        self.tomas = mp.preparar_tomas()
        S = mp.sprite_texto
        e = mp.tam_que_entra
        self.llego = S([("¡LLEGÓ MAÍZ!", MAIZ)], e("¡LLEGÓ MAÍZ!", 140, BLK, 960), BLK, 11, VERDE_OSC)
        self.calidad = mp.pastilla("de primera calidad", 54, VERDE, BLANCO)
        self.bolsas = S([("Bolsas de", BLANCO)], 84, BLK, 9, VERDE_OSC)
        self.b40 = mp.pastilla("40 kg", 84, VERDE, MAIZ, BLK, 40)
        self.y_ = S([("y", BLANCO)], 76, BLK, 9, VERDE_OSC)
        self.b50 = mp.pastilla("50 kg", 84, VERDE, MAIZ, BLK, 40)
        self.mejores = S([("LOS MEJORES PRODUCTOS", BLANCO)], e("LOS MEJORES PRODUCTOS", 84, BLK, 960), BLK, 9, VERDE_OSC)
        self.punto = caja(22, 22, 11, MAIZ)
        self.precio = S([("AL MEJOR PRECIO", MAIZ)], e("AL MEJOR PRECIO", 104, BLK, 960), BLK, 10, VERDE_OSC)
        self.visita = S([("¡VISITANOS!", MAIZ)], 120, BLK, 11, VERDE_OSC)
        self.placa = Placa(self.L)

    # ---- contenido del marco (video natural)
    def toma(self, nombre, t):
        if nombre == "intro":
            p = t / 8
            cx, cy, w = mp.ken_burns((292, 272, 380), (300, 270, 320), p)
            w /= 1 + 0.5 * (1 - ease_out_cubic(clamp01(t / 0.8)))                # zoom rápido inicial
            return encuadre(mp.cuadro(self.tomas, "A1", t), cx, cy, w)
        if nombre == "pres":
            cx, cy, w = mp.ken_burns((282, 318, 398), (282, 320, 340), t / 8)
            return encuadre(mp.cuadro(self.tomas, "C", t), cx, cy, w)
        if nombre == "tolva":
            cx, cy, w = mp.ken_burns((300, 270, 300), (302, 272, 212), t / 6)
            return encuadre(mp.cuadro(self.tomas, "B", t), cx, cy, w)
        cx, cy, w = mp.ken_burns((300, 275, 345), (300, 280, 295), t / 4)
        return encuadre(mp.cuadro(self.tomas, "A2", t), cx, cy, w)

    def contenido(self, t):
        cortes = [(T_INTRO, "intro"), (T_PRES, "pres"), (T_TOLVA, "tolva"), (T_MANOS, "manos")]
        trans = [mp_tr(mp.tr_barrido), mp_tr(mp.tr_destello), mp_tr(mp.tr_deslizar)]
        for i, ((a, b), n) in enumerate(cortes[:-1]):
            if b - TR / 2 <= t < b + TR / 2:
                p = (t - (b - TR / 2)) / TR
                img = trans[i](self.toma(n, min(t, b - 1e-3) - a), self.toma(cortes[i + 1][1], max(t, b) - b), p)
                return img, n
        for (a, b), n in cortes:
            if a <= t < b + 1:
                return self.toma(n, min(t, b - 1e-3) - a), n
        return self.toma("manos", 3.99), "manos"

    # ---- títulos debajo del video
    def titulos(self, f, t):
        y1, y2 = 1530, 1650
        def entra(t0, d=0.5):
            return prog(t, t0, d)
        def sale(t1):
            return 1 - clamp01((t - t1) / 0.25)
        if t < T_PRES[0] + 0.1:
            a = sale(T_PRES[0] - 0.2)
            q = entra(0.5)
            blit(f, self.llego, W / 2, y1, alpha=clamp01(q * 3) * a, escala=max(ease_out_back(q, 2.0), 0.01) * (2.2 - 1.2 * ease_out_cubic(q)) / 1, centro=True)
            q = entra(1.2)
            blit(f, self.calidad, W / 2, y2 + 10 + (1 - ease_out_cubic(q)) * 50, alpha=clamp01(q * 3) * a, centro=True)
        elif t < T_TOLVA[0] + 0.1:
            a = sale(T_TOLVA[0] - 0.2)
            tl = t - T_PRES[0]
            L2 = self.L["L2"]
            t40 = t_palabra(L2, "cuarenta") - T_PRES[0] - 0.1
            t50 = t_palabra(L2, "cincuenta") - T_PRES[0] - 0.1
            q = prog(tl, 0.35, 0.5)
            blit(f, self.bolsas, W / 2 - (1 - ease_out_cubic(q)) * 900, y1, alpha=clamp01(q * 3) * a, centro=True)
            for spr, x, t0 in ((self.b40, 300, t40), (self.y_, 540, t40 + 0.25), (self.b50, 780, t50)):
                q = prog(tl, t0, 0.45)
                blit(f, spr, x, y2 + 10, alpha=clamp01(q * 3) * a, escala=max(ease_out_back(q, 2.4), 0.01), centro=True)
        elif t < T_PLACA:
            a = sale(T_PLACA - 0.25)
            L3 = self.L["L3a"]
            tm, tp = t_palabra(L3, "mejores") - 0.15, t_palabra(L3, "precio") - 0.45
            tv = self.L["L3b"]["inicio"] - 0.1
            av = 1 - clamp01((t - tv) / 0.25)
            q = prog(t, tm, 0.5)
            blit(f, self.mejores, W / 2 - (1 - ease_out_cubic(q)) * 1000, y1, alpha=clamp01(q * 3) * a * av, centro=True)
            q = prog(t, tp - 0.15, 0.3)
            blit(f, self.punto, W / 2, (y1 + y2) / 2 + 8, alpha=clamp01(q * 3) * a * av, escala=max(ease_out_back(q, 2.5), 0.01), centro=True)
            q = prog(t, tp, 0.5)
            blit(f, self.precio, W / 2 + (1 - ease_out_cubic(q)) * 1000, y2 + 10, alpha=clamp01(q * 3) * a * av, centro=True)
            q = prog(t, tv, 0.45)
            if q > 0:
                pul = 1 + 0.04 * np.sin((t - tv) * 7)
                blit(f, self.visita, W / 2, (y1 + y2) / 2 + 20, alpha=clamp01(q * 3) * a,
                     escala=max(ease_out_back(q, 2.2), 0.01) * pul, centro=True)

    def tramo_video(self, t):
        f = fondo(t)
        img, nombre = self.contenido(t)
        # brillos dorados sutiles en momentos clave (el color del video no se toca)
        if nombre == "intro" and 0.6 < t < 4:
            img = mp.brillos(np.ascontiguousarray(img), t, (120, 300, 840, 1000), 6, 1, op=0.7)
        if nombre == "tolva":
            img = mp.brillos(np.ascontiguousarray(img), t, (100, 200, 860, 1050), 10, 11, op=0.8)
        # entrada del marco
        q = prog(t, 0.0, 0.7)
        esc = 0.86 + 0.14 * ease_out_back(q, 1.3)
        cy = FY + FH / 2
        blit(f, SOMBRA, W / 2, cy + 22, alpha=clamp01(q * 2), escala=esc, centro=True)
        blit(f, MARCO, W / 2, cy, alpha=clamp01(q * 3), escala=esc, centro=True)
        blit(f, sprite_video(img), W / 2, cy, alpha=clamp01(q * 3), escala=esc, centro=True)
        qc = ease_out_cubic(prog(t, 0.2, 0.6))
        blit(f, CABECERA, W / 2, 125 - (1 - qc) * 160, alpha=qc, centro=True)
        self.titulos(f, t)
        f = mp.destello(f, t, 0.05, 0.45, 0.8)
        return f

    def frame(self, t):
        t = min(t, self.dur - 1e-3)
        if t < T_PLACA - TR / 2:
            f = self.tramo_video(t)
        elif t < T_PLACA + TR / 2:
            p = (t - (T_PLACA - TR / 2)) / TR
            f = mp.tr_zoom_entrada(self.tramo_video(min(t, T_PLACA - 1e-3)), self.placa.render(self.tomas, max(t - T_PLACA, 0)), p)
        else:
            f = self.placa.render(self.tomas, t - T_PLACA)
        # subtítulos (siempre fuera del video, sobre el fondo verde)
        y_sub = 1795
        for s, e, txt in self.subs:
            if s <= t < e:
                q = prog(t, s, 0.18)
                blit(f, mp.sprite_sub(txt, 58, 990), W / 2, y_sub, alpha=clamp01(q * 3) * clamp01((e - t) / 0.12),
                     escala=0.85 + 0.15 * ease_out_back(q, 2.0), centro=True)
        # barra de progreso
        f = np.ascontiguousarray(f)
        cv2.line(f, (60, 1888), (W - 60, 1888), (40, 70, 50), 6, cv2.LINE_AA)
        cv2.line(f, (60, 1888), (int(60 + (W - 120) * t / self.dur), 1888), MAIZ, 6, cv2.LINE_AA)
        return f

    def audio(self, ruta="videos_salida/_maiz2_voz.wav"):
        n = int(self.dur * SR)
        voz = np.zeros(n, np.float32)
        for Li in self.L.values():
            x = Li["audio"] * (10 ** (-18 / 20) / (np.sqrt((Li["audio"] ** 2).mean()) + 1e-9))
            i = int(Li["inicio"] * SR)
            voz[i:i + x.size] += x[:max(0, n - i)]
        voz = sosfilt(butter(2, 70, btype="highpass", fs=SR, output="sos"), voz)
        voz *= 0.9 / np.abs(voz).max()
        tmp = "videos_salida/_maiz2_crudo.wav"
        wavfile.write(tmp, SR, (voz * 32767).astype(np.int16))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af", "loudnorm=I=-16:TP=-1.5:LRA=7", "-ac", "2",
                        "-ar", str(SR), ruta], check=True)
        return ruta


def mp_tr(fn):
    """Adapta las transiciones (pensadas para 1080x1920) al tamaño del marco."""
    def tr(a, b, p):
        A = cv2.resize(a, (W, H))
        B = cv2.resize(b, (W, H))
        return cv2.resize(fn(A, B, p), (FW, FH))
    return tr


# ------------------------------------------------------------ placa final (estilo de los videos anteriores)
class Placa:
    def __init__(self, L):
        self.L = L
        k = lambda n: L[n]["inicio"] - T_PLACA
        self.c = dict(ruta=k("F1"), tel1=k("F2"), tel2=t_palabra(L["F2"], "o") - T_PLACA, hora=k("F3"),
                      envio=k("F4"), mayor=k("F5"), pagos=k("F6"), firma=k("F7"))
        self.c["chips"] = [t_palabra(L["F6"], w) - T_PLACA - 0.1 for w in ("efectivo", "transferencia", "débito", "crédito")]
        S = mp.sprite_texto
        self.logo = logo_redondo(230)
        self.nombre = S([("FORRALITAS", BLANCO)], 104, BLK, 0)
        self.rubro = S([("Forrajería y Semillería", MAIZ)], 50, XB, 0)

        def fila(ic, l1, l2=None, tam1=56, tam2=42, col1=BLANCO, alto=None):
            w, h = 960, alto or (150 if l2 else 116)
            base = caja(w, h, 32, (0, 0, 0), 0.42)
            if ic:
                base = sobre(base, icono(ic, 88), 26, (h - 88) // 2)
            t1 = S([(l1, col1)], mp.tam_que_entra(l1, tam1, BLK, 790), BLK, 0, sombra=False)
            y1 = 22 - 30 if l2 else (h - t1.shape[0]) // 2 + 2
            base = sobre(base, t1, 136 - 30, y1)
            if l2:
                t2 = S([(l2, (215, 235, 220))], mp.tam_que_entra(l2, tam2, XB, 790), XB, 0, sombra=False)
                base = sobre(base, t2, 136 - 30, 86 - 30)
            return base
        self.f_ruta = fila("ubicacion", "Ruta 305, km 7,5", "Las Talitas")
        self.f_tel1 = fila(None, "381 526 9004", None, 70, col1=MAIZ)
        self.f_tel2 = fila(None, "381 633 4344", None, 70, col1=MAIZ)
        self.ic_tel = icono("telefono", 92)
        self.f_hora = fila(None, "Lunes a viernes 8:00 a 19:00", "Sábados 8:30 a 19:00", 50, 44)
        self.f_envio = fila("camion", "Envíos según la zona", None, 54)
        bt = S([("VENTA POR MAYOR Y MENOR", VERDE_OSC)], 54, BLK, 0, sombra=False)
        self.banner = sobre(caja(960, 104, 52, MAIZ), bt, (960 - bt.shape[1]) // 2, (104 - bt.shape[0]) // 2 + 2)
        self.t_pagos = S([("ACEPTAMOS TODOS LOS MEDIOS DE PAGO", MAIZ)], 38, BLK, 0, sombra=False)
        self.chips = []
        for nom, etq in (("efectivo", "Efectivo"), ("transferencia", "Transferencia"), ("debito", "Débito"),
                         ("credito", "Crédito")):
            ch = caja(225, 150, 26, (0, 0, 0), 0.42)
            ch = sobre(ch, icono(nom, 72), (225 - 72) // 2, 12)
            tt = S([(etq, BLANCO)], mp.tam_que_entra(etq, 30, XB, 205), XB, 0, sombra=False)
            self.chips.append(sobre(ch, tt, (225 - (tt.shape[1] - 60)) // 2 - 30, 96 - 30))

    def fondo(self, tomas, t):
        """El maíz de fondo, desenfocado y oscurecido (sin cambiar el color)."""
        fr = tomas["B"]
        n = len(fr)
        k = int(t * FPS * 0.5) % (2 * n - 2)
        k = k if k < n else 2 * n - 2 - k
        img = mp.encuadre(fr[k], 300, 270, 232)
        img = cv2.resize(cv2.GaussianBlur(cv2.resize(img, (270, 480)), (0, 0), 7), (W, H))
        return (img.astype(np.float32) * 0.36).astype(np.uint8)

    def render(self, tomas, t):
        c = self.c
        f = self.fondo(tomas, t)
        f = og.chispas(f, t * 0.6, MAIZ, 30, 0.3)
        pf = clamp01((t - c["firma"]) / 0.3) * (1 - clamp01((t - c["firma"] - 1.8) / 0.5))
        pul = 1 + 0.07 * np.sin(np.pi * clamp01((t - c["firma"]) / 0.6)) * (t > c["firma"])
        p = prog(t, 0.0, 0.6)
        blit(f, rotar_sprite(og.pad(self.logo, 0.1), -30 * (1 - ease_out_cubic(p))), W / 2, 175, alpha=clamp01(p * 3),
             escala=max(ease_out_back(p, 1.8), 0.01) * pul, centro=True)
        q = prog(t, 0.2, 0.45)
        blit(f, self.nombre, W / 2, 360, alpha=clamp01(q * 3), escala=(1.6 - 0.6 * ease_out_cubic(q)) * pul, centro=True)
        q = prog(t, 0.35, 0.4)
        blit(f, self.rubro, W / 2, 440, alpha=clamp01(q * 3), wipe=ease_out_cubic(q), centro=True)
        if pf > 0:
            f = mp.brillos(f, t, (140, 100, 940, 480), 8, 4, op=pf)

        def entra(spr, t0, y, desde=1):
            q = prog(t, t0, 0.5)
            if q <= 0:
                return None
            e = ease_out_back(q, 1.3)
            x = 60 + (1 - e) * W * desde
            blit(f, spr, x, y, alpha=clamp01(q * 3))
            return x
        entra(self.f_ruta, c["ruta"] - 0.1, 500)
        for spr, t0, y in ((self.f_tel1, c["tel1"] - 0.1, 670), (self.f_tel2, c["tel2"] - 0.1, 800)):
            x = entra(spr, t0, y, -1)
            if x is not None:
                cx, cy = x + 70, y + 58
                fase = (t - t0 - 0.4) % 1.8 if t >= t0 + 0.4 else 99
                env = max(0.0, 1 - fase / 0.6)
                for k in range(3 if env > 0 else 0):
                    ov = f.copy()
                    cv2.circle(ov, (int(cx), int(cy)), int(54 + 26 * k + fase * 80), MAIZ, 4, cv2.LINE_AA)
                    a = env * (1 - k * 0.3) * 0.6
                    f[:] = cv2.addWeighted(ov, a, f, 1 - a, 0)
                ang = 18 * np.sin(fase * 50) * env if env > 0 else 0
                blit(f, rotar_sprite(self.ic_tel, ang), cx, cy, alpha=clamp01(prog(t, t0, 0.5) * 3), centro=True)
        x = entra(self.f_hora, c["hora"] - 0.1, 940)
        if x is not None:
            dibujar_reloj(f, int(x + 70), 940 + 75, 50, t, c["hora"])
        entra(self.f_envio, c["envio"] - 0.1, 1110, -1)
        q = prog(t, c["mayor"] - 0.1, 0.6)
        if q > 0:
            bx = 60 + (1 - ease_out_back(q, 1.4)) * W
            blit(f, self.banner, bx, 1246, alpha=clamp01(q * 3))
            if q >= 1:
                pos = ((t - c["mayor"] - 0.5) % 2.4) * 1700 - 400
                reg = f[1246:1350, 60:1020].astype(np.float32)
                reg += (np.exp(-(((DIAGONAL[1246:1350, 60:1020] - pos) / 45) ** 2)) * self.banner[:, :, 3])[..., None] * 110
                f[1246:1350, 60:1020] = np.clip(reg, 0, 255).astype(np.uint8)
        q = prog(t, c["pagos"] - 0.1, 0.45)
        blit(f, self.t_pagos, W / 2, 1405 + (1 - ease_out_cubic(q)) * 25, alpha=ease_out_cubic(q), centro=True)
        for i, (ch, t0) in enumerate(zip(self.chips, c["chips"])):
            q = prog(t, t0, 0.45)
            idle = 1 + 0.02 * np.sin(t * 3 + i) if q >= 1 else 1
            blit(f, ch, 60 + 112 + i * 245, 1540, alpha=clamp01(q * 3), escala=max(ease_out_back(q, 2.4), 0.01) * idle,
                 centro=True)
        return f


def main():
    v = Promo()
    Path("videos_salida").mkdir(exist_ok=True)
    print("duración:", v.dur, "| voz:", {k: (round(L["inicio"], 2), round(L["dur"], 2)) for k, L in v.L.items()})
    if "--frames" in sys.argv:
        for s in [float(x) for x in sys.argv[sys.argv.index("--frames") + 1:]]:
            Image.fromarray(v.frame(s)).save(f"videos_salida/prev_{s:05.2f}.png")
        return
    wav = v.audio()
    pista = AudioFileClip(wav)
    clip = VideoClip(v.frame, duration=v.dur).with_audio(pista.subclipped(0, min(v.dur, pista.duration)))
    clip.write_videofile(SALIDA, fps=FPS, codec="libx264", audio_codec="aac", audio_bitrate="160k", preset="medium",
                         ffmpeg_params=["-crf", "21", "-pix_fmt", "yuv420p", "-movflags", "+faststart"])
    print("Listo:", SALIDA)


if __name__ == "__main__":
    main()
