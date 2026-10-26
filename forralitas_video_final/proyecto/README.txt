PROYECTO DEL VIDEO — Forrajería Forralitas

Requisitos: Python 3 con numpy, opencv-python-headless, pillow, scipy, torch (CPU) y edge-tts; ffmpeg.
(En este repositorio: el entorno .venv de la raíz ya los tiene.)

1) Preparar material (una sola vez, ~1 h en CPU: upscaling con IA y cámara lenta):
       python preparar.py
2) Renderizar todo (principal 9:16, estado 15 s, cuadrado 1:1, subtítulos .srt, guion y portada):
       python forralitas_promo.py
   Solo un corte:      python forralitas_promo.py --corte principal      (o estado / cuadrado)
   Vista previa rápida de cuadros sueltos:
       python forralitas_promo.py --corte principal --cuadros 2 10 28

CAMBIAR TEXTOS, TELÉFONOS O LOCUCIÓN
Todo está al principio de forralitas_promo.py:
- DATOS: títulos, nombre, ruta, localidad, teléfonos (lista; [] para ocultarlos), llamada a la acción.
- VOZ: lo que dice la locución (texto exacto). Se vuelve a generar sola.
- SUBS: cómo se escribe en pantalla cada palabra de la voz (misma cantidad de palabras; "|" separa
  bloques de subtítulo; "_" = palabra que se dice pero no se muestra; *palabra* = resaltada).
- Montaje: funciones corte_principal() / corte_estado(): tomas, duración en tiempos de música (beats),
  transición de entrada ("corte", "zoom", "whip", "flash", "desliza") y movimiento de cámara.

USAR TU PROPIA VOZ
Grabá cada frase de guion_locucion.txt en un .wav y reemplazá en voz/ el archivo cache_*.wav
correspondiente (o pedime que lo integre).

CARPETAS
material/   copias de los archivos originales (los originales no se tocan)
cache/      material procesado (IA, cámara lenta, audio)
musica/     pista de Kevin MacLeod (CC BY 4.0)
fuentes/    tipografías OFL
modelos/    pesos de Real-ESRGAN
