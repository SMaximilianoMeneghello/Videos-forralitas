"""Genera la locución por frase con la voz neuronal es-AR-TomasNeural (Edge TTS), con marcas por palabra.

Uso: python3 audio/voz.py [rate]   ->  audio/voz/<id>.wav + audio/voz/marcas.json
"""
import asyncio, json, os, ssl, subprocess, sys
from pathlib import Path
import aiohttp, edge_tts

BASE = Path(__file__).resolve().parent
VOZ = "es-AR-TomasNeural"
CA = "/root/.ccr/ca-bundle.crt"
# Ajustes por frase: velocidad y tono. Las preguntas y el cierre van un poco más pausados.
AJUSTES = {"v01": ("-4%", "-2Hz"), "v03": ("+0%", "+0Hz"), "v12": ("+0%", "+0Hz"), "v16": ("-3%", "-2Hz"),
           "v17": ("-2%", "+0Hz"), "v18": ("-3%", "-1Hz")}


async def sintetizar(texto, ruta, rate, pitch):
    ctx = ssl.create_default_context(cafile=CA if os.path.exists(CA) else None)
    com = edge_tts.Communicate(texto, VOZ, rate=rate, pitch=pitch, boundary="WordBoundary",
                               connector=aiohttp.TCPConnector(ssl=ctx), proxy=os.environ.get("HTTPS_PROXY"))
    marcas = []
    with open(ruta, "wb") as f:
        async for ch in com.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                marcas.append({"w": ch["text"], "t": ch["offset"] / 1e7, "d": ch["duration"] / 1e7})
    return marcas


def main():
    base_rate = sys.argv[1] if len(sys.argv) > 1 else "+2%"
    lineas = json.loads((BASE.parent / "guion/locucion.json").read_text())
    salida = {}
    for l in lineas:
        rate, pitch = AJUSTES.get(l["id"], (base_rate, "+0Hz"))
        mp3 = BASE / "voz" / f"{l['id']}.mp3"
        wav = BASE / "voz" / f"{l['id']}.wav"
        marcas = asyncio.run(sintetizar(l["texto"], mp3, rate, pitch))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(mp3), "-ac", "1", "-ar", "48000", str(wav)], check=True)
        dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(wav)]))
        salida[l["id"]] = {"texto": l["texto"], "dur": dur, "palabras": marcas, "rate": rate, "pitch": pitch}
        print(l["id"], round(dur, 2), len(marcas))
    (BASE / "voz" / "marcas.json").write_text(json.dumps(salida, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
