# FORRALITAS — producción audiovisual (3 videos)

| Archivo | Duración | Concepto |
|---|---|---|
| `videos/FORRALITAS_PRESENTACION.mp4` | 44,9 s | "Todo lo que tus animales necesitan, en un solo lugar" |
| `videos/FORRALITAS_PRODUCTOS.mp4` | 41,7 s | "La calidad comienza con una buena alimentación" |
| `videos/FORRALITAS_PUBLICIDAD.mp4` | 41,0 s | "¿Necesitás abastecerte? En FORRALITAS te esperamos" |

Los tres: MP4 H.264 (High) + AAC 44,1 kHz estéreo, 1080 × 1920 (9:16), 30 fps. Miniaturas verticales en `miniaturas/`.
Guiones, textos en pantalla y descripciones con hashtags en `textos/`.

## Qué se hizo
* Motor propio (Python + OpenCV + Pillow + numpy) en `codigo/`: cámara virtual con zoom y paneo, parallax, speed ramp, tipografía cinética,
  subtítulos por palabra, whip pan con motion blur, transiciones por máscara, barridos de luz, partículas y corrección de color.
* Fotos reales de productos como protagonistas (`fotos_preparadas/`, versión ≤ 2400 px con contraste suave, sin cambiar colores).
  El logo es el original (`logo/logo_original.jpg`), sin deformar.
* Música y efectos **originales sintetizados** (sin canciones ni samples de terceros → sin problemas de derechos). Tres identidades:
  inspiradora (96 BPM), enérgica (126 BPM) y publicitaria (110 BPM). Los cortes caen en la grilla del compás.
* Datos comerciales solo los verificados del proyecto (CONFIG de `crear_video.py`). **Sin precios, descuentos ni promociones.**
  Todos los videos cierran con teléfonos, horarios (lunes a sábado; no se atiende domingo), ubicación, envíos, venta por mayor y menor y medios de pago.

## Para regenerar (desde la raíz del repositorio)
```
python FORRALITAS/codigo/preparar_fotos.py
python FORRALITAS/codigo/video1_presentacion.py     # --frames t1 t2 … para vistas previas
python FORRALITAS/codigo/video2_productos.py
python FORRALITAS/codigo/video3_publicidad.py
```

## Limitaciones (importante)
* **Locución:** la voz neuronal argentina (Edge, es-AR-TomasNeural) está bloqueada en este entorno (403 de `speech.platform.bing.com`).
  Se usó una voz masculina de Piper (es_MX-claude-high), de acento neutro latinoamericano y algo menos natural. Los guiones están en
  `textos/GUIONES_LOCUCION.md`; al habilitar ese dominio, regenerar los videos usa automáticamente la voz de Tomás.
* **Subtítulos:** la sincronización por palabra es proporcional (el motor de voz alternativo no entrega marcas de tiempo por palabra).
* **Fotos faltantes:** no hay fotos de avena, expeller de soja, polenta, legumbres ni harinas; esos productos se nombran (tarjeta tipográfica / texto) pero no se muestran imágenes inventadas.
  La alfalfa verde se muestra con las fotos originales; no hay fotos de alfalfa estacionada.
* **Alight Motion:** no existe exportación programática desde este entorno, así que no se entrega ningún proyecto `.alightmotion`. El proyecto editable
  son los scripts de `codigo/`.
