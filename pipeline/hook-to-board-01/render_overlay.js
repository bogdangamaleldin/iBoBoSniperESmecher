// Render overlay.html to a transparent PNG sequence at 30fps.
// usage: node render_overlay.js [onlyTimesCsv]
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const dir = __dirname;
const edl = JSON.parse(fs.readFileSync(path.join(dir, 'edl.json')));
const FPS = 30, WORKERS = 4;
const only = process.argv[2] ? process.argv[2].split(',').map(Number) : null;
const frames = only ? only.map(t => Math.round(t * FPS)) : [...Array(Math.ceil(edl.duration * FPS)).keys()];
const out = path.join(dir, only ? 'ovl_test' : 'ovl');
fs.mkdirSync(out, { recursive: true });

(async () => {
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files'] });
  const t0 = Date.now();
  await Promise.all([...Array(WORKERS).keys()].map(async wi => {
    const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
    await page.goto('file://' + path.join(dir, 'overlay.html'));
    await page.evaluate(e => window.build(e), edl);
    await page.evaluate(() => document.fonts.ready);
    for (let k = wi; k < frames.length; k += WORKERS) {
      const f = frames[k];
      await page.evaluate(t => window.setTime(t), f / FPS);
      await page.screenshot({ path: path.join(out, `${String(f).padStart(5, '0')}.png`), omitBackground: true });
      if (wi === 0 && k % 120 === 0) console.log(`frame ${k}/${frames.length} ${((Date.now() - t0) / 1000).toFixed(0)}s`);
    }
  }));
  await browser.close();
  console.log('done', frames.length, 'frames in', ((Date.now() - t0) / 1000).toFixed(0), 's');
})();
