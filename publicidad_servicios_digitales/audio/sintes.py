"""Pequeña biblioteca de síntesis (numpy/scipy) para la banda sonora y los efectos. Todo el audio es original."""
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve

SR = 48000
RNG = np.random.default_rng(11)


def midi(n):
    return 440.0 * 2 ** ((np.asarray(n) - 69) / 12)


def tt(dur):
    return np.arange(int(dur * SR)) / SR


def adsr(n, a=.01, d=.1, s=.7, r=.2, dur=None):
    t = np.arange(n) / SR
    dur = dur if dur is not None else n / SR
    e = np.where(t < a, t / max(a, 1e-4), np.where(t < a + d, 1 - (1 - s) * (t - a) / max(d, 1e-4), s))
    rel = np.clip((dur - t) / max(r, 1e-4), 0, 1)
    return e * rel


def lp(x, f, order=2):
    return sosfilt(butter(order, min(f, SR / 2 - 100), "low", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, "high", fs=SR, output="sos"), x)


def bp(x, f1, f2, order=2):
    return sosfilt(butter(order, [f1, f2], "band", fs=SR, output="sos"), x)


def saw(f, t, det=0.0):
    ph = (f * (1 + det) * t) % 1.0
    return 2 * ph - 1


def pad(notas, dur, brillo=1800, vol=.12, ataque=.8, rel=1.0):
    t = tt(dur)
    x = np.zeros_like(t)
    for n in notas:
        for d in (-.004, -.0015, .0015, .004):
            x += saw(midi(n), t + RNG.random() * 3, d)
    x = lp(x, brillo, 2) * vol / max(1, len(notas))
    return x * adsr(len(t), ataque, .3, .9, rel, dur)


def campana(n, dur=1.6, vol=.3, brillo=1.0):
    t = tt(dur)
    f = midi(n)
    x = (np.sin(2 * np.pi * f * t) + .45 * brillo * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 6)
         + .25 * brillo * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 11) + .3 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t * 3))
    return x * np.exp(-t * 2.6) * np.minimum(1, t * 400) * vol


def pluck(n, dur=.6, vol=.25, corte=3500, decay=6):
    t = tt(dur)
    f = midi(n)
    x = saw(f, t, 0) * .6 + saw(f, t, .006) * .4
    x = lp(x * np.exp(-t * decay), corte, 2)
    return x * np.minimum(1, t * 300) * vol


def sub(n, dur, vol=.4):
    t = tt(dur)
    return np.sin(2 * np.pi * midi(n) * t) * adsr(len(t), .01, .1, .8, .08, dur) * vol


def bombo(vol=.9, f0=140, dur=.45):
    t = tt(dur)
    f = 42 + (f0 - 42) * np.exp(-t * 28)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7.5)
    click = hp(RNG.standard_normal(len(t)), 3000) * np.exp(-t * 300) * .3
    return np.tanh((x + click) * 1.6) * vol


def palmas(vol=.4, dur=.3):
    t = tt(dur)
    n = bp(RNG.standard_normal(len(t)), 900, 5000)
    env = np.exp(-t * 22) + .6 * np.exp(-((t - .012) * 400) ** 2) + .5 * np.exp(-((t - .024) * 400) ** 2)
    return n * env * vol


def hat(vol=.12, dur=.08, abierto=False):
    dur = .35 if abierto else dur
    t = tt(dur)
    return hp(RNG.standard_normal(len(t)), 7000) * np.exp(-t * (9 if abierto else 60)) * vol


def riser(dur=2.0, vol=.35, f1=200, f2=6000):
    t = tt(dur)
    k = (t / dur) ** 2
    ruido = RNG.standard_normal(len(t))
    out = np.zeros_like(t)
    # barrido de filtro por bloques
    blk = 1024
    for i in range(0, len(t), blk):
        f = f1 + (f2 - f1) * k[min(i, len(k) - 1)]
        out[i:i + blk] = bp(ruido[i:i + blk + 0], max(60, f * .6), min(SR / 2 - 200, f * 1.4), 1)[:len(out[i:i + blk])]
    tono = np.sin(2 * np.pi * np.cumsum(300 + 1500 * k) / SR) * .25
    return (out * 1.3 + tono) * k * vol


def whoosh(dur=.7, vol=.4, arriba=True):
    t = tt(dur)
    pos = t / dur
    env = np.sin(np.pi * pos) ** 2
    ruido = RNG.standard_normal(len(t))
    out = np.zeros_like(t)
    blk = 512
    for i in range(0, len(t), blk):
        p = pos[i]
        f = 400 + 3200 * (p if arriba else 1 - p)
        out[i:i + blk] = bp(ruido[i:i + blk], f * .5, min(f * 1.6, SR / 2 - 200), 1)
    return out * env * vol


def impacto(vol=.9, dur=2.5):
    t = tt(dur)
    boom = np.sin(2 * np.pi * np.cumsum(30 + 90 * np.exp(-t * 5)) / SR) * np.exp(-t * 2.2)
    cola = lp(RNG.standard_normal(len(t)), 900) * np.exp(-t * 3.5) * .5
    crack = hp(RNG.standard_normal(len(t)), 2000) * np.exp(-t * 40) * .4
    return np.tanh((boom * 1.4 + cola + crack) * 1.2) * vol


def braam(n=38, dur=3.0, vol=.5):
    t = tt(dur)
    x = sum(saw(midi(n + o), t, d) for o in (0, 12, 7) for d in (-.006, .006))
    env = adsr(len(t), .05, .4, .6, 1.4, dur)
    corte = 300 + 2500 * np.exp(-t * 1.5)
    out = np.zeros_like(t)
    blk = 1024
    for i in range(0, len(t), blk):
        out[i:i + blk] = lp(x[i:i + blk], corte[i], 2)
    return np.tanh(out * env * 1.5) * vol


def ui_click(vol=.25, f=2400):
    t = tt(.06)
    return np.sin(2 * np.pi * f * t) * np.exp(-t * 90) * vol + hp(RNG.standard_normal(len(t)), 5000) * np.exp(-t * 300) * vol * .3


def ui_blip(vol=.2, f1=900, f2=1800):
    t = tt(.12)
    return np.sin(2 * np.pi * np.cumsum(f1 + (f2 - f1) * t / .12) / SR) * np.exp(-t * 30) * vol


def destello(vol=.25):
    t = tt(1.5)
    x = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * (3 + i)) for i, f in enumerate((2093, 2637, 3136, 4186)))
    return x * np.minimum(1, t * 200) * vol / 2


def reverb(x, dur=2.4, mezcla=.25, brillo=5000):
    t = tt(dur)
    ir = RNG.standard_normal(len(t)) * np.exp(-t * 6.9 / dur)
    ir = lp(ir, brillo)
    ir /= np.sqrt(np.sum(ir ** 2))
    w = fftconvolve(x, ir)[:len(x)]
    return x * (1 - mezcla) + w * mezcla * 1.2


def poner(buf, inicio, sig, gan=1.0):
    i = int(round(inicio * SR))
    if i < 0:
        sig = sig[-i:]; i = 0
    j = min(len(buf), i + len(sig))
    if j > i:
        buf[i:j] += sig[:j - i] * gan


def guardar_wav(ruta, est):
    from scipy.io import wavfile
    est = np.asarray(est)
    wavfile.write(ruta, SR, (np.clip(est, -1, 1) * 32767).astype("<i2"))
