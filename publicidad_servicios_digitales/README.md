# Publicidad · Servicios digitales

Producción completa de una publicidad vertical (9:16) para promocionar cuatro servicios: edición de videos, invitaciones y tarjetas digitales, invitaciones web interactivas y páginas web. Duración: 2:12. Contacto: **WhatsApp +54 9 381 585 9396 · wa.me/5493815859396**.

## Entregables (`salida/`)
| Archivo | Descripción |
|---|---|
| `PUBLICIDAD_SERVICIOS_DIGITALES_VERTICAL.mp4` | 1080×1920, 30 fps, H.264 + AAC, −14 LUFS (Reels, TikTok, Facebook, WhatsApp) |
| `PUBLICIDAD_SERVICIOS_DIGITALES_HORIZONTAL.mp4` | 1920×1080: la pieza vertical centrada, con fondo desenfocado y laterales de servicios y contacto |
| `DEMO_EDICION_PROFESIONAL_10S.mp4` | Demo de edición de 10 s con tomas reales de drone |
| `LOCUCION_VOZ_MASCULINA.wav/.mp3` | Locución sola, procesada y ubicada en el tiempo |
| `BANDA_SONORA_MUSICA_Y_EFECTOS.mp3` | Música y efectos originales, sin voz |
| `SUBTITULOS.srt`, `SUBTITULOS_PALABRA_POR_PALABRA.srt`, `SUBTITULOS_KARAOKE.vtt` | Subtítulos sincronizados (en el video ya están incrustados palabra por palabra) |
| `MINIATURA_VERTICAL.jpg`, `MINIATURA_HORIZONTAL.jpg` | Portadas |
| `GUION_FINAL_LOCUCION.md` | Guion con tiempos y descripción de imagen |
| `TEXTO_PARA_REDES.md` | Textos para publicar |

Licencias y créditos: `LICENCIAS_Y_RECURSOS.md`.

## Demostraciones funcionales (`web/`)
Abrir el `index.html` de cada carpeta en un navegador (funcionan sin conexión):
- `invitacion_15_valentina/`: invitación web interactiva con apertura animada, cuenta regresiva real, enlace a Google Maps, galería con visor, música con controles y confirmación por WhatsApp con formulario.
- `invitacion_18_mateo/`: invitación digital animada (negro y dorado).
- `otras_celebraciones/`: cumpleaños infantil, primera comunión, aniversario y baby shower.
- `tienda_orbe/`: tienda con catálogo, filtros, carrito y consultas.
- `servicios_habitar/`: landing de servicios con galería y formulario validado.
- `gastronomia_brasa/`: hamburguesería con menú por pestañas, promociones y pedido armado por WhatsApp.

Los datos son ficticios. Los botones de WhatsApp de las demos no llevan número: se configura en la constante `WHATSAPP` / `EVENTO.whatsapp` de cada sitio.

## Cómo se produce (todo reproducible)
1. Locución: `python3 audio/voz.py` (Edge TTS, es-AR-TomasNeural, marcas por palabra). Verificación con Whisper local: `python3 audio/verificar_voz.py`.
2. Capturas reales de las webs con tiempo virtual: `node captura/capturar.js captura/guiones/<guion>.js build/cap/<nombre>`. Playwright controla el reloj y las animaciones CSS avanzan cuadro a cuadro, así que clics, escritura y desplazamiento son eventos reales.
3. Demo de edición: `python3 edicion/demo_edicion.py <carpeta_tomas> build/demo build/demo_raw`. Incluye reencuadre con cámara virtual, *speed ramps* con flujo óptico, *motion blur*, color por plano, *tilt-shift*, transiciones y tipografía.
4. Composición: `python3 motion/generar_datos.py` y después `bash build/render_todo.sh` (Chromium renderiza `motion/publicidad.html` cuadro a cuadro).
5. Sonido: `python3 audio/banda_sonora.py` (música, efectos, *ducking* y mezcla). Masterización a −14 LUFS y codificación con ffmpeg (ver comandos en el historial del proyecto).

Las fuentes de video originales (Wikimedia Commons, CC BY 3.0) y los cuadros intermedios van en `build/` y no se versionan.
