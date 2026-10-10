// Graba la demo en formato vertical 1080x1920, cuadro por cuadro (30 fps) para que quede perfectamente fluida.
//   node grabar_video.js            -> libro_recuerdos.mp4
//   node grabar_video.js --prueba   -> solo unos cuadros sueltos (png) para revisar el diseño
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path'), fs = require('fs');
const FPS = 30, W = 1080, H = 1920;
const prueba = process.argv.includes('--prueba');
const out = path.join(__dirname, 'libro_recuerdos.mp4');

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME || undefined, args:['--enable-gpu-rasterization','--ignore-gpu-blocklist'] });
  const page = await (await browser.newContext({ viewport:{width:W,height:H} })).newPage();
  page.on('pageerror', e => console.log('ERROR en la página:', e.message));
  await page.clock.install({ time: 0 });
  await page.goto('file://' + path.join(__dirname, 'index.html'));
  await page.waitForFunction(() => window.__ready);
  await page.clock.pauseAt(5000);   // congela el reloj: de acá en adelante avanza solo cuadro a cuadro

  let ff = null, n = 0;
  if (!prueba) {
    ff = spawn('ffmpeg', ['-y','-loglevel','error','-f','image2pipe','-framerate',String(FPS),'-c:v','mjpeg','-i','-',
      '-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart', out], { stdio:['pipe','inherit','inherit'] });
  }
  const frame = async () => {
    await page.clock.runFor(1000 / FPS);
    if (!prueba) {
      const buf = await page.screenshot({ type:'jpeg', quality:92 });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    }
    n++;
  };
  const wait = async ms => { for (let i = 0; i < Math.round(ms*FPS/1000); i++) await frame(); };
  const snap = async name => { if (prueba) await page.screenshot({ path: path.join(process.env.SCRATCH||__dirname, name) }); };
  const cap = t => page.evaluate(t => setCaption(t), t);
  const click = sel => page.evaluate(s => document.querySelector(s).click(), sel);
  const next = async c => { for (let i=0;i<c;i++){ await click('#next'); await wait(1700); if(prueba&&i==0){} await wait(450); } };
  const prev = async c => { for (let i=0;i<c;i++){ await click('#prev'); await wait(1700); await wait(450); } };

  await page.evaluate(() => setLayout(2));
  await cap('Tu libro de recuerdos: pasá las hojas con los botones'); await wait(2600);
  if (prueba) { await snap('p_inicio.png'); await click('#next'); await wait(700); await snap('p_giro1.png'); await wait(450); await snap('p_giro2.png'); await wait(900); await snap('p_giro3.png'); await browser.close(); return; }

  await cap('2 fotos por hoja'); await next(3);
  await cap('Volvemos al principio'); await prev(3); await wait(300);
  await click('#segLayout [data-v="1"]'); await cap('1 foto por hoja: para destacar los mejores momentos'); await wait(1600);
  await next(3); await prev(3);
  await click('#segLayout [data-v="3"]'); await cap('3 fotos por hoja: más recuerdos en cada página'); await wait(1600);
  await next(2); await prev(2);
  await click('#segLayout [data-v="mix"]'); await cap('Mixto: 1, 2 y 3 fotos combinadas'); await wait(1600);
  await next(3);
  await cap('Vos elegís cómo acomodar tus fotos'); await wait(3200);
  await cap(''); await wait(700);

  ff.stdin.end(); await new Promise(r => ff.on('close', r));
  await browser.close();
  console.log('listo: libro_recuerdos.mp4 (' + n + ' cuadros)');
})();
