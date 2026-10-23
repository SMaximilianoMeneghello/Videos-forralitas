"""Locución, música original sintetizada y efectos de sonido para los videos de FORRALITAS.

* Música y efectos se generan desde cero con numpy (sin samples ni canciones de terceros): no hay derechos de
  autor que cuidar y se pueden usar en publicidad comercial.
* Locución: voz neuronal de Edge (es-AR-TomasNeural) si el entorno la permite; si no, voz masculina de Piper.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

SR = 44100
rng = np.random.default_rng(7)
PIPER_MODELO = os.environ.get("PIPER_MODELO", str(Path("/tmp/claude-0/-home-user-Videos-forralitas/df62490c-9a54-5d48-b887-16a37994cf35/scratchpad/pv/es_MX-claude-high.onnx")))
CACHE = RAIZ / "FORRALITAS/audios/cache"
ESTADO = {"motor": None}          # qué motor de voz se usó realmente


# ------------------------------------------------------------------ locución
def _edge(texto, ruta_mp3):
    import voz_tts
    voz_tts.sintetizar(texto, "es-AR-TomasNeural", str(ruta_mp3), rate="+4%")


def _piper(texto, ruta_wav, ritmo=0.9):
    subprocess.run([sys.executable, "-m", "piper", "-m", PIPER_MODELO, "-f", str(ruta_wav), "--length-scale", str(ritmo),
                    "--noise-scale", "0.75", "--noise-w-scale", "0.85", "--", texto], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _recortar(x):
    idx = np.where(np.abs(x) > 0.012)[0]
    return x[max(idx[0] - int(0.03 * SR), 0): idx[-1] + int(0.06 * SR)]


def voz(texto, ritmo=0.9):
    """Devuelve (audio float32 mono a 44,1 kHz, [(palabra, inicio_s)]) de la frase."""
    CACHE.mkdir(parents=True, exist_ok=True)
    h = hashlib.md5(f"{PIPER_MODELO}|{ritmo}|{texto}".encode()).hexdigest()[:12]
    wav = CACHE / f"{h}.wav"
    if not wav.exists():
        crudo = CACHE / f"{h}_raw.wav"
        motor = ESTADO["motor"]
        if motor in (None, "edge"):
            try:
                mp3 = CACHE / f"{h}.mp3"
                _edge(texto, mp3)
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(mp3), "-ac", "1", "-ar", str(SR), str(wav)], check=True)
                ESTADO["motor"] = "edge"
            except Exception:
                ESTADO["motor"] = "piper"
        if ESTADO["motor"] == "piper":
            _piper(texto, crudo, ritmo)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(crudo), "-ac", "1", "-ar", str(SR), str(wav)], check=True)
    _, x = wavfile.read(wav)
    x = _recortar(x.astype(np.float32) / 32768)
    return x, tiempos_palabras(texto, len(x) / SR)


def tiempos_palabras(texto, dur):
    """Reparto del tiempo por palabra según su longitud y las pausas de puntuación (para subtítulos)."""
    pal = texto.split()
    pesos = []
    for p in pal:
        w = len(re.sub(r"\W", "", p)) + 1.5
        if p[-1] in ".!?":
            w += 3.2
        elif p[-1] in ",;:":
            w += 1.8
        pesos.append(w)
    tot, acum, out = sum(pesos), 0.0, []
    for p, w in zip(pal, pesos):
        out.append((p, dur * acum / tot))
        acum += w
    return out


# ------------------------------------------------------------------ instrumentos
def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def _tt(dur):
    return np.arange(int(dur * SR)) / SR


def _lp(x, fc, orden=2):
    return sosfilt(butter(orden, fc, btype="low", fs=SR, output="sos"), x)


def _hp(x, fc, orden=2):
    return sosfilt(butter(orden, fc, btype="high", fs=SR, output="sos"), x)


def _bp(x, a, b):
    return sosfilt(butter(2, [a, b], btype="band", fs=SR, output="sos"), x)


def kick(g=1.0):
    t = _tt(0.42)
    f = 48 + 120 * np.exp(-t * 30)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7.5)
    x += 0.35 * _hp(rng.normal(0, 1, t.size), 2500) * np.exp(-t * 140)
    return (x * g).astype(np.float32)


def snare(g=1.0):
    t = _tt(0.3)
    n = _bp(rng.normal(0, 1, t.size), 1800, 7500) * np.exp(-t * 17)
    return ((n + 0.5 * np.sin(2 * np.pi * 190 * t) * np.exp(-t * 28)) * g).astype(np.float32)


def clap(g=1.0):
    t = _tt(0.32)
    n = _bp(rng.normal(0, 1, t.size), 1200, 6500)
    e = sum(np.exp(-np.clip(t - d, 0, None) * 38) * (t >= d) for d in (0, 0.012, 0.026)) * 0.5 + np.exp(-t * 14) * 0.5
    return (n * e * g).astype(np.float32)


def hat(g=1.0, abierto=False):
    t = _tt(0.28 if abierto else 0.07)
    return (_hp(rng.normal(0, 1, t.size), 7000) * np.exp(-t * (18 if abierto else 70)) * g).astype(np.float32)


def bajo(nota, dur, g=1.0):
    t = _tt(dur)
    f = midi(nota)
    x = np.sin(2 * np.pi * f * t) + 0.45 * (2 * ((f * t) % 1) - 1)
    x = _lp(x, 520) * np.minimum(1, t / 0.008) * np.exp(-t * 2.2) * np.minimum(1, (dur - t) / 0.03)
    return (x * g).astype(np.float32)


def pad(notas, dur, g=1.0, brillo=1700):
    t = _tt(dur)
    x = np.zeros_like(t)
    for n in notas:
        for det in (-0.06, 0.0, 0.06):
            f = midi(n) * 2 ** (det / 12)
            x += 2 * ((f * t) % 1) - 1
    x = _lp(x / (3 * len(notas)), brillo)
    a, r = min(0.5, dur / 3), min(0.7, dur / 3)
    return (x * np.minimum(1, t / a) * np.minimum(1, (dur - t) / r) * g).astype(np.float32)


def pluck(nota, dur=0.5, g=1.0):
    t = _tt(dur)
    f = midi(nota)
    x = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2 * f * t) + 0.12 * np.sin(2 * np.pi * 3 * f * t)
    return (x * np.exp(-t * 9) * np.minimum(1, t / 0.004) * g).astype(np.float32)


def stab(notas, dur=0.22, g=1.0, brillo=3800):
    t = _tt(dur)
    x = np.zeros_like(t)
    for n in notas:
        for det in (-0.07, 0.07):
            f = midi(n) * 2 ** (det / 12)
            x += 2 * ((f * t) % 1) - 1
    x = _lp(x / (2 * len(notas)), brillo)
    return (x * np.exp(-t * 9) * np.minimum(1, t / 0.005) * g).astype(np.float32)


def riser(dur, g=1.0):
    t = _tt(dur)
    n = _hp(rng.normal(0, 1, t.size), 1500)
    e = (t / dur) ** 2.2
    s = np.sin(2 * np.pi * np.cumsum(200 + 1800 * (t / dur) ** 2) / SR)
    return ((n * 0.6 + s * 0.35) * e * g * np.minimum(1, (dur - t) / 0.02)).astype(np.float32)


# ------------------------------------------------------------------ efectos de sonido
def sfx(tipo):
    if tipo == "whoosh":
        t = _tt(0.55)
        n = _bp(rng.normal(0, 1, t.size), 700, 7000)
        e = np.sin(np.pi * np.clip(t / 0.55, 0, 1)) ** 1.6
        s = np.sin(2 * np.pi * np.cumsum(250 + 1700 * (t / 0.55) ** 1.4) / SR) * 0.18
        return ((n * 0.9 + s) * e * 0.8).astype(np.float32)
    if tipo == "whoosh_corto":
        t = _tt(0.3)
        n = _bp(rng.normal(0, 1, t.size), 1200, 9000)
        return (n * np.sin(np.pi * np.clip(t / 0.3, 0, 1)) ** 1.4 * 0.7).astype(np.float32)
    if tipo == "impacto":
        t = _tt(1.1)
        sub = np.sin(2 * np.pi * np.cumsum(32 + 90 * np.exp(-t * 14)) / SR) * np.exp(-t * 3.2)
        n = _lp(rng.normal(0, 1, t.size), 1800) * np.exp(-t * 7) * 0.5
        return ((sub * 1.1 + n) * 0.95).astype(np.float32)
    if tipo == "golpe":
        t = _tt(0.45)
        sub = np.sin(2 * np.pi * np.cumsum(55 + 100 * np.exp(-t * 25)) / SR) * np.exp(-t * 8)
        n = _hp(rng.normal(0, 1, t.size), 1500) * np.exp(-t * 40) * 0.5
        return ((sub + n) * 0.9).astype(np.float32)
    if tipo == "pop":
        t = _tt(0.12)
        return (np.sin(2 * np.pi * np.cumsum(1500 - 900 * t / 0.12) / SR) * np.exp(-t * 38) * 0.55).astype(np.float32)
    if tipo == "tick":
        t = _tt(0.06)
        return (_hp(rng.normal(0, 1, t.size), 3500) * np.exp(-t * 90) * 0.5).astype(np.float32)
    if tipo == "brillo":                      # logo
        t = _tt(1.6)
        x = np.zeros_like(t)
        for f, d, a in ((1318, 0.0, 1), (1760, 0.07, 0.8), (2093, 0.14, 0.7), (2637, 0.22, 0.6), (3136, 0.3, 0.45)):
            x += a * np.sin(2 * np.pi * f * t) * np.exp(-np.clip(t - d, 0, None) * 3.2) * (t >= d) * np.minimum(1, np.clip(t - d, 0, None) / 0.005)
        return (x * 0.22).astype(np.float32)
    if tipo == "subida":
        return riser(0.9, 0.7)
    if tipo == "campana":                      # llamada a la acción
        t = _tt(1.0)
        x = (np.sin(2 * np.pi * 1568 * t) + 0.5 * np.sin(2 * np.pi * 2349 * t)) * np.exp(-t * 5)
        return (x * 0.25).astype(np.float32)
    raise ValueError(tipo)


# ------------------------------------------------------------------ música
class Pista:
    def __init__(self, dur):
        self.n = int((dur + 2.5) * SR)
        self.m = np.zeros((self.n, 2), np.float32)

    def poner(self, x, t0, g=1.0, pan=0.0):
        i = int(t0 * SR)
        if i < 0 or i >= self.n:
            return
        x = x[: self.n - i]
        self.m[i:i + x.size, 0] += x * g * (1 - max(pan, 0))
        self.m[i:i + x.size, 1] += x * g * (1 + min(pan, 0))


ACORDES = {"M": (0, 4, 7, 11), "m": (0, 3, 7, 10), "7": (0, 4, 7, 10)}


def _acorde(raiz, tipo, octava=0):
    return [raiz + i + 12 * octava for i in ACORDES[tipo]]


def musica(estilo, bpm, compases, dur):
    """Pista estéreo original. estilo: 'inspirador' | 'energico' | 'publicitario'."""
    p = Pista(dur)
    b = 60.0 / bpm
    if estilo == "inspirador":          # moderna, luminosa, arpegio + pad (Do mayor)
        prog = [(48, "M"), (55, "M"), (45, "m"), (53, "M")]
    elif estilo == "energico":          # ritmo marcado, bajo y stabs (La menor)
        prog = [(45, "m"), (41, "M"), (48, "M"), (43, "M")]
    else:                               # publicitaria dinámica, urgencia moderada (Re menor)
        prog = [(50, "m"), (46, "M"), (53, "M"), (48, "M")]
    for c in range(compases):
        t0 = c * 4 * b
        raiz, tipo = prog[c % 4]
        ac = _acorde(raiz + 12, tipo)
        ultimo = c >= compases - 2
        if estilo == "inspirador":
            p.poner(pad(ac + [raiz + 24], 4 * b + 0.3, 0.30), t0, 1, 0.0)
            if c >= 1:
                for k in range(8):               # arpegio de corcheas
                    p.poner(pluck(ac[[0, 1, 2, 3, 2, 1, 3, 1][k] % 4] + 12, 0.5, 0.20), t0 + k * b / 2, 1, (-1) ** k * 0.35)
            if c == 0 or c == compases - 2:
                p.poner(kick(1.0), t0, 0.9)
            if 1 <= c < compases - 2:
                for k in (0, 2):
                    p.poner(kick(0.8), t0 + k * b, 0.55)
                if c >= 2:
                    for k in range(8):
                        p.poner(hat(0.5), t0 + k * b / 2 + b / 4 * 0, 0.18)
                    p.poner(snare(0.6), t0 + b, 0.22)
                    p.poner(snare(0.6), t0 + 3 * b, 0.22)
                if c >= 3:
                    p.poner(bajo(raiz - 12 + 12, 2 * b, 0.9), t0, 0.5)
                    p.poner(bajo(raiz, 2 * b, 0.9), t0 + 2 * b, 0.5)
        elif estilo == "energico":
            p.poner(pad(ac, 4 * b + 0.2, 0.22, 1400), t0, 1)
            for k in range(4):
                p.poner(kick(1.0), t0 + k * b, 0.95)
                p.poner(hat(0.9, True), t0 + k * b + b / 2, 0.30)
            for k in (1, 3):
                p.poner(clap(1.0), t0 + k * b, 0.55)
            for k in range(8):
                p.poner(hat(0.5), t0 + k * b / 2 + b / 4, 0.14)
            for k in range(8):                    # bajo en corcheas con octava
                p.poner(bajo(raiz - 12 + (12 if k % 4 == 3 else 0), b * 0.46, 1.0), t0 + k * b / 2, 0.55)
            if c >= 1:
                for k in (0.5, 1.5, 2.5, 3.5):    # stabs a contratiempo
                    p.poner(stab(ac[:3], 0.2, 0.9), t0 + k * b, 0.20, 0.3)
            if c >= 2:
                for k in range(8):
                    p.poner(pluck(ac[[0, 2, 1, 3, 0, 2, 3, 1][k]] + 12, 0.3, 0.14), t0 + k * b / 2, 1, (-1) ** k * 0.4)
            if c % 4 == 3:
                p.poner(riser(4 * b, 0.5), t0, 0.35)
        else:                                      # publicitario
            p.poner(pad(ac, 4 * b + 0.2, 0.20, 1300), t0, 1)
            for k in (0, 1.5, 2, 3.5 if c % 2 else 3):
                p.poner(kick(1.0), t0 + k * b, 0.85)
            for k in (1, 3):
                p.poner(snare(1.0), t0 + k * b, 0.40)
            for k in range(8):
                p.poner(hat(0.8), t0 + k * b / 2, 0.14)
            for k in range(8):
                nota = raiz - 12 + [0, 0, 12, 0, 7, 0, 12, 7][k]
                p.poner(bajo(nota, b * 0.45, 1.0), t0 + k * b / 2, 0.50)
            for k in (0, 1.5, 2.5):
                p.poner(stab(ac, 0.28, 1.0, 3200), t0 + k * b, 0.22, -0.25)
            for k in range(4):
                p.poner(pluck(ac[k % 4] + 24, 0.25, 0.14), t0 + (k + 0.5) * b, 1, 0.4)
            if c == compases - 3:                  # redoble antes del cierre
                for k in range(8):
                    p.poner(snare(0.5 + k * 0.1), t0 + 2 * b + k * b / 4, 0.28)
                p.poner(riser(2 * b, 0.6), t0 + 2 * b, 0.35)
    # cola de reverberación simple y límite suave
    m = p.m
    for d, g in ((0.11, 0.22), (0.19, 0.15), (0.31, 0.10)):
        k = int(d * SR)
        m[k:] += m[:-k] * g
    return m


# ------------------------------------------------------------------ mezcla
def mezclar(total, voces, mus, eventos, ruta, gm=-19.0):
    """voces: [(t0, audio)] · mus: pista estéreo · eventos: [(t, tipo, ganancia)] → wav estéreo normalizado."""
    n = int(total * SR)
    v = np.zeros(n, np.float32)
    for t0, x in voces:
        x = x * (10 ** (-17.5 / 20) / (np.sqrt((x ** 2).mean()) + 1e-9))
        x = np.tanh(x * 1.5) / 1.5
        i = int(t0 * SR)
        v[i:i + x.size] += x[: max(0, n - i)]
    v = _hp(v, 70)
    musica_ = mus[:n].copy()
    musica_ *= 10 ** (gm / 20) / (np.sqrt((musica_ ** 2).mean()) + 1e-9)
    # la música baja ~9 dB mientras habla la voz (ataque rápido, vuelta suave)
    activo = (np.convolve(np.abs(v), np.ones(int(0.04 * SR)) / int(0.04 * SR), "same") > 0.012).astype(np.float32)
    k = int(SR * 0.4)
    suave = np.convolve(np.pad(activo, (k, k), mode="edge"), np.ones(k) / k, mode="same")[k:-k]
    suave = np.maximum(suave, np.convolve(np.pad(activo, (k, 0)), np.ones(int(SR * 0.06)) / int(SR * 0.06), mode="same")[k:])
    gan = 1 - 0.65 * np.clip(suave, 0, 1)
    fx = np.zeros(n, np.float32)
    for t, tipo, g in eventos:
        s = sfx(tipo) * g
        i = int(t * SR)
        if 0 <= i < n:
            fx[i:i + s.size] += s[: n - i]
    mezcla = musica_ * gan[:, None] + fx[:, None] * (0.55 + 0.45 * gan[:, None]) * 0.8 + v[:, None]
    fi, fo = int(0.15 * SR), int(1.6 * SR)
    mezcla[:fi] *= np.linspace(0, 1, fi)[:, None]
    mezcla[-fo:] *= np.linspace(1, 0, fo)[:, None]
    mezcla = np.tanh(mezcla * 1.1)
    mezcla *= 0.92 / np.abs(mezcla).max()
    crudo = str(ruta) + ".crudo.wav"
    wavfile.write(crudo, SR, (mezcla * 32767).astype(np.int16))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", crudo, "-af", "loudnorm=I=-14:TP=-1.5:LRA=9", "-ar", str(SR), str(ruta)], check=True)
    os.remove(crudo)
    return ruta
