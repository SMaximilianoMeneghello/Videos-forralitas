"""Genera motion/datos.js con la línea de tiempo, las palabras de la locución (tiempos absolutos) y los bloques de subtítulos."""
import json
from pathlib import Path
B = Path(__file__).resolve().parent.parent
tl = json.loads((B / "guion/timeline.json").read_text())
marcas = json.loads((B / "audio/voz/marcas.json").read_text())
voz, subs = {}, []
for k, t0 in sorted(tl["voz"].items(), key=lambda x: x[1]):
    m = marcas[k]
    pal = [{"w": p["w"], "t": round(t0 + p["t"], 3), "d": round(p["d"], 3)} for p in m["palabras"]]
    voz[k] = {"t": t0, "dur": round(m["dur"], 3), "texto": m["texto"], "palabras": pal}
    # bloques de subtítulo: hasta ~24 caracteres, cortando en signos de puntuación del texto original
    texto = m["texto"]
    bloque, largo = [], 0
    pos = 0
    for i, p in enumerate(pal):
        idx = texto.find(p["w"], pos); fin_idx = idx + len(p["w"]) if idx >= 0 else pos
        sig = texto[fin_idx:fin_idx + 1] if idx >= 0 else ""
        pos = fin_idx if idx >= 0 else pos
        bloque.append(p); largo += len(p["w"]) + 1
        # no dejar una sola palabra colgando al final de la frase
        sig_sig = ""
        if i + 1 < len(pal):
            j = texto.find(pal[i + 1]["w"], pos)
            sig_sig = texto[j + len(pal[i + 1]["w"]):j + len(pal[i + 1]["w"]) + 1] if j >= 0 else ""
        ultima_de_frase = i + 1 == len(pal) - 1 or sig_sig in (",", ".", "?", "!", "…")
        corta = sig in ",.?!…" or (largo > 22 and not ultima_de_frase) or largo > 30 or i == len(pal) - 1
        if corta:
            subs.append({"palabras": bloque, "t": bloque[0]["t"]})
            bloque, largo = [], 0
for i, s in enumerate(subs):
    ult = s["palabras"][-1]
    s["fin"] = round(ult["t"] + ult["d"] + .35, 3)
    if i + 1 < len(subs):
        s["fin"] = round(min(s["fin"] + .4, subs[i + 1]["t"]), 3)
(B / "motion/datos.js").write_text("window.TL=" + json.dumps(tl, ensure_ascii=False) + ";\nwindow.VOZ=" + json.dumps(voz, ensure_ascii=False) + ";\nwindow.SUBS=" + json.dumps(subs, ensure_ascii=False) + ";\n")
print(len(subs), "bloques de subtítulos")
for s in subs[:8]: print(s["t"], " ".join(p["w"] for p in s["palabras"]))
