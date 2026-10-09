"""Música de campo tranquila (guitarra criolla + silbido + ambiente) sintetizada por código."""
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, fftconvolve, lfilter, sosfilt

SR = 44100
BPM = 76
BEAT = 60 / BPM
rng = np.random.default_rng(11)


def nota(m):
    return 440 * 2 ** ((m - 69) / 12)


def _t(d):
    return np.arange(int(d * SR)) / SR


def _filtro(x, tipo, fc, orden=2):
    return sosfilt(butter(orden, fc, btype=tipo, fs=SR, output="sos"), x)


def cuerda(f, dur=2.6, g=0.9965, suave=0.55):
    """Cuerda pulsada (Karplus-Strong): suena a guitarra criolla."""
    N = max(int(round(SR / f - 0.5)), 2)
    n = int(dur * SR)
    x = np.zeros(n)
    exc = rng.uniform(-1, 1, N)
    for _ in range(2):                       # excitación suavizada = pulsación con yema
        exc = (1 - suave) * exc + suave * np.roll(exc, 1)
    x[:N] = exc - exc.mean()
    a = np.zeros(N + 2)
    a[0], a[N], a[N + 1] = 1, -g / 2, -g / 2
    y = lfilter([1.0], a, x)
    y = _filtro(y, "lowpass", 5200)
    return y / (np.abs(y).max() + 1e-9)


def silbido(f, dur, vibrato=True):
    t = _t(dur)
    vib = 1 + (0.006 * np.sin(2 * np.pi * 5.2 * t) * np.minimum(t / 0.35, 1) if vibrato else 0)
    fase = 2 * np.pi * np.cumsum(f * vib) / SR
    s = np.sin(fase) + 0.12 * np.sin(2 * fase)
    env = np.minimum(t / 0.09, 1) * np.minimum((dur - t) / 0.45, 1).clip(0, 1)
    soplo = _filtro(rng.standard_normal(t.size), "bandpass", [2200, 3600]) * 0.02
    return (s + soplo) * env


def colchon(freqs, dur):
    t = _t(dur)
    s = sum(np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.003 * t) for f in freqs)
    env = np.minimum(t / 1.2, 1) * np.minimum((dur - t) / 1.2, 1).clip(0, 1)
    return _filtro(s * env / len(freqs), "lowpass", 1400)


def shaker():
    t = _t(0.09)
    return _filtro(rng.standard_normal(t.size), "highpass", 5500) * np.exp(-t * 45)


def bombo_suave():
    t = _t(0.35)
    f = 52 + 40 * np.exp(-t * 22)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 8)


def trino(f):
    t = _t(0.16)
    barrido = f * (1 + 0.45 * (1 - np.exp(-t * 40)))
    s = np.sin(2 * np.pi * np.cumsum(barrido) / SR)
    return s * np.exp(-t * 18) * np.sin(np.pi * np.minimum(t / 0.16, 1)) * 0.6


def pajaros(dur):
    out = np.zeros((int(dur * SR), 2))
    t = 2.5
    while t < dur - 1.5:
        f0 = rng.uniform(2600, 4200)
        pan = rng.uniform(0.2, 0.8)
        for k in range(rng.integers(2, 5)):
            c = trino(f0 * rng.uniform(0.9, 1.15))
            i = int((t + k * 0.19) * SR)
            n = min(c.size, out.shape[0] - i)
            if n > 0:
                out[i:i + n, 0] += c[:n] * (1 - pan) * 0.5
                out[i:i + n, 1] += c[:n] * pan * 0.5
        t += rng.uniform(4.5, 8.5)
    return out


def viento(dur):
    n = int(dur * SR)
    r = _filtro(rng.standard_normal(n), "lowpass", 420, 2)
    lento = 0.55 + 0.45 * np.sin(2 * np.pi * np.arange(n) / SR / 9.0 + 1.3)
    return r * lento


def campana(f):
    t = _t(1.2)
    s = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 6)
    return s * np.exp(-t * 4.5) * np.minimum(t / 0.004, 1)


def sutil_viento(dur=0.9):
    t = _t(dur)
    r = _filtro(rng.standard_normal(t.size), "bandpass", [300, 1800])
    return r * np.sin(np.pi * t / dur) ** 2 * 0.9


def _poner(buf, x, inicio, g=1.0, pan=0.5):
    i = int(max(inicio, 0) * SR)
    if i >= buf.shape[0]:
        return
    n = min(x.size, buf.shape[0] - i)
    buf[i:i + n, 0] += x[:n] * g * (1 - pan) * 2 * 0.5
    buf[i:i + n, 1] += x[:n] * g * pan * 2 * 0.5


