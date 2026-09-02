/**
 * Session lifecycle check.
 *
 * The catalog check renders surfaces; this one drives the *shell* — landing
 * page, session, restart, second session — against a stubbed WebSocket, and
 * asserts that a new conversation starts on an empty screen.
 *
 * It exists because the renderer's MessageProcessor outlives any one session.
 * Surfaces from a finished conversation stay in it unless they are explicitly
 * deleted; the renderer then rejects the next session's `createSurface` for an
 * id it already has, and the client keeps looking at the last person's advice.
 * Nothing in a static render can see that — it only appears when you restart.
 *
 *   npm run check:session
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

/*
 * The whole experience runs in either language, so the restart path is driven
 * in both: the surfaces a session leaks are the same objects either way, but
 * the *shell* is not, and a language switched between two sessions is one more
 * way for the last conversation to stay on screen.
 */
const LOCALE = process.env.CHECK_LOCALE ?? 'de';

const LABELS = {
  de: {energie: 'Mein Zuhause', mobilitaet: 'Meine Mobilität', restart: 'Neu starten',
       confirm: 'Ja, neu starten'},
  en: {energie: 'My Home', mobilitaet: 'My Mobility', restart: 'Start over',
       confirm: 'Yes, start over'},
}[LOCALE];

const JOURNEYS = [
  {id: 'energie', label: LABELS.energie, tagline: '—'},
  {id: 'mobilitaet', label: LABELS.mobilitaet, tagline: '—'},
];

/*
 * How long the stub waits between the session frame and the first surface.
 * Long enough to look at the empty screen, which is the only moment the
 * topics are on it — and the moment a first-time client decides whether they
 * know what to say.
 */
const OPENING_PAUSE = 250;

const fixtures = JSON.parse(
  fs.readFileSync(path.resolve(import.meta.dirname, '../fixtures.json'), 'utf8'),
)[LOCALE];

const server = http.createServer((req, res) => {
  const url = req.url.split('?')[0];
  if (url === '/api/journeys') {
    res.writeHead(200, {'Content-Type': 'application/json'});
    return res.end(JSON.stringify({journeys: JOURNEYS}));
  }
  const file = path.join(ROOT, url === '/' ? 'index.html' : url);
  if (!fs.existsSync(file) || fs.statSync(file).isDirectory()) {
    res.writeHead(404);
    return res.end('nf');
  }
  res.writeHead(200, {'Content-Type': MIME[path.extname(file)] ?? 'application/octet-stream'});
  fs.createReadStream(file).pipe(res);
});
await new Promise(r => server.listen(4174, r));

const preinstalled = process.env.CHROMIUM_PATH ?? '/opt/pw-browsers/chromium';
const browser = await chromium.launch(
  fs.existsSync(preinstalled) ? {executablePath: preinstalled} : {},
);
const context = await browser.newContext({viewport: {width: 1440, height: 900}});
const page = await context.newPage();

const problems = [];
page.on('pageerror', e => problems.push(`page error: ${String(e).slice(0, 200)}`));
page.on('console', m => {
  const t = m.text();
  if (m.type() === 'error' && !/ERR_CONNECTION_RESET|ERR_FAILED|fonts\./.test(t)) {
    problems.push(`console: ${t.slice(0, 200)}`);
  }
});
await page.route('**fonts.googleapis.com**', r => r.abort());
await page.route('**fonts.gstatic.com**', r => r.abort());

/*
 * Stand in for the backend. Each connect replays that journey's captured A2UI
 * stream, which is what a real session does — so the surfaces on screen are the
 * real ones, and only the transport is fake.
 */
await page.addInitScript(
  ({fixtures: captured, pause}) => {
    navigator.mediaDevices.getUserMedia = () => Promise.reject(new Error('no mic in this check'));
    window.__sockets = 0;
    class FakeSocket {
      constructor(url) {
        this.readyState = 1;
        this.binaryType = 'arraybuffer';
        window.__sockets += 1;
        const id = new URL(url.replace(/^ws/, 'http')).searchParams.get('journey');
        const send = payload => this.onmessage?.({data: JSON.stringify(payload)});
        setTimeout(() => {
          this.onopen?.();
          send({
            type: 'session',
            journey: {
              id,
              label: id,
              steps: captured[id].steps,
              topics: captured[id].topics,
            },
          });
        }, 20);
        setTimeout(() => {
          for (const message of captured[id].messages) send({type: 'a2ui', payload: message});
        }, 20 + pause);
      }
      send() {}
      close() {
        this.readyState = 3;
        this.onclose?.();
      }
    }
    window.WebSocket = FakeSocket;
  },
  {fixtures, pause: OPENING_PAUSE},
);

const surfaceIds = () =>
  page.$$eval('[data-surface-id]', nodes => nodes.map(n => n.dataset.surfaceId).sort());

async function startJourney(label) {
  await page.getByRole('button', {name: new RegExp(label)}).click();
  await page.waitForSelector('.session__bar', {timeout: 8000});

  // The empty screen, before any surface lands: the only place the topics
  // appear, and the moment someone decides whether they know what to say.
  const opening = await page.$$eval('.stage__topics li', nodes =>
    nodes.map(n => n.textContent.trim()),
  );

  await page.waitForFunction(() => document.querySelectorAll('[data-surface-id]').length > 0, {
    timeout: 8000,
  });
  await page.waitForTimeout(300);
  return opening;
}

