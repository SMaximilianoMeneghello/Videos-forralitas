"""Música de fondo suave (piano eléctrico + colchón cálido) pensada para acompañar una locución."""
import numpy as np
from scipy.signal import butter, sosfilt

SR = 44100
BPM = 66
BEAT = 60 / BPM
rng = np.random.default_rng(23)


TRANSP = 0


def nota(m):
    return 440 * 2 ** ((m + TRANSP - 69) / 12)


def _t(d):
    return np.arange(int(d * SR)) / SR


def _filtro(x, tipo, fc, orden=2):
    return sosfilt(butter(orden, fc, btype=tipo, fs=SR, output="sos"), x)


def piano_e(f, dur=2.4):
    """Piano eléctrico suave (FM): ataque redondo y decaimiento largo."""
    t = _t(dur)
    mod = np.sin(2 * np.pi * f * t) * 1.5 * np.exp(-t * 6.5)
    s = np.sin(2 * np.pi * f * t + mod) + 0.22 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t * 4)
    env = np.minimum(t / 0.006, 1) * np.exp(-t * 1.9) * np.minimum((dur - t) / 0.25, 1).clip(0, 1)
    return s * env


def colchon(midis, dur):
    t = _t(dur)
    s = 0
    for m in midis:
        f = nota(m)
        s = s + np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 1.004 * t + 1.1)
    env = np.minimum(t / 1.6, 1) * np.minimum((dur - t) / 1.6, 1).clip(0, 1)
    return _filtro(s * env / len(midis), "lowpass", 900)


def bajo(f, dur):
    t = _t(dur)
    return np.sin(2 * np.pi * f * t) * np.exp(-t * 1.3) * np.minimum(t / 0.02, 1) * np.minimum((dur - t) / 0.2, 1).clip(0, 1)


def _poner(buf, x, inicio, g=1.0, pan=0.5):
    i = int(max(inicio, 0) * SR)
    if i >= buf.shape[0]:
        return
    n = min(x.size, buf.shape[0] - i)
    buf[i:i + n, 0] += x[:n] * g * (1 - pan) * 2 * 0.5
    buf[i:i + n, 1] += x[:n] * g * pan * 2 * 0.5


def _reverb(buf, mezcla=0.28, dur=2.2):
    from scipy.signal import fftconvolve
    n = int(dur * SR)
    env = np.exp(-np.arange(n) / SR * 2.6)
    out = np.empty_like(buf)
    for c in range(2):
        ir = _filtro(rng.standard_normal(n), "lowpass", 3800) * env
        ir /= np.abs(ir).sum() * 0.35
        out[:, c] = fftconvolve(buf[:, c], ir)[:buf.shape[0]]
    return buf * (1 - mezcla * 0.5) + out * mezcla


# Fa mayor: F - C - Dm - Bb   (bajo, acorde)
ACORDES = [(41, (60, 65, 69, 72)), (48, (60, 64, 67, 72)), (50, (62, 65, 69, 74)), (46, (58, 62, 65, 70))]


def musica(duracion):
    n = int((duracion + 1.0) * SR)
    buf = np.zeros((n, 2))
    compases = int(duracion / (4 * BEAT)) + 2
    for c in range(compases):
        bj, ac = ACORDES[c % 4]
        t0 = c * 4 * BEAT
        _poner(buf, colchon([m - 12 for m in ac[:3]], 4 * BEAT + 1.2), t0, 0.16, 0.5)
        _poner(buf, bajo(nota(bj), 2 * BEAT), t0, 0.34, 0.5)
        _poner(buf, bajo(nota(bj + (7 if c % 2 == 0 else 0)), 2 * BEAT), t0 + 2 * BEAT, 0.20, 0.5)
        patron = [0, 1, 2, 3, 2, 1, 2, 1]
        for k, p in enumerate(patron):
            t = t0 + k * BEAT / 2 + rng.normal(0, 0.005)
            vel = 0.20 + (0.05 if k in (0, 4) else 0) + rng.uniform(-0.02, 0.02)
            _poner(buf, piano_e(nota(ac[p] + 12 * (k in (3, 7)))), t, vel, 0.4 + 0.2 * (k % 2))
        if c % 4 == 0:           # melodía simple, grave y espaciada
            for k, m in enumerate((ac[3] + 12, ac[2] + 12)):
                _poner(buf, piano_e(nota(m), 3.0), t0 + (1.5 + 1.5 * k) * BEAT, 0.12, 0.62)
    buf = _reverb(buf)
    # dejar espacio a la voz: sin brillo y con un hueco suave en las frecuencias del habla
    for c in range(2):
        x = _filtro(buf[:, c], "lowpass", 3400)
        buf[:, c] = x - 0.30 * _filtro(x, "bandpass", [1200, 3000])
    return buf[:int(duracion * SR)]
