# 🧠 Your brain is lying to you

Presentación interactiva **en inglés** sobre ilusiones ópticas y trucos de la mente, para una exposición de unos 30 minutos. La controlás desde el celular y al final se juega un juego tipo Kahoot.

📘 **Guía de estudio** (guion en inglés con traducción, pronunciación, datos y preguntas): [`guia.html`](guia.html). Publicada en: https://smaximilianomeneghello.github.io/Videos-forralitas/presentacion-cerebro/guia.html

- **15 diapositivas** con transiciones cinematográficas, cámara lenta, luces, partículas y sonido. En pantalla van solo palabras clave: la explicación la das vos.
- **9 ilusiones comprobadas** (documentadas por el científico de la visión Michael Bach y en la literatura): Café wall, círculos de Ebbinghaus, rejilla centelleante, Lilac chaser, la bandera fantasma (postimagen), la espiral (efecto consecutivo de movimiento), Stepping feet, ceguera inducida por movimiento y tres rotaciones ambiguas (cubo, flecha en tambor y esfera, como en los videos). Después vienen memoria y efecto Mandela.
- **Partes automáticas**: dentro de cada diapositiva todo aparece solo, con el tiempo calculado según lo que tenés que decir. Vos solo pasás de diapositiva.
- **Control remoto en tu celular**: qué decir (en inglés, con la traducción abajo), datos clave de cada diapositiva, cuenta regresiva de la próxima parte con ⏸ Pausar y ⏩ Ya, cronómetro y lista de diapositivas.
- **Juego final**: tus compañeros entran con un QR o un enlace, ponen su nombre y responden 12 preguntas con 40 segundos cada una. Hay puntos por velocidad, rachas, ranking y podio con confeti.

---

## 1. Publicarla en internet (una sola vez)

1. Entrá a tu repositorio en GitHub → **Settings** → **Pages**.
2. En **Source** elegí **Deploy from a branch**.
3. En **Branch** elegí `claude/eloquent-darwin-bpvl7t`, carpeta `/ (root)` y tocá **Save**.
4. Esperá 1 o 2 minutos. La presentación queda en:

   **https://smaximilianomeneghello.github.io/Videos-forralitas/presentacion-cerebro/**

   (La dirección sin `/presentacion-cerebro/` también redirige ahí).

> Si después pasás estos archivos a otra rama, elegí esa rama en el paso 3.

## 2. El día de la exposición

1. En la netbook abrí el enlace en **Google Chrome**.
2. Escribí tu nombre en *Your name* (aparece en la portada).
3. Con tu celular **escaneá el QR** de la derecha y escribí el **PIN de 4 números**.
4. En la netbook tocá **▶ START PRESENTATION**: se pone en pantalla completa.
5. Desde ahí manejás todo con el celular:
   - Las partes de cada diapositiva aparecen **solas**. Arriba de las notas ves cuánto falta para la próxima; **⏸ Pausar** la frena y **⏩ Ya** la muestra en el momento.
   - **SIGUIENTE DIAPO** pasa a la próxima diapositiva (eso lo hacés siempre vos).
   - En la tarjeta **🎤 What to say** tenés el texto en inglés para cada momento, con la traducción abajo.
   - **☰ Diapos** salta a cualquier diapositiva.
6. Al terminar la última diapositiva se abre el **juego**:
   - Tocá **📲 Compartir enlace** y mandalo al grupo de WhatsApp, o que escaneen el QR de la pantalla.
   - Cuando estén todos, tocá **▶ COMENZAR**.
   - Con el botón verde vas pasando: respuesta correcta → ranking → siguiente pregunta → podio.
   - Si alguien pone un nombre feo, sacalo con la ✕.

### Atajos de teclado (en la netbook)

| Tecla | Qué hace |
|---|---|
| `→` | Siguiente diapositiva |
| `Espacio` | Mostrar ya la próxima parte |
| `S` | Pausar o seguir las partes automáticas |
| `←` | Anterior |
| `F` | Pantalla completa |
| `M` | Prender o apagar el sonido |
| `L` | **Modo liviano**, si la netbook va lenta |
| `P` | Volver a mostrar el QR y el PIN para conectar el celular |
| `G` | Abrir o cerrar el juego |

También funciona con un puntero/clicker USB de presentaciones.

## 3. Consejos importantes

- **Probalo un día antes en el colegio**, con el wifi del colegio. Si algo falla, avisá.
- La netbook y los celulares necesitan **internet** (wifi o datos móviles; no hace falta que estén en la misma red).
- Si el wifi del colegio bloquea la conexión, **la presentación igual funciona con las flechas del teclado**. Para el juego, pedí que se conecten con datos móviles.
- Subí el volumen de la netbook: hay efectos de sonido y música durante el juego.
- Si recargás la página por error, el control remoto se reconecta solo. La pantalla de inicio te ofrece **seguir desde la diapositiva** en la que estabas.
- Para ensayar una diapositiva puntual agregá `?slide=7` al final del enlace.

## 4. Probar en tu compu sin celular

Abrí `index.html?local=1` en una pestaña. Copiá el enlace del control que aparece debajo del QR y abrilo en otra pestaña. Con `?local=1` las pestañas se conectan entre sí sin internet.

## 5. Cambiar textos y preguntas

| Qué querés cambiar | Archivo |
|---|---|
| Tu nombre, la materia, los segundos por pregunta | `js/config.js` |
| Las preguntas del juego | `js/questions.js` (`ok` es el número de la respuesta correcta: 0, 1, 2 o 3) |
| Textos y notas de cada diapositiva (`en` = inglés, `es` = traducción) | `js/slides.js` |

## Créditos

Ilusiones basadas en trabajos de Richard Gregory y Priscilla Heard (Café wall, 1979), Hermann Ebbinghaus y E. B. Titchener (1901), Bergen y Schrauf (rejilla centelleante), Jeremy Hinton (Lilac chaser, 2005), Joseph Plateau (espiral, 1849), Stuart Anstis (Stepping feet), Bonneh, Cooperman y Sagi (ceguera inducida por movimiento, 2001), el efecto de profundidad cinética y Elizabeth Loftus. Los parámetros se tomaron de las páginas de Michael Bach (https://michaelbach.de/ot/). Todas están redibujadas con código.

Librerías: GSAP, PeerJS, qrcode-generator y canvas-confetti (están incluidas en `js/vendor/`).
