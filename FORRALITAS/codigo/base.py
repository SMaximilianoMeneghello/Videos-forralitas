"""Planificación sobre la grilla del compás, mezcla de audio y render en paralelo (FFmpeg H.264 + AAC)."""
import math
import multiprocessing as mp
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import motor as m  # noqa: E402
import sonido as so  # noqa: E402

RAIZ = m.RAIZ
SALIDA = RAIZ / "FORRALITAS"
TR = 0.42


class Info:
    def __init__(self, dur, beat, voces, ini):
        self.dur, self.beat, self.voces, self.ini = dur, beat, voces, ini   # voces: [(t_local, dur, texto)]
        self.sfx = []                                                         # (t_local, tipo, ganancia)

    def b(self, k):
        return k * self.beat


def planificar(bpm, escenas, ritmo=0.9, cola=1.2):
    """escenas: [dict(nombre, min_beats, hold, voz=[(texto, pausa_antes)], fabrica(info)->fn(t), sfx_corte=...)]"""
    beat = 60.0 / bpm
    t = 0.0
    plan = []
    for e in escenas:
        voces, cur = [], 0.25
        for texto, pausa in e.get("voz", []):
            x, tiempos = so.voz(texto, ritmo)
            cur += pausa
            voces.append((cur, len(x) / so.SR, texto, x, tiempos))
            cur += len(x) / so.SR
        beats = max(e["min_beats"], math.ceil((cur + e.get("hold", 0.6)) / beat)) if voces else e["min_beats"]
        dur = beats * beat
        info = Info(dur, beat, [(a, d, tx) for a, d, tx, _, _ in voces], t)
        plan.append(dict(e, info=info, ini=t, dur=dur, voces=voces, fn=None))
        t += dur
    plan[-1]["dur"] += cola
    plan[-1]["info"].dur += cola
    return plan, beat, t + cola


def construir_linea(plan, transiciones):
    for e in plan:
        e["fn"] = e["fabrica"](e["info"])
    return m.Linea([(e["dur"], e["fn"]) for e in plan], transiciones, TR)


def palabras_globales(plan):
    out = []
    for e in plan:
        for a, d, tx, x, tiempos in e["voces"]:
            for i, (p, o) in enumerate(tiempos):
                ini = e["ini"] + a + o
                fin = e["ini"] + a + (tiempos[i + 1][1] if i + 1 < len(tiempos) else d)
                out.append((p, ini, fin))
    return out


def audio(plan, total, estilo, bpm, nombre, extra_sfx=()):
    beat = 60.0 / bpm
    compases = int(math.ceil(total / (4 * beat))) + 1
    mus = so.musica(estilo, bpm, compases, total)
    voces, ev = [], []
    for e in plan:
        for a, d, tx, x, tiempos in e["voces"]:
            voces.append((e["ini"] + a, x))
        for t, tipo, g in e["info"].sfx:
            ev.append((e["ini"] + t, tipo, g))
    for i, e in enumerate(plan):
        if i:
            ev.append((e["ini"] - 0.32, "whoosh", 0.9))
            ev.append((e["ini"] - 0.02, e.get("impacto", "golpe"), 0.8))
    ev += list(extra_sfx)
    ruta = SALIDA / f"audios/{nombre}_mezcla.wav"
    so.mezclar(total, voces, mus, ev, ruta)
    from scipy.io import wavfile
    wavfile.write(SALIDA / f"musica/{nombre}_musica.wav", so.SR, (np.clip(mus[: int(total * so.SR)], -1, 1) * 0.4 * 32767).astype(np.int16))
    return ruta


# ------------------------------------------------------------------ render en paralelo
_G = {}


def _trabajo(i):
    tl, subs, grado, fx = _G["tl"], _G["subs"], _G["grado"], _G["fx"]
    t = i / m.FPS
    f = tl.frame(t)
    if subs is not None and not any(a <= t < b for a, b in _G["sin_subs"]):
        subs.draw(f, t)
    if fx:
        fx(f, t)
    return m.grade(f, grado).tobytes()


def renderizar(tl, subs, sin_subs, total, wav, salida, grado="cine", fx=None, hilos=4, frames=None):
    _G.update(tl=tl, subs=subs, sin_subs=sin_subs, grado=grado, fx=fx)
    n = int(round(total * m.FPS))
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{m.W}x{m.H}", "-r", str(m.FPS), "-i", "-",
           "-i", str(wav), "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-profile:v", "high", "-level", "4.2",
           "-pix_fmt", "yuv420p", "-r", str(m.FPS), "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-shortest", "-movflags", "+faststart", str(salida)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    ctx = mp.get_context("fork")
    with ctx.Pool(hilos) as pool:
        for k, buf in enumerate(pool.imap(_trabajo, range(n), chunksize=4)):
            p.stdin.write(buf)
            if k % 150 == 0:
                print(f"  {k}/{n}", flush=True)
    p.stdin.close()
    p.wait()
    return n


def vista_previa(tl, subs, sin_subs, tiempos, ruta_base, grado="cine", fx=None):
    from PIL import Image
    _G.update(tl=tl, subs=subs, sin_subs=sin_subs, grado=grado, fx=fx)
    for t in tiempos:
        b = _trabajo(int(round(t * m.FPS)))
        Image.frombytes("RGB", (m.W, m.H), b).save(f"{ruta_base}_{t:05.1f}.png")
