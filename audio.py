"""Música de fondo y efectos de sonido sintetizados (sin derechos de autor)."""
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

SR = 44100
BPM = 112
BEAT = 60 / BPM
rng = np.random.default_rng(7)


def _t(dur):
    return np.arange(int(dur * SR)) / SR


def nota(m):
    return 440 * 2 ** ((m - 69) / 12)


def _filtro(x, tipo, fc):
    sos = butter(3, fc, btype=tipo, fs=SR, output="sos")
    return sosfilt(sos, x)


def bombo():
    t = _t(0.3)
    f = 45 + 100 * np.exp(-t * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)


def palmada():
    t = _t(0.2)
    return _filtro(rng.standard_normal(t.size), "bandpass", [900, 3500]) * np.exp(-t * 24) * 2.2


def hihat():
    t = _t(0.07)
    return _filtro(rng.standard_normal(t.size), "highpass", 7000) * np.exp(-t * 65)


def pluck(f, dur=0.4):
    t = _t(dur)
    s = np.sin(2 * np.pi * f * t) + 0.4 * np.sin(4 * np.pi * f * t) + 0.18 * np.sin(6 * np.pi * f * t)
    return s * np.exp(-t * 9) * np.minimum(t / 0.004, 1)


def bajo(f, dur):
    t = _t(dur)
    s = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t)
    return s * np.exp(-t * 3.5) * np.minimum(t / 0.008, 1)


def colchon(freqs, dur):
    t = _t(dur)
    s = sum(np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 1.005 * t) for f in freqs)
    env = np.minimum(t / 0.5, 1) * np.minimum((dur - t) / 0.5, 1)
    return s * env / len(freqs)


def whoosh(dur=0.7):
    n = int(dur * SR)
    ruido = rng.standard_normal(n)
    tt = np.linspace(0, 1, n)
    fc = 250 * (24 ** np.sin(np.pi * tt))        # barrido 250 -> 6000 -> 250 Hz
    alfa = 1 - np.exp(-2 * np.pi * fc / SR)
    out = np.empty(n)
    y = 0.0
    for i in range(n):
        y += alfa[i] * (ruido[i] - y)
        out[i] = y
    env = np.sin(np.pi * tt) ** 1.5
    return out * env * 3.0


def golpe():
    t = _t(0.9)
    return (np.sin(2 * np.pi * 70 * t) * np.exp(-t * 5)
            + _filtro(rng.standard_normal(t.size), "lowpass", 1800) * np.exp(-t * 6) * 0.6)


def _poner(buf, x, inicio, ganancia=1.0, pan=0.5):
    i = int(inicio * SR)
    if i >= buf.shape[0]:
        return
    n = min(x.size, buf.shape[0] - i)
    buf[i:i + n, 0] += x[:n] * ganancia * (1 - pan) * 2 * 0.5
    buf[i:i + n, 1] += x[:n] * ganancia * pan * 2 * 0.5


def generar(duracion, t_transiciones, t_drop, t_golpes, ruta="videos_salida/_musica.wav"):
    buf = np.zeros((int((duracion + 0.5) * SR), 2))
    acordes = [(48, (0, 4, 7)), (55, (0, 4, 7)), (57, (0, 3, 7)), (53, (0, 4, 7))]  # C G Am F
    n_beats = int(duracion / BEAT) + 2
    for i in range(n_beats):
        t0 = i * BEAT
        raiz, ints = acordes[(i // 4) % 4]
        notas = [raiz + k for k in ints]
        if i % 4 == 0:
            _poner(buf, colchon([nota(m) for m in notas], 4 * BEAT + 0.3), t0, 0.14)
        # bajo
        _poner(buf, bajo(nota(raiz - 12), BEAT * 0.9), t0, 0.5 if t0 >= t_drop else 0.3)
        if t0 >= t_drop:
            _poner(buf, bombo(), t0, 0.95)
            _poner(buf, bajo(nota(raiz - 12), BEAT * 0.45), t0 + BEAT / 2, 0.35)
            if i % 2 == 1:
                _poner(buf, palmada(), t0, 0.5)
            _poner(buf, hihat(), t0 + BEAT / 2, 0.22)
            _poner(buf, hihat(), t0 + BEAT / 4, 0.1)
            _poner(buf, hihat(), t0 + BEAT * 3 / 4, 0.1)
        # arpegio en corcheas
        patron = [0, 1, 2, 1] if t0 >= t_drop else [0, 2]
        paso = BEAT / len(patron)
        for j, p in enumerate(patron):
            m = notas[p % 3] + 24 + (12 if j == len(patron) - 1 and t0 >= t_drop else 0)
            _poner(buf, pluck(nota(m)), t0 + j * paso, 0.2, pan=0.35 if j % 2 else 0.65)
    for t in t_transiciones:
        _poner(buf, whoosh(), t, 0.5)
    for t in t_golpes:
        _poner(buf, golpe(), t, 0.7)
    buf = np.tanh(buf * 1.1)
    n = int(duracion * SR)
    buf = buf[:n]
    fade_in, fade_out = int(0.4 * SR), int(1.8 * SR)
    buf[:fade_in] *= np.linspace(0, 1, fade_in)[:, None]
    buf[-fade_out:] *= np.linspace(1, 0, fade_out)[:, None]
    buf *= 0.9 / max(np.abs(buf).max(), 1e-6)
    wavfile.write(ruta, SR, (buf * 32767).astype(np.int16))
    return ruta
