"""Exporta los subtítulos sincronizados: por frase (SRT) y palabra por palabra (SRT y VTT)."""
import json, re
from pathlib import Path
B = Path(__file__).resolve().parent.parent
js = (B / "motion/datos.js").read_text()
subs = json.loads(re.search(r"window\.SUBS=(.*);\s*$", js, re.S).group(1))
voz = json.loads(re.search(r"window\.VOZ=(.*?);\nwindow\.SUBS", js, re.S).group(1))
def ts(t, sep=","):
    h, r = divmod(t, 3600); m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d}{sep}{int(round((s - int(s)) * 1000)) % 1000:03d}"
# por frase: usa el texto original con puntuación de cada locución
frases = []
for k, v in voz.items():
    frases.append((v["t"] + v["palabras"][0]["t"] - v["t"], v["t"] + v["dur"], v["texto"]))
srt = "".join(f"{i}\n{ts(a)} --> {ts(b)}\n{txt}\n\n" for i, (a, b, txt) in enumerate(frases, 1))
(B / "salida/SUBTITULOS.srt").write_text(srt, encoding="utf-8")
pal = [p for v in voz.values() for p in v["palabras"]]
srt2 = "".join(f"{i}\n{ts(p['t'])} --> {ts(p['t'] + max(p['d'], .12))}\n{p['w']}\n\n" for i, p in enumerate(pal, 1))
(B / "salida/SUBTITULOS_PALABRA_POR_PALABRA.srt").write_text(srt2, encoding="utf-8")
vtt = "WEBVTT\n\n" + "".join(f"{ts(s['t'], '.')} --> {ts(s['fin'], '.')}\n" + " ".join(f"<{ts(p['t'], '.')}><c>{p['w']}</c>" for p in s["palabras"]) + "\n\n" for s in subs)
(B / "salida/SUBTITULOS_KARAOKE.vtt").write_text(vtt, encoding="utf-8")
print(len(frases), "frases,", len(pal), "palabras")