async function restart() {
  await page.getByRole('button', {name: LABELS.restart}).click();
  await page.getByRole('button', {name: LABELS.confirm}).click();
  await page.waitForSelector('.landing', {timeout: 8000});
}

await page.goto(`http://localhost:4174/?lang=${LOCALE}`, {waitUntil: 'networkidle'});

// --- First conversation ----------------------------------------------------
const opening = await startJourney(LABELS.energie);
const first = await surfaceIds();

// The agent says what it can help with; the empty screen has to say the same,
// because three topics heard once are hard to hold on to.
if (opening.length === 0) {
  problems.push('the empty screen offered no topics, so nobody knows what to say');
} else if (JSON.stringify(opening) !== JSON.stringify(fixtures.energie.topics)) {
  problems.push(`the screen and the greeting disagree: ${opening.join(' | ')}`);
}
if (first.length === 0) problems.push('the first session rendered no surfaces at all');
if (!first.includes('eignung')) {
  problems.push(`the first session is missing its own surfaces: ${first.join(', ')}`);
}

// --- The advice is reachable without a mouse -------------------------------
// The stage sits behind a header of controls, so the first thing a keyboard
// reaches in a session has to be the way past them.
//
// Asserted on the DOM and on the link's own behaviour rather than by pressing
// Tab: Chromium keeps a "sequential focus navigation starting point" from the
// last click, so a synthetic Tab here starts from the middle of the page and
// measures the test's setup instead of the page.
const skip = await page.evaluate(() => {
  const link = document.querySelector('.skip-link');
  if (!link) return {present: false};

  const tabbable = document.querySelectorAll('a[href], button, [tabindex]');
  const hiddenBox = link.getBoundingClientRect();
  link.focus();
  const focusedBox = link.getBoundingClientRect();

  return {
    present: true,
    first: tabbable[0] === link,
    // A skip link that stays clipped while focused is one nobody can use.
    revealed: focusedBox.width > hiddenBox.width || getComputedStyle(link).clipPath === 'none',
    target: link.getAttribute('href'),
  };
});

if (!skip.present) {
  problems.push('a session has no skip link past the header to the advice');
} else {
  if (!skip.first) problems.push('the skip link is not the first thing a keyboard reaches');
  if (!skip.revealed) problems.push('the skip link stays hidden while focused');

  await page.keyboard.press('Enter');
  await page.waitForTimeout(150);
  const landed = await page.evaluate(() => document.activeElement?.id);
  if (landed !== 'stage') {
    problems.push(`the skip link left focus on ${landed || 'nothing'}, not the stage`);
  }
}

// --- Restart ---------------------------------------------------------------
await restart();
if ((await surfaceIds()).length) {
  problems.push('surfaces survived the restart into the landing page');
}

// --- Second conversation, different journey --------------------------------
await startJourney(LABELS.mobilitaet);
const second = await surfaceIds();

// `eignung` belongs to the energy journey and `alltag` to the mobility one, so
// either name appearing in the wrong run is unambiguous evidence of leakage.
const leaked = second.filter(id => id === 'eignung' || id === 'foerderung');
if (leaked.length) {
  problems.push(`the previous conversation is still on screen: ${leaked.join(', ')}`);
}
if (!second.includes('alltag')) {
  problems.push(`the second session did not render its own surfaces: ${second.join(', ')}`);
}

// A leaked surface can also hide inside a *shared* id: `profil` exists in both
// journeys, so check its content rather than its presence.
const profileText = await page
  .locator('.aside')
  .innerText()
  .catch(() => '');
const energyProfileWords = LOCALE === 'de' ? /Baujahr|Wärmebedarf|Heizung heute/ : /built |Heat demand|Heating today/;
if (energyProfileWords.test(profileText)) {
  problems.push('the previous journey’s profile is still in the context column');
}

// The progress indicator has to describe this journey, not the last one.
const progressLabels = await page.$$eval('.progress__label', nodes =>
  nodes.map(n => n.textContent.trim()),
);
const energySteps = LOCALE === 'de' ? ['Eignung', 'Förderung'] : ['Suitability', 'Subsidy'];
if (energySteps.some(label => progressLabels.includes(label))) {
  problems.push(`progress still shows the previous arc: ${progressLabels.join(', ')}`);
}

// --- Same journey twice, the case a shared surface id would hide ------------
await restart();
await startJourney(LABELS.mobilitaet);
const third = await surfaceIds();
if (third.length !== second.length) {
  problems.push(
    `rerunning the same journey changed the surface count: ${second.length} then ${third.length}`,
  );
}

const sockets = await page.evaluate(() => window.__sockets);
if (sockets !== 3) problems.push(`expected 3 sessions, the shell opened ${sockets}`);

await browser.close();
server.close();

console.log(`[${LOCALE}] sessions: ${sockets}, surfaces: ${first.length} / ${second.length} / ${third.length}`);
for (const problem of problems) console.log(`  ${problem}`);
console.log(problems.length ? `\nFAILURES: ${problems.length}` : '\nSESSION CHECKS PASSED');
process.exit(problems.length ? 1 : 0);
