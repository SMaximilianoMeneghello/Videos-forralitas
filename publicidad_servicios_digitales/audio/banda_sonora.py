"""Banda sonora original (música + efectos) sincronizada con la línea de tiempo, y mezcla con la locución.

Salidas en audio/:
  musica_efectos.wav   música y efectos sin voz
  voz_completa.wav     locución procesada y ubicada en el tiempo
  mezcla_final.wav     mezcla con ducking (la voz siempre por delante)
  demo_edicion.wav     audio de la demo de 10 s (tramo 17.5–27.5)
"""
import json
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly
import sintes as S
from sintes import SR, poner, midi

B = Path(__file__).resolve().parent
TL = json.loads((B.parent / "guion/timeline.json").read_text())
MARCAS = json.loads((B / "voz/marcas.json").read_text())
DUR = TL["duracion"]
N = int(SR * (DUR + .5))
BEAT = 60 / TL["bpm"]
BAR = 4 * BEAT
pal = lambda vid, w: next((TL["voz"][vid] + p["t"] for p in MARCAS[vid]["palabras"] if p["w"].lower().startswith(w)), TL["voz"][vid])

mus = np.zeros((N, 2))
sfx = np.zeros((N, 2))


def st(x, pan=0.0):
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    return np.stack([x * l * 1.41, x * r * 1.41], 1)


def add(buf, t, x, g=1.0, pan=0.0):
    if x.ndim == 1:
        x = st(x, pan)
    i = int(round(t * SR))
    if i < 0:
        x = x[-i:]; i = 0
    j = min(len(buf), i + len(x))
    if j > i:
        buf[i:j] += x[:j - i] * g


# ------------------------------------------------------------------ progresiones y energía por sección
PROG_A = [(57, 60, 64), (53, 57, 60), (48, 52, 55), (55, 59, 62)]          # Am F C G
PROG_B = [(53, 57, 60, 64), (55, 59, 62, 66), (52, 55, 59, 62), (57, 60, 64, 67)]  # Fmaj7 G Em7 Am7 (más elegante)
# (inicio, fin, estilo)
SECCIONES = [(0, 6.0, "intro"), (6.0, 14.0, "titulo"), (14.0, 17.5, "nle"), (17.5, 27.5, "demo"), (27.5, 43.0, "groove"),
             (43.0, 45.0, "golpes"), (45.0, 63.0, "elegante"), (63.0, 86.5, "tech"), (86.5, 109.0, "build"),
             (109.0, 123.0, "cierre"), (123.0, DUR, "final")]


def estilo(t):
    for a, b, e in SECCIONES:
        if a <= t < b:
            return e
    return "final"


