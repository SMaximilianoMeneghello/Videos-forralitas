// Uso: node render.js test t1 t2 ...   -> PNGs de prueba en ./prueba
//      node render.js frames <desde> <hasta> <carpeta>  -> frames JPG
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const path = require('path'), fs = require('fs');
(async () => {
  const [mode, ...args] = process.argv.slice(2);
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args: ['--no-sandbox', '--font-render-hinting=none'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('pageerror', e => console.log('PAGEERR', e.message));
  await page.goto('file://' + path.join(__dirname, 'video.html'));
  await page.evaluate(() => document.fonts.ready);
  if (mode === 'test') {
    fs.mkdirSync('prueba', { recursive: true });
    for (const t of args) { await page.evaluate(t => render(t), +t); await page.screenshot({ path: `prueba/t${t}.png` }); }
  } else {
    const [a, b, dir] = args; fs.mkdirSync(dir, { recursive: true });
    for (let f = +a; f < +b; f++) {
      await page.evaluate(t => render(t), f / 30);
      await page.screenshot({ path: `${dir}/f${String(f).padStart(4, '0')}.jpg`, type: 'jpeg', quality: 93 });
    }
  }
  await browser.close();
})();
