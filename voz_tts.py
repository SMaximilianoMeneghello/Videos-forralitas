"""Genera la locución con una voz neuronal (Edge TTS) respetando el proxy y los certificados del entorno."""
import asyncio
import os
import ssl

import aiohttp
import edge_tts

CA = os.environ.get("CCR_CA", "/root/.ccr/ca-bundle.crt")


async def _sintetizar(texto, voz, ruta, rate="-4%", pitch="+0Hz", boundary="SentenceBoundary"):
    ctx = ssl.create_default_context(cafile=CA if os.path.exists(CA) else None)
    conector = aiohttp.TCPConnector(ssl=ctx)
    com = edge_tts.Communicate(texto, voz, rate=rate, pitch=pitch, boundary=boundary, connector=conector,
                               proxy=os.environ.get("HTTPS_PROXY"))
    marcas = []
    with open(ruta, "wb") as f:
        async for ch in com.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] in ("WordBoundary", "SentenceBoundary"):
                marcas.append(ch)
    return marcas


def sintetizar(texto, voz, ruta, **kw):
    return asyncio.run(_sintetizar(texto, voz, ruta, **kw))


if __name__ == "__main__":
    for v in ("es-AR-ElenaNeural", "es-AR-TomasNeural"):
        sintetizar("¿Sos de Las Talitas y no sabés dónde comprar alimentos para tus animales? Te presento Forralitas.",
                   v, f"voz/prueba_{v}.mp3")
        print("ok", v)


# ------------------------------------------------------------ clips listos para mezclar
import hashlib
import subprocess

import numpy as np
from scipy.io import wavfile

SR = 44100
VOZ = "es-AR-TomasNeural"       # alternativa: "es-AR-ElenaNeural" (voz de mujer)
RATE = "+5%"


def clip(texto, voz=None, rate=None):
    """Devuelve la locución de `texto` como array float mono (SR Hz), sin silencios en los bordes."""
    voz, rate = voz or VOZ, rate or RATE
    h = hashlib.md5(f"{voz}|{rate}|{texto}".encode()).hexdigest()[:12]
    mp3, wav = f"voz/cache_{h}.mp3", f"voz/cache_{h}.wav"
    if not os.path.exists(wav):
        sintetizar(texto, voz, mp3, rate=rate)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp3, "-ac", "1", "-ar", str(SR), wav], check=True)
    sr, x = wavfile.read(wav)
    x = x.astype(np.float32) / 32768
    idx = np.where(np.abs(x) > 0.012)[0]
    return x[max(idx[0] - int(0.02 * SR), 0): idx[-1] + int(0.04 * SR)]


def clip_palabras(texto, voz=None, rate=None):
    """Como clip(), pero devuelve también el instante (s) en que empieza cada palabra del texto."""
    import json
    voz, rate = voz or VOZ, rate or RATE
    h = hashlib.md5(f"{voz}|{rate}|{texto}|wb".encode()).hexdigest()[:12]
    mp3, wav, js = f"voz/cache_{h}.mp3", f"voz/cache_{h}.wav", f"voz/cache_{h}.json"
    if not (os.path.exists(wav) and os.path.exists(js)):
        marcas = sintetizar(texto, voz, mp3, rate=rate, boundary="WordBoundary")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp3, "-ac", "1", "-ar", str(SR), wav], check=True)
        json.dump([(m["text"], m["offset"] / 1e7, m["duration"] / 1e7) for m in marcas], open(js, "w"))
    sr, x = wavfile.read(wav)
    x = x.astype(np.float32) / 32768
    idx = np.where(np.abs(x) > 0.012)[0]
    a, b = max(idx[0] - int(0.02 * SR), 0), idx[-1] + int(0.04 * SR)
    marcas = json.load(open(js))
    pal = texto.split()
    dur = (b - a) / SR
    if len(marcas) == len(pal):
        tiempos = [max(m[1] - a / SR, 0.0) for m in marcas]
    else:                                   # respaldo: reparto proporcional por letras
        tot = sum(len(p) for p in pal)
        acum, tiempos = 0, []
        for p in pal:
            tiempos.append(dur * acum / tot)
            acum += len(p)
    return x[a:b], tiempos
