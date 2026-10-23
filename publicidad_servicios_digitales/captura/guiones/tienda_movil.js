module.exports = { url: '../../web/tienda_orbe/index.html', w: 390, h: 844, dpr: 2, mobile: true, dur: 7, pasos: [
  { t: 1.8, tipo: 'scroll', a: { sel: '#catalogo', off: 80 }, dur: 1.4 },
  { t: 3.8, tipo: 'tap', sel: '.prod:nth-child(1) .agregar' },
  { t: 4.8, tipo: 'scroll', a: { sel: '.prod:nth-child(5)', off: 100 }, dur: 1.4 } ] };
