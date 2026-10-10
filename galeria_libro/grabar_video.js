// Graba una demo del libro de recuerdos: node grabar_video.js  (genera libro_recuerdos.mp4)
const { chromium } = require('playwright');
const { execSync } = require('child_process');
const path = require('path'), fs = require('fs');
const out = __dirname, tmp = path.join(out, '_rec');
fs.rmSync(tmp, {recursive:true, force:true});
const wait = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME || undefined });
  const ctx = await browser.newContext({ viewport:{width:1280,height:720}, recordVideo:{dir:tmp, size:{width:1280,height:720}} });
  const page = await ctx.newPage();
  await page.goto('file://' + path.join(out, 'index.html'));
  const cap = t => page.evaluate(t => setCaption(t), t);
  const next = async n => { for (let i=0;i<n;i++){ await page.click('#next'); await wait(1700); } };
  const prev = async n => { for (let i=0;i<n;i++){ await page.click('#prev'); await wait(1700); } };

  await page.evaluate(() => setLayout(2));
  await cap('Libro de recuerdos: pasá las hojas con los botones de cada lado'); await wait(2800);
  await cap('2 fotos por hoja'); await next(3);
  await cap('Volvemos al principio'); await prev(3); await wait(500);

  await page.click('#segLayout [data-v="1"]'); await cap('1 foto por hoja — para destacar los mejores momentos'); await wait(1800);
  await next(3); await prev(3);

  await page.click('#segLayout [data-v="3"]'); await cap('3 fotos por hoja — más recuerdos en cada página'); await wait(1800);
  await next(2); await prev(2);

  await page.click('#segLayout [data-v="mix"]'); await cap('Mixto: 1, 2 y 3 fotos combinadas'); await wait(1800);
  await next(3);
  await cap('El cliente elige cómo acomodar sus fotos'); await wait(3000);
  await cap(''); await wait(500);

  await ctx.close(); await browser.close();
  const webm = fs.readdirSync(tmp).find(f => f.endsWith('.webm'));
  execSync(`ffmpeg -y -loglevel error -i "${path.join(tmp,webm)}" -c:v libx264 -pix_fmt yuv420p -crf 20 -movflags +faststart "${path.join(out,'libro_recuerdos.mp4')}"`);
  fs.rmSync(tmp, {recursive:true, force:true});
  console.log('listo: libro_recuerdos.mp4');
})();
