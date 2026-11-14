// Render reel-kit/overlay.html to a transparent PNG sequence for a reel.
// usage: node render_overlay.js <reel_dir> [preview|final] [t1,t2,...]   (times -> test stills only)
// needs NODE_PATH=$(npm root -g) for the preinstalled playwright
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const dir = path.resolve(process.argv[2]);
const mode = process.argv[3] || 'preview';
const R = JSON.parse(fs.readFileSync(path.join(dir, 'reel.json')));
const edl = JSON.parse(fs.readFileSync(path.join(dir, 'work', 'edl.json')));
const exp = R.export || {};
const FPS = mode === 'preview' ? 30 : (exp.fps || 60);
const DSF = mode === 'preview' ? 1 : (exp.scale || 2);
const only = process.argv[4] ? process.argv[4].split(',').map(Number) : null;
const frames = only ? only.map(t => Math.round(t * FPS)) : [...Array(Math.ceil(edl.duration * FPS)).keys()];
const out = path.join(dir, 'work', only ? 'ovl_test' : `ovl_${mode}`);
fs.rmSync(out, { recursive: true, force: true });
fs.mkdirSync(out, { recursive: true });
const WORKERS = 4;

(async () => {
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files'] });
  const t0 = Date.now();
  await Promise.all([...Array(WORKERS).keys()].map(async wi => {
    const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: DSF });
    await page.goto('file://' + path.join(__dirname, 'overlay.html'));
    await page.evaluate(e => window.build(e), edl);
    await page.evaluate(() => document.fonts.ready);
    for (let k = wi; k < frames.length; k += WORKERS) {
      const f = frames[k];
      await page.evaluate(t => window.setTime(t), f / FPS);
      await page.screenshot({ path: path.join(out, `${String(f).padStart(5, '0')}.png`), omitBackground: true });
      if (wi === 0 && k % 240 === 0) console.log(`frame ${k}/${frames.length} ${((Date.now() - t0) / 1000).toFixed(0)}s`);
    }
  }));
  await browser.close();
  console.log(`overlay ${mode}: ${frames.length} frames @${FPS}fps x${DSF} in ${((Date.now() - t0) / 1000).toFixed(0)}s -> ${out}`);
})();
