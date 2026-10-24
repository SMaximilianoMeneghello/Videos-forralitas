# 🧠 Tu cerebro te miente

Presentación interactiva sobre ilusiones ópticas y trucos de la mente, para una exposición de unos 30 minutos. La controlás desde el celular y al final se juega un juego tipo Kahoot.

- **20 diapositivas** con transiciones cinematográficas, cámara lenta, luces, partículas y sonido.
- **9 momentos interactivos**: punto ciego, líneas de Müller-Lyer, tablero de Adelson, el vestido, la bandera fantasma, el efecto Stroop, el desafío del gorila, encontrá la diferencia y el efecto Mandela.
- **Control remoto en tu celular**: botones grandes, notas de qué decir en cada paso, cronómetro y lista de diapositivas.
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
2. Escribí tu nombre (aparece en la portada).
3. Con tu celular **escaneá el QR** de la derecha y escribí el **PIN de 4 números**.
4. En la netbook tocá **▶ COMENZAR PRESENTACIÓN**: se pone en pantalla completa.
5. Desde ahí manejás todo con el celular:
   - **SIGUIENTE** avanza. En las diapositivas interactivas cada toque revela la próxima parte.
   - En la tarjeta **🎤 Qué decir** tenés el texto para cada momento.
   - **☰ Diapos** salta a cualquier diapositiva.
6. Al terminar la última diapositiva se abre el **juego**:
   - Tocá **📲 Compartir enlace** y mandalo al grupo de WhatsApp, o que escaneen el QR de la pantalla.
   - Cuando estén todos, tocá **▶ COMENZAR**.
   - Con el botón verde vas pasando: respuesta correcta → ranking → siguiente pregunta → podio.
   - Si alguien pone un nombre feo, sacalo con la ✕.

### Atajos de teclado (en la netbook)

| Tecla | Qué hace |
|---|---|
| `→` / `Espacio` | Siguiente |
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
| Textos y notas de cada diapositiva | `js/slides.js` |

## Créditos

Ilusiones basadas en trabajos de Franz Müller-Lyer (1889), Edward H. Adelson (1995), J. R. Stroop (1935), Simons y Chabris (1999), Akiyoshi Kitaoka y Elizabeth Loftus. Todas están redibujadas con código.

Librerías: GSAP, PeerJS, qrcode-generator y canvas-confetti (están incluidas en `js/vendor/`).
