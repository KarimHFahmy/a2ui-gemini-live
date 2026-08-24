/**
 * Catalog regression check.
 *
 * Serves the built `preview.html`, renders every captured surface in a real
 * browser in both colour schemes, and fails if anything comes out as a missing
 * child placeholder, an unknown component, an empty chart, literal Markdown or
 * a page that scrolls sideways. It also scrolls the stage and checks that the
 * pinned profile stays opaque — a sticky header that lets the conversation
 * show through is only visible mid-scroll. Run it after touching a component,
 * a schema or a composer.
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
      const q = (sel) => document.querySelectorAll(sel).length;
      return {
        surfaces: q('.surface'),
        ids: [...document.querySelectorAll('[data-surface-id]')].map(e => e.dataset.surfaceId),
        // A2UI failure modes: a child that never arrived, or a component the
        // catalog does not whitelist.
        placeholders: (html.match(/\[Loading /g) || []).length,
        unknown: (html.match(/Unknown component/g) || []).length,
        // Our two additions.
        charts: q('.chart__svg'),
        chartEmpty: q('.chart__empty'),
        tables: q('.compare__table'),
        // Official basic-catalog components the composers rely on.
        cards: q('.a2ui-card'),
        headings: q('.surface h2'),
        lists: q('.surface ul'),
        chips: q('.surface button.chip'),
        buttons: q('.surface button:not(.chip)'),
        modals: q('.a2ui-modal-trigger'),
        // Literal Markdown on screen means the renderer has no Markdown
        // renderer wired up, or a non-Markdown variant was used with syntax.
        rawMarkdown: (document.body.innerText.match(/(^|\s)(\*\*|##+\s|- \*\*)/gm) || []).length,
        hScroll: document.documentElement.scrollWidth > document.documentElement.clientWidth,
      };
    });
    const bad =
      stats.placeholders ||
      stats.unknown ||
      stats.chartEmpty ||
      stats.rawMarkdown ||
      stats.hScroll ||
      stats.charts === 0 ||
      stats.tables === 0 ||
      stats.cards === 0 ||
      stats.headings === 0 ||
      stats.modals === 0;
    if (bad) failures++;
    console.log(`[${scheme}] ${journey}:`, JSON.stringify(stats));
    const pinned = await checkPinnedBand(page);
    if (pinned.problems.length) {
      failures++;
      console.log(`  [${scheme}] ${journey} pinned band: ${pinned.problems.join("; ")}`);
    }

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

/**
 * Scrolls the stage and inspects the sticky profile band.
 *
 * The band has to be fully opaque and flush with the top of the scrollport.
 * A transparent edge — or a sticky inset measured from the padding box rather
 * than the border box — leaves a strip the conversation scrolls through, which
 * looks like text printed on top of a chart. That is only visible mid-scroll,
 * so a static render will never catch it.
 */
async function checkPinnedBand(page) {
  if (!(await page.locator('.stage__pinned').count())) return {problems: []};

  await page.evaluate(() => document.querySelector('.stage').scrollBy(0, 700));
  await page.waitForTimeout(250);

  return page.evaluate(() => {
    const problems = [];
    const stage = document.querySelector('.stage');
    const pinned = document.querySelector('.stage__pinned');
    const surface = document.querySelector('.surface--pinned');

    if (Math.round(pinned.getBoundingClientRect().top - stage.getBoundingClientRect().top) !== 0) {
      problems.push('band is not flush with the top of the stage');
    }

    const background = getComputedStyle(pinned).backgroundImage;
    if (background !== 'none') {
      problems.push(`band background is not a solid colour (${background})`);
    }

    // Every text leaf in the band must sit on a card of its own, so nothing
    // relies on the band's background alone.
    const bare = [...pinned.querySelectorAll('h3, h5, li, em')].filter(el => !el.closest('.a2ui-card'));
    if (bare.length) {
      problems.push(`${bare.length} element(s) in the band sit outside a card`);
    }

    if (surface && surface.scrollHeight > surface.clientHeight + 1) {
      problems.push(`profile exceeds its height cap (${surface.scrollHeight}px)`);
    }

    return {problems};
  });
}
