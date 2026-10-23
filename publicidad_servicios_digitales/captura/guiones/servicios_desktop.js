module.exports = { url: '../../web/servicios_habitar/index.html', w: 1440, h: 900, dpr: 1, dur: 10.5, pasos: [
  { t: 2.2, tipo: 'scroll', a: { sel: '#servicios', off: 40 }, dur: 1.4 },
  { t: 4.0, tipo: 'scroll', a: { sel: '#trabajos', off: 60 }, dur: 1.4 },
  { t: 5.8, tipo: 'scroll', a: { sel: '#contacto', off: 100 }, dur: 1.2 },
  { t: 7.1, tipo: 'tap', sel: '#nombre' },
  { t: 7.4, tipo: 'escribir', sel: '#nombre', texto: 'Lucía Fernández', cps: 22 },
  { t: 8.3, tipo: 'tap', sel: '#email' },
  { t: 8.6, tipo: 'escribir', sel: '#email', texto: 'lucia@ejemplo.com', cps: 26 },
  { t: 9.4, tipo: 'tap', sel: '#form button[type=submit]' } ] };
