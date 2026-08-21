/**
 * Catalog regression check.
 *
 * Serves the built `preview.html`, renders every captured surface in a real
 * browser in both colour schemes, and fails if anything comes out as a missing
 * child placeholder, an unknown component, an empty chart or a page that
 * scrolls sideways. Run it after touching a component, a schema or a composer.
 *
 *   make check-catalog
 */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

import {chromium} from 'playwright';

const ROOT = path.resolve(import.meta.dirname, '../../backend/static');
const MIME = {'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json','.svg':'image/svg+xml'};

const server = http.createServer((req,res)=>{
  const url = req.url.split('?')[0];
  const file = path.join(ROOT, url === '/' ? 'index.html' : url);
  if (!fs.existsSync(file) || fs.statSync(file).isDirectory()) { res.writeHead(404); return res.end('nf'); }
  res.writeHead(200, {'Content-Type': MIME[path.extname(file)] ?? 'application/octet-stream'});
  fs.createReadStream(file).pipe(res);
});
await new Promise(r => server.listen(4173, r));

const shotDir = process.env.SHOT_DIR ?? '/tmp';

// Prefer a pre-installed Chromium when one is present (CI images, sandboxes)
// so this never triggers a browser download.
const preinstalled = process.env.CHROMIUM_PATH ?? '/opt/pw-browsers/chromium';
const browser = await chromium.launch(
  fs.existsSync(preinstalled) ? {executablePath: preinstalled} : {},
);
let failures = 0;

for (const scheme of ['light','dark']) {
  const ctx = await browser.newContext({viewport:{width:1440,height:1000}, colorScheme: scheme, deviceScaleFactor: 2});
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  // Google Fonts is unreachable in this sandbox; the fallback stack covers it.
  page.on('console', m => {
    const t = m.text();
    if (m.type()==='error' && !/ERR_CONNECTION_RESET|ERR_FAILED|fonts\.(googleapis|gstatic)/.test(t)) {
      errors.push('console: '+t);
    }
  });
  await page.route('**fonts.googleapis.com**', r => r.abort());
  await page.route('**fonts.gstatic.com**', r => r.abort());

  await page.goto('http://localhost:4173/preview.html', {waitUntil:'networkidle'});
  await page.waitForSelector('.surface', {timeout: 8000});

  for (const journey of ['Mein Zuhause','Meine Mobilität']) {
    await page.getByRole('button', {name: journey}).click();
    await page.waitForTimeout(400);
    const stats = await page.evaluate(() => {
      const html = document.body.innerHTML;
      return {
        surfaces: document.querySelectorAll('.surface').length,
        ids: [...document.querySelectorAll('[data-surface-id]')].map(e=>e.dataset.surfaceId),
        placeholders: (html.match(/\[Loading /g)||[]).length,
        unknown: (html.match(/Unknown component/g)||[]).length,
        charts: document.querySelectorAll('.chart__svg').length,
        chartEmpty: document.querySelectorAll('.chart__empty').length,
        tables: document.querySelectorAll('.compare__table').length,
        timelines: document.querySelectorAll('.timeline__list').length,
        recs: document.querySelectorAll('.recommendation').length,
        insights: document.querySelectorAll('.insight').length,
        scenarios: document.querySelectorAll('.scenario').length,
        assumptions: document.querySelectorAll('.assumptions').length,
        ctas: document.querySelectorAll('.cta').length,
        profiles: document.querySelectorAll('.profile').length,
        emptyFacts: [...document.querySelectorAll('.profile__facts')].filter(e=>e.children.length===0).length,
        hScroll: document.documentElement.scrollWidth > document.documentElement.clientWidth,
      };
    });
    const bad = stats.placeholders || stats.unknown || stats.chartEmpty || stats.emptyFacts || stats.hScroll;
    if (bad) failures++;
    console.log(`[${scheme}] ${journey}:`, JSON.stringify(stats));
    if (scheme==='light') {
      const slug = journey==='Mein Zuhause'?'energie':'mobilitaet';
      await page.screenshot({path: path.resolve(shotDir, `${slug}.png`), fullPage: true});
    }
  }
  if (errors.length) { console.log(`[${scheme}] PAGE ERRORS:`, errors.slice(0,5)); failures++; }
  await ctx.close();
}

await browser.close();
server.close();
console.log(failures ? `\nFAILURES: ${failures}` : '\nALL CHECKS PASSED');
process.exit(failures?1:0);
