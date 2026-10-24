// ============================================================
//  PREGUNTAS DEL JUEGO
//  - q: la pregunta
//  - a: las 4 opciones (en orden: rojo ▲, azul ◆, amarillo ●, verde ■)
//  - ok: número de la opción correcta (0, 1, 2 o 3)
//  Podés agregar, sacar o cambiar preguntas libremente.
// ============================================================
window.QUESTIONS = [
  {
    q: "¿Por qué tenemos un “punto ciego” en cada ojo?",
    a: ["Porque el párpado lo tapa", "Porque ahí sale el nervio óptico y no hay receptores", "Porque es una zona lastimada", "Porque solo pasa de noche"],
    ok: 1,
  },
  {
    q: "En la ilusión de las flechas (Müller-Lyer), ¿cómo eran las dos líneas?",
    a: ["Exactamente iguales", "Una era el doble de larga", "La A era más larga", "La B era más larga"],
    ok: 0,
  },
  {
    q: "En el tablero con sombra, las casillas A y B…",
    a: ["A era más clara", "B era más oscura", "Cambiaban de color", "Eran del mismo color"],
    ok: 3,
  },
  {
    q: "¿De qué color era en realidad “el vestido” de 2015?",
    a: ["Blanco y dorado", "Verde y gris", "Azul y negro", "Rosa y blanco"],
    ok: 2,
  },
  {
    q: "¿Qué porcentaje de la energía del cuerpo consume el cerebro, más o menos?",
    a: ["2 %", "5 %", "50 %", "20 %"],
    ok: 3,
  },
  {
    q: "¿Cómo llega la imagen a la retina?",
    a: ["Tal cual la vemos", "Invertida (al revés)", "En blanco y negro", "Partida en dos"],
    ok: 1,
  },
  {
    q: "En el juego de los colores (efecto Stroop), ¿qué era lo difícil?",
    a: ["Decir el color de la letra y no la palabra", "Leer palabras largas", "Recordar los colores", "Leer en otro idioma"],
    ok: 0,
  },
  {
    q: "¿Cómo se llama ver caras en objetos como enchufes o autos?",
    a: ["Hipnosis", "Efecto Mandela", "Daltonismo", "Pareidolia"],
    ok: 3,
  },
  {
    q: "En el desafío del gorila, ¿qué tenían que hacer?",
    a: ["Cerrar los ojos", "Mirar el celular", "Contar los pases del equipo blanco", "Buscar al gorila"],
    ok: 2,
  },
  {
    q: "¿Qué es el “efecto Mandela”?",
    a: ["Ver colores que no existen", "Que mucha gente recuerde lo mismo de forma equivocada", "Escuchar palabras distintas en un audio", "No ver algo que cambia"],
    ok: 1,
  },
  {
    q: "¿Pikachu tiene la punta de la cola negra?",
    a: ["Sí, siempre la tuvo", "Solo en las películas", "No, nunca la tuvo", "Solo en los videojuegos"],
    ok: 2,
  },
  {
    q: "Según la exposición, tu cerebro funciona más como…",
    a: ["Una máquina de predicciones", "Una cámara de fotos", "Un disco duro", "Una calculadora"],
    ok: 0,
  },
];
