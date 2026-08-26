/**
 * Catalog regression check.
 *
 * Serves the built `preview.html`, renders every captured surface in a real
 * browser in both colour schemes, and fails if anything comes out as a missing
 * child placeholder, an unknown component, an empty chart, literal Markdown or
 * a page that scrolls sideways. It also checks the context column — progress
 * plus "Das habe ich verstanden" — and the interactive what-if surface, whose
 * figures are computed in the browser rather than composed server-side. Run it
 * after touching a component, a schema or a composer.
 *
 *   make check-catalog
 */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

import {chromium} from 'playwright';

const ROOT = path.resolve(import.meta.dirname, '../../backend/static');
const MIME = {
  '.html': 'text/html',
  '.js': 'text/javascript',
  '.css': 'text/css',
  '.json': 'application/json',
  '.svg': 'image/svg+xml',
};

const server = http.createServer((req, res) => {
  const url = req.url.split('?')[0];
  const file = path.join(ROOT, url === '/' ? 'index.html' : url);
  if (!fs.existsSync(file) || fs.statSync(file).isDirectory()) {
    res.writeHead(404);
    return res.end('nf');
  }
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

for (const scheme of ['light', 'dark']) {
  const ctx = await browser.newContext({
    viewport: {width: 1440, height: 1000},
    colorScheme: scheme,
    deviceScaleFactor: 2,
  });
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  page.on('console', m => {
    const t = m.text();
    if (m.type() === 'error' && !/ERR_CONNECTION_RESET|ERR_FAILED/.test(t)) {
      errors.push('console: ' + t);
    }
  });
  // Nothing is fetched from a font CDN any more. If something tries, the type
  // has quietly gone back to being a network dependency.
  await page.route('**fonts.googleapis.com**', r => {
    errors.push('the page requested Google Fonts; the type is meant to be self-hosted');
    r.abort();
  });
  await page.route('**fonts.gstatic.com**', r => {
    errors.push('the page requested a font from gstatic; the type is meant to be self-hosted');
    r.abort();
  });

  await page.goto('http://localhost:4173/preview.html', {waitUntil: 'networkidle'});
  await page.waitForSelector('.surface', {timeout: 8000});

  const type = await checkType(page);
  if (type.problems.length) {
    failures++;
    console.log(`  [${scheme}] type: ${type.problems.join('; ')}`);
  }

  for (const journey of ['Mein Zuhause', 'Meine Mobilität']) {
    await page.getByRole('button', {name: journey}).click();
    await page.waitForTimeout(400);
    const stats = await page.evaluate(() => {
      const html = document.body.innerHTML;
      const q = sel => document.querySelectorAll(sel).length;
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
        sliders: q(".surface input[type='range']"),
        stats: q('.stat'),
        // An axis label that runs off the left of its SVG reads as a data
        // error, not a layout one: "125 Tsd. €" clipped to "25 Tsd. €" is a
        // plausible number. The gutter is computed from the label width, and
        // this is what proves it.
        clippedTicks: [...document.querySelectorAll('.chart__tick, .chart__label')].filter(
          node => node.getBBox().x < -0.5,
        ).length,
        // Literal Markdown on screen means the renderer has no Markdown
        // renderer wired up, or a non-Markdown variant was used with syntax.
        rawMarkdown: (document.body.innerText.match(/(^|\s)(\*\*|##+\s|- \*\*)/gm) || []).length,
        hScroll: document.documentElement.scrollWidth > document.documentElement.clientWidth,
        /*
         * The shell fits the viewport: only `.stage` and `.aside` scroll. A
         * scrolling *document* means something has escaped into document
         * coordinates — an absolutely positioned element with no positioned
         * ancestor is the usual way — and it shows up as a second scrollbar
         * that runs off into empty page.
         */
        vScroll: document.documentElement.scrollHeight - document.documentElement.clientHeight,
      };
    });
    const bad =
      stats.placeholders ||
      stats.unknown ||
      stats.chartEmpty ||
      stats.rawMarkdown ||
      stats.hScroll ||
      stats.vScroll ||
      stats.charts === 0 ||
      stats.tables === 0 ||
      stats.cards === 0 ||
      stats.headings === 0 ||
      stats.modals === 0 ||
      stats.sliders === 0 ||
      stats.stats === 0 ||
      stats.clippedTicks;
    if (bad) failures++;
    console.log(`[${scheme}] ${journey}:`, JSON.stringify(stats));
    const aside = await checkContextAside(page);
    if (aside.problems.length) {
      failures++;
      console.log(`  [${scheme}] ${journey} context column: ${aside.problems.join('; ')}`);
    }

    const whatIf = await checkWhatIf(page);
    if (whatIf.problems.length) {
      failures++;
      console.log(`  [${scheme}] ${journey} what-if: ${whatIf.problems.join('; ')}`);
    }

    const tone = await checkTone(page);
    if (tone.problems.length) {
      failures++;
      console.log(`  [${scheme}] ${journey} tone: ${tone.problems.join('; ')}`);
    }

    if (scheme === 'light') {
      const slug = journey === 'Mein Zuhause' ? 'energie' : 'mobilitaet';
      await page.screenshot({path: path.resolve(shotDir, `${slug}.png`), fullPage: true});
    }
  }
  if (errors.length) {
    console.log(`[${scheme}] PAGE ERRORS:`, errors.slice(0, 5));
    failures++;
  }
  await ctx.close();
}

await browser.close();
server.close();
console.log(failures ? `\nFAILURES: ${failures}` : '\nALL CHECKS PASSED');
process.exit(failures ? 1 : 0);

/**
 * Checks the context column: progress, then "Das habe ich verstanden".
 *
 * Both are persistent context, so they belong beside the conversation rather
 * than in it. As a sticky band above the stage the profile cost a third of the
 * height and let content scroll behind it; this asserts it stays out of the
 * flow and keeps its own scroll.
 */
async function checkContextAside(page) {
  return page.evaluate(() => {
    const problems = [];
    const aside = document.querySelector('.aside');
    const stage = document.querySelector('.stage');

    if (!aside) {
      problems.push('no profile column rendered');
      return {problems};
    }

    // The profile must not also appear among the conversation surfaces.
    if (document.querySelector('.stage__flow [data-surface-id="profil"]')) {
      problems.push('the profile is still in the conversation flow');
    }

    const asideBox = aside.getBoundingClientRect();
    const stageBox = stage.getBoundingClientRect();
    const sideBySide = asideBox.left >= stageBox.right - 1;
    const stacked = asideBox.bottom <= stageBox.top + 1;
    if (!sideBySide && !stacked) {
      problems.push('the profile column overlaps the conversation');
    }

    if (getComputedStyle(aside).overflowY !== 'auto') {
      problems.push('the profile column does not scroll on its own');
    }

    // A live voice experience renders no transcript.
    if (document.querySelector('.transcript')) {
      problems.push('a transcript panel is present');
    }

    // Progress is only honest if a step counts as done when its surface is on
    // screen — no more, no less.
    const progress = aside.querySelector('.progress');
    if (!progress) {
      problems.push('no progress indicator');
    } else {
      const total = Number(progress.dataset.total);
      const done = Number(progress.dataset.done);
      const onScreen = progress.querySelectorAll('.progress__step[data-state="done"]').length;
      if (!total) problems.push('the arc is empty');
      if (done !== onScreen) problems.push(`progress counts ${done} but marks ${onScreen}`);
      if (done > total) problems.push('more steps done than exist');
      if (done === 0) problems.push('no step marked done despite rendered surfaces');
    }

    return {problems};
  });
}

/**
 * Checks that the type on screen is the type that was chosen.
 *
 * The previous stack loaded Inter from a CDN with no self-hosted fallback, so
 * anywhere that CDN is blocked — which is a lot of German corporate networks —
 * the whole design silently rendered in Arial and nothing said so. The faces
 * are vendored now, and this fails if they are not actually in use.
 */
async function checkType(page) {
  await page.evaluate(() => document.fonts.ready);
  return page.evaluate(() => {
    const problems = [];
    for (const face of ['IBM Plex Sans', 'IBM Plex Mono']) {
      if (!document.fonts.check(`16px "${face}"`)) problems.push(`${face} did not load`);
    }

    // And that both roles are actually doing their job on the page.
    const body = getComputedStyle(document.body).fontFamily;
    if (!body.includes('IBM Plex Sans')) problems.push(`body is set in ${body}`);

    const tick = document.querySelector('.chart__tick');
    if (tick && !getComputedStyle(tick).fontFamily.includes('IBM Plex Mono')) {
      problems.push('chart readings are not set in the mono');
    }
    return {problems};
  });
}

/**
 * Checks that colour tells the truth about each figure.
 *
 * Every headline metric used to be painted with the brand accent, including
 * the one whose job is to say "this is more expensive for you". Tone now
 * arrives as data, so this reads the computed colour back out of the browser
 * and fails if a caution figure is wearing the positive colour — the exact
 * shape of the original bug, in both themes where the tokens differ.
 */
async function checkTone(page) {
  return page.evaluate(() => {
    const problems = [];
    const cards = [...document.querySelectorAll('.stat')];
    if (cards.length === 0) return {problems: ['no stat cards rendered']};

    const colourOf = card => {
      const metric = card.querySelector('.stat__metric');
      return metric ? getComputedStyle(metric).color : null;
    };
    const toneOf = card =>
      card.classList.contains('stat--caution')
        ? 'caution'
        : card.classList.contains('stat--positive')
          ? 'positive'
          : 'neutral';

    const seen = new Map();
    for (const card of cards) {
      const colour = colourOf(card);
      if (!colour) continue;
      const tone = toneOf(card);
      if (!seen.has(tone)) seen.set(tone, colour);
      if (seen.get(tone) !== colour) {
        problems.push(`two ${tone} figures render in different colours`);
      }
    }

    // The three tones must be visually distinct wherever two of them meet.
    const distinct = new Set(seen.values());
    if (distinct.size !== seen.size) {
      problems.push(`tones share a colour: ${[...seen].map(([t, c]) => `${t}=${c}`).join(', ')}`);
    }

    // And the tone has to be readable without colour at all.
    for (const card of cards) {
      if (!card.querySelector('.stat__mark')) problems.push('a stat card has no tone mark');
      const label = card.querySelector('.stat__tone-label');
      if (!label || !label.textContent.trim()) {
        problems.push('a stat card has no tone label for assistive tech');
      }
    }

    return {problems};
  });
}

/**
 * Checks the what-if surface.
 *
 * Its figures are the only ones on screen the backend never rendered: the
 * sliders write into the data model and the renderer recomputes every value
 * from a chain of catalog functions. A missing function, a stale coefficient
 * or a wrong locale shows up here as a blank, a NaN or a dollar sign — none of
 * which any server-side test can see.
 */
async function checkWhatIf(page) {
  const surface = page.locator('[data-surface-id="stellschrauben"]');
  if ((await surface.count()) === 0) return {problems: ['no what-if surface rendered']};

  const problems = [];
  const readValues = () =>
    surface
      .locator('.stat__metric')
      .evaluateAll(nodes => nodes.map(n => n.firstChild?.textContent.trim() ?? ''));

  const before = await readValues();
  if (before.length < 3) problems.push(`only ${before.length} live figures`);
  for (const value of before) {
    if (!value) problems.push('a live figure rendered empty');
    else if (/NaN|Infinity|undefined/.test(value)) problems.push(`live figure reads "${value}"`);
    // German formatting: 1.234 € or 25.950, never $1,234.00.
    else if (/[$£]|\d,\d{3}/.test(value)) problems.push(`live figure is not German: "${value}"`);
  }

  // Drag the first slider to its maximum and watch the figures follow, with no
  // round trip to an agent — the whole point of the surface.
  const slider = surface.locator("input[type='range']").first();
  await slider.evaluate(input => {
    // React tracks the last value it wrote and swallows an event that does not
    // differ from it, so the assignment has to go through the native setter.
    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
    setter.call(input, input.max);
    input.dispatchEvent(new Event('input', {bubbles: true}));
  });
  await page.waitForTimeout(200);

  // A range input steps in ones, so a fractional start would leave the thumb
  // half a step from the figures it is supposed to explain.
  const offGrid = await surface
    .locator("input[type='range']")
    .evaluateAll(inputs => inputs.filter(i => !Number.isInteger(Number(i.value))).length);
  if (offGrid) problems.push(`${offGrid} slider(s) sit between steps`);

  const after = await readValues();
  if (JSON.stringify(before) === JSON.stringify(after)) {
    problems.push('dragging a slider changed nothing');
  }

  return {problems};
}
