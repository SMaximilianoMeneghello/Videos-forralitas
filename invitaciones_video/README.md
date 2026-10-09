# Video de invitaciones web (15 y 18 años)

Video vertical 1080x1920, 24 s, generado con HTML animado + Chromium (Playwright) + ffmpeg.

- `video.html`: todas las escenas y animaciones (función `render(t)`).
- `render.js`: `node render.js frames <desde> <hasta> <carpeta>` exporta frames a 30 fps.
- `musica.py`: sintetiza la música de fondo.
- Armado: `ffmpeg -framerate 30 -i frames/f%04d.jpg -i musica.wav -c:v libx264 -crf 17 -pix_fmt yuv420p -c:a aac salida/invitaciones_web.mp4`

Para cambiar el teléfono, los nombres o las fechas editá `video.html` (`THEMES` y la escena `S5`).
