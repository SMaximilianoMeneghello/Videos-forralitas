"""Transcribe cada frase con Whisper (local) y la compara con el guion para detectar errores de pronunciación."""
import json, re, sys, unicodedata
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly
from faster_whisper import WhisperModel

BASE = Path(__file__).resolve().parent
norm = lambda s: re.sub(r"[^a-z0-9ñ ]", "", unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode())
m = WhisperModel(sys.argv[1] if len(sys.argv) > 1 else "small", device="cpu", compute_type="int8")
marks = json.loads((BASE / "voz/marcas.json").read_text())
for k, v in marks.items():
    sr, x = wavfile.read(BASE / f"voz/{k}.wav")
    x = resample_poly(x.astype(np.float32) / 32768, 1, 3)
    segs, _ = m.transcribe(x, language="es", beam_size=5)
    txt = " ".join(s.text.strip() for s in segs)
    a, b = norm(v["texto"]).split(), norm(txt).split()
    dif = [w for w in a if w not in b]
    print(k, "OK " if not dif else "REV", "|", txt, "| faltan:" if dif else "", " ".join(dif))
