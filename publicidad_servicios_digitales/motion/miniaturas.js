// Exporta la miniatura vertical, la horizontal y los laterales transparentes de la versión 16:9.
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const path = require('path');
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args: ['--no-sandbox'] });
  for (const [modo, w, h, out, transp] of [['vertical', 1080, 1920, 'salida/MINIATURA_VERTICAL.jpg'], ['horizontal', 1920, 1080, 'salida/MINIATURA_HORIZONTAL.jpg'], ['laterales', 1920, 1080, 'build/laterales.png', true]]) {
    const p = await b.newPage({ viewport: { width: w, height: h } });
    await p.goto('file://' + path.join(__dirname, 'miniatura.html') + '#' + modo);
    await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(400);
    await p.screenshot({ path: path.join(__dirname, '..', out), type: transp ? 'png' : 'jpeg', quality: transp ? undefined : 92, omitBackground: !!transp });
    await p.close();
  }
  await b.close();
})();
