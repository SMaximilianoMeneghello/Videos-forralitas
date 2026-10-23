// Recorrido real de la invitación web en un celular (390x844 @2x)
module.exports = {
  url: '../../web/invitacion_15_valentina/index.html',
  w: 390, h: 844, dpr: 2, mobile: true, dur: 26,
  pasos: [
    { t: 1.8, tipo: 'tap', sel: '#btnAbrir' },
    { t: 6.2, tipo: 'scroll', a: { sel: '#frase', off: 40 }, dur: 1.4 },
    { t: 8.0, tipo: 'scroll', a: { sel: '#cuenta', off: 150 }, dur: 1.2 },
    { t: 11.6, tipo: 'scroll', a: { sel: '#lugar', off: 30 }, dur: 1.5 },
    { t: 14.0, tipo: 'tap', sel: '#btnMapa' },
    { t: 15.0, tipo: 'scroll', a: { sel: '#galeria', off: 20 }, dur: 1.5 },
    { t: 17.4, tipo: 'tap', sel: '.foto.alta' },
    { t: 19.0, tipo: 'tap', x: 200, y: 120 },
    { t: 19.8, tipo: 'scroll', a: { sel: '#confirmar', off: 230 }, dur: 1.2 },
    { t: 21.3, tipo: 'tap', sel: '#btnRsvp' },
    { t: 22.0, tipo: 'escribir', sel: '#fNombre', texto: 'Martina Gómez', cps: 14 },
    { t: 23.2, tipo: 'tap', sel: '.contador button[data-d="1"]' },
    { t: 24.0, tipo: 'tap', sel: '.btn.whatsapp' }
  ]
};
