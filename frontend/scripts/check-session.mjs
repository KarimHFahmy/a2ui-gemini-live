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

const JOURNEYS = [
  {id: 'energie', label: 'Mein Zuhause', tagline: 'Wärmepumpe, Sanierung, Förderung'},
  {id: 'mobilitaet', label: 'Meine Mobilität', tagline: 'Reichweite, Laden, Kosten'},
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
);

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
  await page.getByRole('button', {name: 'Neu starten'}).click();
  await page.getByRole('button', {name: 'Ja, neu starten'}).click();
  await page.waitForSelector('.landing', {timeout: 8000});
}

await page.goto('http://localhost:4174/', {waitUntil: 'networkidle'});

// --- First conversation ----------------------------------------------------
const opening = await startJourney('Mein Zuhause');
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

// --- Restart ---------------------------------------------------------------
await restart();
if ((await surfaceIds()).length) {
  problems.push('surfaces survived the restart into the landing page');
}

// --- Second conversation, different journey --------------------------------
await startJourney('Meine Mobilität');
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
if (/Baujahr|Wärmebedarf|Heizung heute/.test(profileText)) {
  problems.push('the previous journey’s profile is still in the context column');
}

// The progress indicator has to describe this journey, not the last one.
const progressLabels = await page.$$eval('.progress__label', nodes =>
  nodes.map(n => n.textContent.trim()),
);
if (progressLabels.includes('Eignung') || progressLabels.includes('Förderung')) {
  problems.push(`progress still shows the previous arc: ${progressLabels.join(', ')}`);
}

// --- Same journey twice, the case a shared surface id would hide ------------
await restart();
await startJourney('Meine Mobilität');
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

console.log(`sessions: ${sockets}, surfaces: ${first.length} / ${second.length} / ${third.length}`);
for (const problem of problems) console.log(`  ${problem}`);
console.log(problems.length ? `\nFAILURES: ${problems.length}` : '\nSESSION CHECKS PASSED');
process.exit(problems.length ? 1 : 0);