nbar = int(DUR / BAR) + 1
for b in range(nbar):
    t0 = b * BAR
    e = estilo(t0 + .01)
    prog = PROG_B if e in ("elegante", "final") else PROG_A
    ch = prog[b % 4]
    # pad de fondo en todas las secciones salvo los golpes
    if e != "golpes":
        brillo = {"intro": 900, "titulo": 1500, "nle": 1600, "demo": 1800, "groove": 2000, "elegante": 2400, "tech": 2200, "build": 2600, "cierre": 2400, "final": 2600}[e]
        vol = {"intro": .10, "demo": .08, "elegante": .13, "final": .14}.get(e, .09)
        add(mus, t0, S.pad([n - 12 for n in ch[:3]] + ([ch[3] - 12] if len(ch) > 3 else []), BAR + .5, brillo, vol, .5, .6), 1, 0)
    # bajo en corcheas
    if e in ("titulo", "nle", "groove", "tech", "build", "cierre", "demo"):
        for k in range(8):
            if e == "nle" and k % 2: continue
            add(mus, t0 + k * BEAT / 2, S.pluck(ch[0] - 24, BEAT * .48, .22, 600, 7), 1)
    if e in ("elegante", "final"):
        for k in range(4):
            add(mus, t0 + k * BEAT, S.sub(ch[0] - 24, BEAT * .95, .16), 1)
    # arpegios / campanas
    if e in ("titulo", "groove", "tech", "build", "cierre"):
        patron = [0, 1, 2, 1, 2, 0, 1, 2] if e != "tech" else [0, 2, 1, 2, 0, 2, 1, 2]
        for k in range(16 if e in ("tech", "build") else 8):
            paso = BEAT / 4 if e in ("tech", "build") else BEAT / 2
            n = ch[patron[k % 8]] + 12 + (12 if (k // 8) % 2 else 0)
            add(mus, t0 + k * paso, S.pluck(n, .35, .07, 3200 if e != "build" else 4200, 9), 1, -.4 + .8 * ((k % 4) / 3))
    if e in ("elegante", "final"):
        for k in range(8):
            n = ch[[0, 1, 2, 3 if len(ch) > 3 else 1, 2, 1, 2, 0][k]] + 12
            add(mus, t0 + k * BEAT / 2, S.campana(n, 1.4, .05), 1, -.5 + k / 7)
    # batería
    if e in ("titulo", "groove", "demo", "tech", "build", "cierre"):
        for k in range(4):
            tb = t0 + k * BEAT
            if e == "titulo" and tb < 8.0: continue
            if e == "cierre" and 113.0 < tb < 119.0: continue
            add(mus, tb, S.bombo(.8 if e != "tech" else .65), 1)
            if k in (1, 3) and e not in ("titulo",):
                add(mus, tb, S.palmas(.32), 1)
            for h in range(2 if e in ("titulo", "groove") else 4):
                add(mus, tb + h * BEAT / (2 if e in ("titulo", "groove") else 4) + (BEAT / 4 if e in ("titulo", "groove") else 0), S.hat(.06 if h % 2 else .09), 1, .3)
    if e == "elegante" and t0 >= 51.0:
        for k in (0, 2):
            add(mus, t0 + k * BEAT, S.bombo(.4, 110), 1)
        add(mus, t0 + 3 * BEAT, S.hat(.08, abierto=True), 1, .3)

# ------------------------------------------------------------------ efectos sincronizados
IMP = lambda t, g=1.0: add(sfx, t, S.impacto(.9), g)
WH = lambda t, g=.5, arriba=True, d=.7: add(sfx, t - d * .6, S.whoosh(d, .45, arriba), g)
RIS = lambda t, d=2.0, g=.5: add(sfx, t - d, S.riser(d, .35), g)
CLIC = lambda t, g=.6: add(sfx, t, S.ui_click(.3), g)
BLIP = lambda t, g=.5, f1=900, f2=1800: add(sfx, t, S.ui_blip(.25, f1, f2), g)

# intro
add(sfx, .3, S.braam(36, 2.4, .5), 1); IMP(.3, .8)
for k, t0 in enumerate([.3, .75, 1.2, 1.65, 2.1, 2.55, 3.0, 3.45, 3.9, 4.35, 4.8, 5.2]):
    WH(t0 + 1.95, .16, True, .55)
RIS(5.78, 2.0, .35); IMP(5.78, .8); add(sfx, 5.78, S.destello(.4), 1)
# título y servicios
for i in range(3): add(sfx, 6.2 + i * .14, S.whoosh(.4, .3), .5)
td = pal("v02", "experiencias") - .3
for j in range(4): BLIP(td + j * .2, .45, 700 + j * 150, 1500 + j * 200)
RIS(13.95, 1.6, .5); IMP(13.95, .6)
# interfaz de edición
for i in range(10): CLIC(14.3 + i * .09, .45)
for i in range(7): BLIP(15.5 + i * .06, .3, 1500, 2400)
RIS(17.4, 1.0, .6); WH(17.45, .6, True, .5)
# demo (cortes en 1.5, 3.0, 4.5, 7.0, 8.5 relativos a 17.5)
D0 = 17.5
add(sfx, D0, S.braam(33, 3.0, .5), 1); IMP(D0 + .02, .7)
WH(D0 + 1.5, .7, True, .6); IMP(D0 + 1.5, .35)
WH(D0 + 3.0, .8, False, .5)
RIS(D0 + 4.5, 1.2, .6); IMP(D0 + 4.5, 1.0); add(sfx, D0 + 4.5, S.destello(.35), 1)
add(sfx, D0 + 5.2, S.whoosh(1.3, .5, False), .6)          # cámara lenta
IMP(D0 + 5.85, .7); add(sfx, D0 + 5.85, S.braam(38, 1.6, .35), 1)  # caída acelerada
for i in range(5): add(sfx, D0 + 6.95 + i * .035, S.hat(.25, .03), 1, (-1) ** i * .6)  # glitch
add(sfx, D0 + 7.0, S.ui_blip(.3, 3000, 200), .8)
WH(D0 + 8.5, .5, True, .9); add(sfx, D0 + 8.5, S.braam(31, 2.5, .5), 1); IMP(D0 + 8.5, .6)
add(sfx, D0 + 9.0, S.destello(.3), 1)
# edición 2
WH(27.6, .5); IMP(27.5, .35)
for w in ("animaciones", "efectos", "transiciones", "detalle"): WH(pal("v04", w) - .05, .35, True, .45); BLIP(pal("v04", w), .3)
WH(36.4, .45)
for w in ("redes", "eventos", "marcas", "emprendimientos", "proyectos"): BLIP(pal("v05", w), .35, 1200, 2000)
# golpes
for t0, g in ((43.0, .8), (43.35, .85), (43.7, 1.0)): IMP(t0, g); add(sfx, t0, S.bombo(.9, 160), 1)
RIS(44.98, .9, .5); IMP(44.98, .9); WH(44.98, .6)
# invitaciones
add(sfx, 46.5, S.whoosh(1.4, .35, True), .5); add(sfx, 47.2, S.destello(.35), 1)
for w in ("quince", "dieciocho", "cumpleaños", "celebraciones"): add(sfx, pal("v07", w), S.campana(88, .8, .12), 1); WH(pal("v07", w), .25, True, .4)
WH(56.0, .35, True, 1.2)
for w in ("personalizado", "elegante", "sorprender"): BLIP(pal("v08", w), .3, 1000, 1600)
RIS(63.0, 1.3, .5); IMP(63.0, .7); WH(63.0, .5)
# invitación web: clics reales de la captura convertidos al tiempo de la publicidad
MAPA_INV = [(63.6, 0), (65.4, 1.8), (68.4, 4.8), (70.2, 6.2), (71.2, 9.6), (72.6, 11.2), (73.8, 14.3), (75.0, 18.2), (76.2, 21.6), (81.0, 25.9)]
inv = lambda c: float(np.interp(c, [b for a, b in MAPA_INV], [a for a, b in MAPA_INV]))
for c in (1.8, 14.0, 17.4, 19.0, 21.3, 23.2, 24.0): CLIC(inv(c + .2), .7)
add(sfx, inv(2.0), S.whoosh(1.0, .35, True), .5); add(sfx, inv(3.2), S.destello(.3), 1)
for i in range(13): add(sfx, inv(22.0 + i / 14), S.ui_click(.12, 3200), .5)  # tecleo
WH(68.3, .5)
for a in (68.8, 71.2, 73.4, 74.9, 76.5, 78.3): BLIP(a, .35, 900, 1700)
WH(81.6, .45)
for i in range(5): WH(83.0 + i * .28 + .3, .25, True, .4); add(sfx, 83.5 + i * .28, S.ui_blip(.22, 1400, 2600), .6)
RIS(86.48, 1.4, .5); IMP(86.48, .6)
# páginas web
for i in range(15): CLIC(87.0 + i * .08, .25)
for j in range(6): BLIP(87.6 + j * .14, .3, 800 + j * 100, 1400 + j * 100)
MAPAS = {"tiendaD": [(88.8, 0), (96.5, 9.0)], "servD": [(96.5, 0), (102.5, 10.4)], "brasaD": [(102.5, 0), (108.6, 9.0)]}
TAPS = {"tiendaD": [4.4, 5.6, 6.5], "servD": [7.1, 8.3, 9.4], "brasaD": [4.4, 5.1, 5.9, 6.7, 7.7]}
for k, taps in TAPS.items():
    (a, x), (b, y) = MAPAS[k]
    for c in taps: CLIC(a + (c + .2 - x) * (b - a) / (y - x), .7)
for c in range(15): add(sfx, 96.5 + (7.4 + c / 22) * 6 / 10.4, S.ui_click(.1, 3400), .45)
for c in range(16): add(sfx, 96.5 + (8.6 + c / 26) * 6 / 10.4, S.ui_click(.1, 3400), .45)
for t0 in (96.2, 102.2): WH(t0 + .35, .6, True, .6)
for a in (92.4, 94.2, 92.0, 97.6, 98.7, 99.8, 104.1, 105.4, 107.4): BLIP(a, .3, 1000, 1800)
RIS(109.0, 1.5, .55); IMP(109.0, .7)
# cierre
add(sfx, 109.2, S.whoosh(2.2, .4, True), .5)
RIS(112.4, 1.4, .4); IMP(112.4, .75); add(sfx, 112.4, S.braam(33, 2.6, .3), 1); add(sfx, 112.45, S.destello(.45), 1)
for t0 in (112.6, 113.2, 113.5): add(sfx, t0, S.bombo(.5, 120), 1)
IMP(115.8, .45); WH(115.8, .4)
for j in range(3): BLIP(117.7 + j * .22, .35, 900, 1800)
WH(119.0, .4)
for i in range(38): add(sfx, 120.2 + i * 1.5 / 38, S.ui_click(.1, 3000 + (i % 3) * 300), .5)
CLIC(121.95, .8); WH(122.25, .6, True, .7)
IMP(123.0, .55); add(sfx, 123.0, S.destello(.4), 1)
for i in range(18): add(sfx, 124.0 + i * .045, S.ui_click(.08, 2600 + i * 40), .5)
# sonido de marca: acorde brillante + destello + sub
for n in (57, 64, 69, 72, 76, 81):
    add(sfx, 129.6, S.campana(n, 3.0, .08), 1, (n - 69) / 15)
add(sfx, 129.6, S.sub(33, 2.5, .35), 1); add(sfx, 129.6, S.destello(.5), 1); add(sfx, 129.4, S.whoosh(.8, .3, True), .5)

# ------------------------------------------------------------------ voz
voz = np.zeros(N)
for vid, t0 in TL["voz"].items():
    sr, x = wavfile.read(B / f"voz/{vid}.wav")
    x = x.astype(np.float64) / 32768
    i = int(t0 * SR); voz[i:i + len(x)] += x[:N - i]
# procesamiento: paso alto, limpieza de medios graves, presencia y compresión suave
voz = S.hp(voz, 85)
voz = voz - .18 * S.bp(voz, 220, 420)
voz = voz + .22 * S.bp(voz, 2500, 5000)
env = np.sqrt(S.lp(voz ** 2, 12) .clip(0) + 1e-9)
umbral = .08
gan = np.where(env > umbral, (umbral / env) ** (1 - 1 / 2.5), 1.0)
voz = voz * gan
voz = voz / (np.max(np.abs(voz)) + 1e-9) * .9
voz = S.reverb(voz, .6, .06, 6000)
voz2 = np.stack([voz, voz], 1)

# ducking: la música baja cuando hay voz
act = S.lp((np.abs(voz) > .02).astype(float), 3)
act = np.clip(act * 3, 0, 1)
duck_m = 1 - .62 * act
duck_s = 1 - .6 * act
musica = mus * duck_m[:, None]
efectos = sfx * duck_s[:, None]
fx = musica * .55 + efectos * .8
fx[:, 0] = S.reverb(fx[:, 0], 1.8, .12); fx[:, 1] = S.reverb(fx[:, 1], 1.8, .12)
# fundidos
tt = np.arange(N) / SR
fade = np.clip(tt / .05, 0, 1) * np.clip((DUR - tt) / 1.4, 0, 1)
fx *= fade[:, None]
voz2 *= fade[:, None]
mezcla = fx * .62 + voz2 * .95
mezcla = np.tanh(mezcla * 1.1) / 1.1


def guardar(nombre, x):
    S.guardar_wav(str(B / nombre), x / max(1, np.max(np.abs(x)) / .98))


guardar("musica_efectos.wav", fx[: int(DUR * SR)])
guardar("voz_completa.wav", voz2[: int(DUR * SR)])
guardar("mezcla_final.wav", mezcla[: int(DUR * SR)])
d = fx[int(17.5 * SR): int(27.5 * SR)].copy()
td = np.arange(len(d)) / SR
d *= (np.clip(td / .03, 0, 1) * np.clip((10 - td) / .5, 0, 1))[:, None]
guardar("demo_edicion.wav", d)
print("ok", DUR)