def _reverb(buf, mezcla=0.24, dur=1.9):
    n = int(dur * SR)
    env = np.exp(-np.arange(n) / SR * 3.2)
    out = np.empty_like(buf)
    for c in range(2):
        ir = _filtro(rng.standard_normal(n), "lowpass", 4500) * env
        ir /= np.abs(ir).sum() * 0.35
        out[:, c] = fftconvolve(buf[:, c], ir)[:buf.shape[0]]
    return buf * (1 - mezcla * 0.5) + out * mezcla


# acordes: (bajo, bajo alterno, arpegio)  G - D - Em - C
ACORDES = [
    (43, 50, (55, 59, 62, 67)),
    (50, 45, (57, 62, 66, 69)),
    (40, 47, (55, 59, 64, 67)),
    (48, 43, (55, 60, 64, 67)),
]
# melodía de silbido (compases de 4 tiempos): (tiempo dentro del bucle de 4 compases, duración, nota)
MELODIA = [(0, 2, 71), (2, 1, 69), (3, 1, 67), (4, 3, 69), (8, 2, 74), (10, 1, 76), (11, 1, 74),
           (12, 3, 71), (14, 0, 0)]


def generar(duracion, t_transiciones, t_dings, t_campanas, t_melodia=3.5,
            ruta="videos_salida/_musica_campo.wav"):
    n = int((duracion + 1.0) * SR)
    inst = np.zeros((n, 2))
    n_compases = int(duracion / (4 * BEAT)) + 2
    for c in range(n_compases):
        bajo, alt, arp = ACORDES[c % 4]
        t0 = c * 4 * BEAT
        _poner(inst, colchon([nota(m) for m in (bajo + 12, arp[0], arp[1], arp[2])], 4 * BEAT + 1.0),
               t0, 0.10, 0.5)
        patron = [("b", bajo), ("a", arp[0]), ("a", arp[1]), ("a", arp[2]),
                  ("b", alt), ("a", arp[1]), ("a", arp[2]), ("a", arp[3])]
        for k, (tipo, m) in enumerate(patron):
            t = t0 + k * BEAT / 2 + rng.normal(0, 0.006) + (0.012 if k % 2 else 0)   # leve swing
            if tipo == "b":
                _poner(inst, cuerda(nota(m), 3.0, 0.9975), t, 0.55, 0.42)
            else:
                vel = 0.30 + 0.07 * (k in (1, 5)) + rng.uniform(-0.03, 0.03)
                _poner(inst, cuerda(nota(m), 2.2), t, vel, 0.58 + 0.06 * (k % 3 - 1))
            if t0 > 6 and k % 2 == 1:
                _poner(inst, shaker(), t + 0.02, 0.05 + 0.02 * (k == 3), 0.62)
        if t0 > 6 and c % 2 == 0:
            _poner(inst, bombo_suave(), t0, 0.22, 0.5)
            _poner(inst, bombo_suave(), t0 + 2 * BEAT, 0.15, 0.5)
    # silbido
    c0 = 0
    while True:
        base = t_melodia + c0 * 16 * BEAT
        if base > duracion:
            break
        for beat, dur, m in MELODIA:
            if m:
                _poner(inst, silbido(nota(m), dur * BEAT + 0.3), base + beat * BEAT, 0.16, 0.5)
        c0 += 1
    inst = _reverb(inst)
    amb = np.zeros((n, 2))
    v = viento(duracion + 1.0)
    amb[:, 0] += v[:n] * 0.05
    amb[:, 1] += np.roll(v, 7000)[:n] * 0.05
    amb += pajaros(duracion + 1.0)[:n] * 0.9
    buf = inst + amb
    for t in t_transiciones:
        _poner(buf, sutil_viento(), t, 0.22)
    for t in t_dings:
        _poner(buf, campana(nota(79)), t, 0.18)
    for t in t_campanas:
        _poner(buf, campana(nota(76)), t, 0.2)
        _poner(buf, campana(nota(83)), t + 0.22, 0.16)
    buf = np.tanh(buf * 1.25)[:int(duracion * SR)]
    fi, fo = int(1.2 * SR), int(2.8 * SR)
    buf[:fi] *= np.linspace(0, 1, fi)[:, None]
    buf[-fo:] *= np.linspace(1, 0, fo)[:, None]
    buf *= 0.88 / max(np.abs(buf).max(), 1e-6)
    wavfile.write(ruta, SR, (buf * 32767).astype(np.int16))
    return ruta


if __name__ == "__main__":
    print(generar(20, [5, 10], [8], [15], ruta="videos_salida/_prueba_campo.wav"))
