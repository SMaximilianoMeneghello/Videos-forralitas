"""Sintetiza una base musical corta (24 s) para el video, sin archivos externos."""
import sys, wave
import numpy as np

SR = 44100
DUR = 24.0
BPM = 112
BEAT = 60 / BPM
N = int(SR * DUR)
t = np.arange(N) / SR
rng = np.random.default_rng(7)


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def env_pluck(length, decay):
    x = np.arange(int(length * SR)) / SR
    return np.exp(-x * decay) * np.minimum(1, x * 200)


def add(buf, start, sig, gain=1.0):
    i = int(start * SR)
    if i >= N:
        return
    j = min(N, i + len(sig))
    buf[i:j] += sig[: j - i] * gain


def tone(freq, length, decay, harmonics=(1, .5, .25, .12)):
    x = np.arange(int(length * SR)) / SR
    s = sum(a * np.sin(2 * np.pi * freq * (k + 1) * x) for k, a in enumerate(harmonics))
    return s * env_pluck(length, decay)


mix = np.zeros(N)
# progresión Am - F - C - G (cada acorde 4 pulsos)
chords = [(57, 60, 64), (53, 57, 60), (48, 52, 55), (55, 59, 62)]
bar = BEAT * 4
for b in range(int(DUR / bar) + 1):
    ch = chords[b % 4]
    st = b * bar
    # pad suave
    L = bar + .4
    x = np.arange(int(L * SR)) / SR
    pad = np.zeros_like(x)
    for n in ch:
        for det in (-.003, 0, .003):
            pad += np.sin(2 * np.pi * midi(n) * (1 + det) * x) * .12
    e = np.minimum(1, x / .5) * np.minimum(1, (L - x) / .4)
    add(mix, st, pad * e, .55)
    # bajo
    for k in range(4):
        add(mix, st + k * BEAT, tone(midi(ch[0] - 24), BEAT * .95, 4, (1, .4)), .55)
    # arpegio en corcheas
    for k in range(8):
        n = ch[[0, 1, 2, 1][k % 4]] + 12 + (12 if k % 8 >= 4 else 0)
        add(mix, st + k * BEAT / 2, tone(midi(n), .5, 7), .22)

# percusión desde la escena 2
def kick(freq0=120, L=.28):
    x = np.arange(int(L * SR)) / SR
    f = 45 + (freq0 - 45) * np.exp(-x * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 11)


def hat(L=.06):
    x = np.arange(int(L * SR)) / SR
    return rng.standard_normal(len(x)) * np.exp(-x * 70)


K = kick()
H = hat()
nb = int(DUR / BEAT)
for i in range(nb):
    ts = i * BEAT
    if ts >= 3.5:
        add(mix, ts, K, .7)
        add(mix, ts + BEAT / 2, H, .12)
    if ts >= 9.3 and i % 2 == 1:
        sn = rng.standard_normal(int(.15 * SR)) * np.exp(-np.arange(int(.15 * SR)) / SR * 28)
        add(mix, ts, sn, .25)

# risers + impacto en cada transición
for tt in (3.5, 9.3, 15.3, 19.5):
    L = .8
    x = np.arange(int(L * SR)) / SR
    noise = rng.standard_normal(len(x)) * (x / L) ** 2 * .22
    sweep = np.sin(2 * np.pi * np.cumsum(300 + 2500 * (x / L) ** 2) / SR) * (x / L) * .12
    add(mix, tt - L + .1, noise + sweep, 1)
    imp = np.sin(2 * np.pi * np.cumsum(90 * np.exp(-x * 4) + 38) / SR) * np.exp(-x * 4)
    add(mix, tt + .1, imp, .9)

# acorde final brillante
for n in (69, 72, 76, 81):
    add(mix, 19.6, tone(midi(n), 4.2, 1.1), .18)

# fade in/out
mix *= np.minimum(1, t / .5) * np.minimum(1, (DUR - t) / 1.2)
mix = np.tanh(mix * 1.2)
mix = mix / np.max(np.abs(mix)) * .8
pcm = (mix * 32767).astype("<i2")
stereo = np.stack([pcm, np.roll(pcm, 40)], axis=1)  # leve ancho estéreo
out = sys.argv[1] if len(sys.argv) > 1 else "musica.wav"
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(stereo.tobytes())
print("ok", out)
