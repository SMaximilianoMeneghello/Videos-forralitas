"""Genera un video publicitario vertical (1080x1920) para la forrajería.

Uso:
    python crear_video.py                 # usa las fotos de ./fotos
    python crear_video.py mi_config.json  # usa otra configuración

Poné tus fotos (jpg/png) o videos cortos (mp4) en la carpeta ./fotos.
Editá los textos en CONFIG (abajo) o en un JSON con las mismas claves.
"""
import json
import sys
from pathlib import Path

from moviepy import (ColorClip, CompositeVideoClip, ImageClip, TextClip,
                     VideoFileClip, concatenate_videoclips)

ANCHO, ALTO = 1080, 1920
FUENTE = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

CONFIG = {
    "nombre": "FORRAJERÍA",           # nombre del local
    "slogan": "Todo para tus animales",
    "frases": ["Alimento balanceado", "Fardos y semillas", "Mascotas y campo"],
    "contacto": "📞 Tel: 000-0000000  ·  Av. Ejemplo 123",
    "segundos_por_foto": 3,
    "musica": None,                   # ej: "musica.mp3"
    "salida": "videos_salida/publicidad.mp4",
}


def ajustar(clip):
    """Escala y recorta el medio para llenar la pantalla vertical."""
    escala = max(ANCHO / clip.w, ALTO / clip.h)
    return clip.resized(escala).cropped(
        x_center=clip.w * escala / 2, y_center=clip.h * escala / 2,
        width=ANCHO, height=ALTO)


def texto(msg, tam, color="white", y="center", dur=3):
    t = TextClip(font=FUENTE, text=msg, font_size=tam, color=color,
                 stroke_color="black", stroke_width=4, method="caption",
                 size=(ANCHO - 120, None), text_align="center")
    return t.with_position(("center", y)).with_duration(dur)


def escena(ruta, frase, dur):
    if ruta.suffix.lower() in {".mp4", ".mov", ".avi", ".mkv"}:
        base = ajustar(VideoFileClip(str(ruta)).without_audio().subclipped(0, dur))
    else:
        base = ajustar(ImageClip(str(ruta)).with_duration(dur))
    return CompositeVideoClip(
        [base, texto(frase, 90, "yellow", ALTO - 450, dur)], size=(ANCHO, ALTO))


def main():
    cfg = dict(CONFIG)
    if len(sys.argv) > 1:
        cfg.update(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))

    medios = sorted(p for p in Path("fotos").glob("*")
                    if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".mp4", ".mov"})
    dur = cfg["segundos_por_foto"]

    verde = (30, 110, 50)
    portada = CompositeVideoClip([
        ColorClip((ANCHO, ALTO), color=verde, duration=3),
        texto(cfg["nombre"], 140, "white", 700, 3),
        texto(cfg["slogan"], 70, "yellow", 1000, 3),
    ], size=(ANCHO, ALTO))

    cierre = CompositeVideoClip([
        ColorClip((ANCHO, ALTO), color=verde, duration=4),
        texto("¡Te esperamos!", 120, "yellow", 650, 4),
        texto(cfg["nombre"], 100, "white", 900, 4),
        texto(cfg["contacto"], 55, "white", 1150, 4),
    ], size=(ANCHO, ALTO))

    frases = cfg["frases"]
    escenas = [escena(m, frases[i % len(frases)], dur) for i, m in enumerate(medios)]
    video = concatenate_videoclips([portada, *escenas, cierre], method="compose")

    if cfg["musica"] and Path(cfg["musica"]).exists():
        from moviepy import AudioFileClip
        audio = AudioFileClip(cfg["musica"]).subclipped(0, video.duration)
        video = video.with_audio(audio.with_volume_scaled(0.6))

    Path(cfg["salida"]).parent.mkdir(exist_ok=True)
    video.write_videofile(cfg["salida"], fps=30, codec="libx264",
                          audio_codec="aac", logger=None)
    print("Listo:", cfg["salida"])


if __name__ == "__main__":
    main()
