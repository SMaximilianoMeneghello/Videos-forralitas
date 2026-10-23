// Renderiza la composición cuadro a cuadro con Chromium.
// Uso: node motion/render.js prueba <t1> <t2> ...           -> PNG en build/prueba
//      node motion/render.js cuadros <desde> <hasta> <dir>    -> JPG de alta calidad
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const path = require('path'), fs = require('fs');
(async () => {
  const [modo, ...args] = process.argv.slice(2);
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args: ['--no-sandbox', '--font-render-hinting=none', '--allow-file-access-from-files'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('pageerror', e => console.log('PAGEERR', e.stack));
  page.on('console', m => { if (m.type() === 'error') console.log('CONSOLE', m.text()); });
  await page.goto('file://' + path.join(__dirname, 'publicidad.html'));
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(500);
  if (modo === 'prueba') {
    const dir = path.join(__dirname, '../build/prueba'); fs.mkdirSync(dir, { recursive: true });
    for (const t of args) { await page.evaluate(t => render(t), +t); await page.screenshot({ path: `${dir}/t${(+t).toFixed(2)}.jpg`, type: 'jpeg', quality: 88 }); }
  } else {
    const [a, b, dir] = args; fs.mkdirSync(dir, { recursive: true });
    for (let f = +a; f < +b; f++) {
      await page.evaluate(t => render(t), f / 30);
      await page.screenshot({ path: `${dir}/f${String(f).padStart(5, '0')}.jpg`, type: 'jpeg', quality: 94 });
    }
  }
  await browser.close();
})();
