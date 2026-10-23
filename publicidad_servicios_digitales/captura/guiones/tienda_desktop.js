module.exports = { url: '../../web/tienda_orbe/index.html', w: 1440, h: 900, dpr: 1, dur: 9, pasos: [
  { t: 2.4, tipo: 'scroll', a: { sel: '#catalogo', off: 90 }, dur: 1.5 },
  { t: 4.4, tipo: 'tap', sel: '#filtros button[data-f="audio"]' },
  { t: 5.6, tipo: 'tap', sel: '#filtros button[data-f="todos"]' },
  { t: 6.5, tipo: 'tap', sel: '.prod:nth-child(2) .agregar' },
  { t: 7.3, tipo: 'scroll', a: { sel: '#beneficios', off: 120 }, dur: 1.4 } ] };
