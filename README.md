# Videos para la forrajería

Genera videos publicitarios verticales (1080x1920, ideales para Instagram, TikTok, WhatsApp y Facebook) con Python.

## Cómo se usa

1. Poné tus fotos (`.jpg`, `.png`) o videos cortos (`.mp4`) en la carpeta `fotos/`. Se usan en orden alfabético (nombralas `01_...`, `02_...`).
2. Editá los textos (nombre, slogan, teléfono, dirección) en `CONFIG` dentro de `crear_video.py`, o creá un `.json` con las mismas claves.
3. Ejecutá:

```bash
source .venv/bin/activate      # primera vez: python3 -m venv .venv && pip install -r requirements.txt
python crear_video.py
```

El video queda en `videos_salida/publicidad.mp4`.

Para sumar música poné un `.mp3` en la carpeta y completá `"musica": "musica.mp3"`.

Requiere `ffmpeg` instalado en el sistema.
