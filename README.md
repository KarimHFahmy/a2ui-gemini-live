# Adaptive Advisory Experiences

Two voice-led advisory demos for the German market — **Energieberater** and
**Autoberater** — built on the **Gemini Live API over Vertex AI** and
**[A2UI](https://github.com/a2ui-project/a2ui)**. The client talks; the agent
listens, understands, and builds the advisory interface in real time.

> Nicht die Kund:innen durch Komplexität navigieren lassen. Die KI baut in
> Echtzeit genau die Beratungserfahrung, die zur individuellen Frage, Situation
> und Sorge passt.

Backend (Python) and frontend (React) ship in **one container** and deploy to
**Cloud Run** as a single service.

---

## What it does

Someone says *"Unser Haus ist von 1985. Ich habe Sorge, dass eine Wärmepumpe im
Winter nicht reicht und sich die Investition nicht lohnt."*

The agent does not answer with a wall of text. It calls an advisory tool, the
backend composes an A2UI surface from deterministic calculations, and the page
grows a suitability check with the client's own numbers — flow temperature,
seasonal performance factor, the winter heat load month by month — while the
agent explains in two sentences what it means for them.

Ask about money and a twenty-year cost curve appears with the break-even
marked. Mention a worry and it gets its own card, named in the client's words
and answered point by point. Every figure carries its assumptions one click
away.

### Two journeys, one core

| | **Mein Zuhause** | **Meine Mobilität** |
|---|---|---|
| Frame | Wärmepumpe, Sanierung, Förderung | Reichweite, Laden, Fahrzeugwahl, Kosten |
| Opening worry | „Reicht das im Winter?" | „Ist das praktikabel ohne Wallbox?" |
| Decisive insight | Vorlauftemperatur, nicht Außentemperatur | Der Ladeort, nicht das Modell |
| Closes with | Förderfahrplan + Vor-Ort-Check | Ladecheck + Probefahrt |

---

## Architecture

```
Browser                          Cloud Run (one container)              Google Cloud
┌──────────────────────┐         ┌───────────────────────────┐          ┌──────────────┐
│ React SPA            │         │ FastAPI                   │          │ Vertex AI    │
│                      │  audio  │                           │  audio   │              │
│ AudioWorklet ────────┼────────>│ AdvisorySession ──────────┼─────────>│ Gemini Live  │
│ 16 kHz PCM16         │  (bin)  │                           │  (WSS)   │ native audio │
│                      │<────────┼── 24 kHz PCM16            │<─────────┤ de-DE        │
│                      │         │                           │ tool call│              │
│ @a2ui/react v0_9     │<────────┼── A2UI envelopes (JSON)   │          └──────────────┘
│  ├ basic catalog     │  (text) │      ▲                    │
│  └ advisory blocks   │         │      │ composes           │
│                      │────────>│  Journey ──> Domain calc  │
│ transcript + dock    │ actions │  (tools)     (no LLM)     │
└──────────────────────┘         └───────────────────────────┘
```

**The model never emits UI JSON.** It calls semantic tools —
`waermepumpen_eignung_zeigen`, `ladeloesungen_vergleichen` — and the backend
composes the surface from deterministic domain calculations. That is the
guardrail the briefing asks for:

- **A fixed catalogue of approved components.** The renderer whitelists them;
  anything else renders as "unknown component" rather than executing.
- **No invented numbers.** Every figure comes back from a tool. The system
  prompt says so, and the composers are the only thing that writes them.
- **Visible assumptions.** Each surface that shows a number carries an
  `AssumptionNote` with the inputs, the price path and the as-of date.

### Why A2UI v0.9

The official renderers (`@a2ui/react`, `@a2ui/web_core`) ship **v0.8 and
v0.9**; v1.0 is still a candidate specification. This demo targets **v0.9.1**
and uses the official React renderer rather than a hand-written one.

v0.9 also resolves every component against the *surface's* catalog — there is
no per-component `catalogId` override yet. So the Adaptive Advisory catalog is
a superset: the basic catalog's components and functions plus our advisory
blocks, registered under one id
(`urn:a2ui:catalog:adaptive-advisory:1.0`, shared by
`backend/app/a2ui/protocol.py` and `frontend/src/a2ui/catalog.ts`).

### The advisory catalog

Ten building blocks, matching the briefing's "6–8 UI-Bausteine":

| Component | Rolle |
|---|---|
| `AdvisoryHeader` | Rahmt, was gerade gezeigt wird |
| `ProfileSummary` | „Zusammenfassung des Verstandenen", mit Schätzmarkierung |
| `InsightCard` | Eine Aussage, optional mit Leitkennzahl |
| `ComparisonTable` | Optionen als Spalten, Kriterien als Zeilen |
| `ScenarioSelector` | Auswählbare Szenarien (Zwei-Wege-Bindung) |
| `MetricChart` | Balken, gruppiert, gestapelt, Linie |
| `Timeline` | Reihenfolge und Dauer |
| `Recommendation` | Rangfolge mit offen gezeigten Trade-offs |
| `NextStepCTA` | Übergabe an Mensch oder Prozess |
| `AssumptionNote` | Annahmen und Datenquellen sichtbar machen |

`ScenarioSelector` shows off A2UI's reactive binding: picking a scenario writes
to the data model, the comparison table below re-highlights immediately, and
the action reaches the agent separately so it can react in speech. The UI never
waits on the model.

---

## Quick start

### Prerequisites

- Python 3.11+, Node 20+
- A Google Cloud project with the Vertex AI API enabled, and
  `gcloud auth application-default login`
- A microphone, and a browser on `localhost` or HTTPS (`getUserMedia` requires
  a secure context)

### Run it

```bash
cp .env.example .env          # set GOOGLE_CLOUD_PROJECT
make install
make dev                      # backend :8080, frontend :5173
```

Open <http://localhost:5173>, pick a journey, allow the microphone and start
talking.

Prefer AI Studio for a quick local run? Set `USE_VERTEX_AI=false` and
`GOOGLE_API_KEY` in `.env`.

### Look at the UI without spending a voice session

```bash
make preview                  # http://localhost:8080/preview.html
```

`preview.html` replays captured A2UI fixtures through the real renderer — every
surface of both journeys, no API key needed. Regenerate the fixtures after
changing a composer:

```bash
make fixtures
```

---

## Deploy to Cloud Run

```bash
PROJECT_ID=my-project REGION=europe-west4 ./deploy/deploy.sh
```

The script enables the APIs, creates a runtime service account with
`roles/aiplatform.user`, and deploys from source. Authentication is
Application Default Credentials throughout — **no API keys in the image or in
Secret Manager**.

Settings that matter for a live voice demo:

| Flag | Why |
|---|---|
| `--timeout 3600` | WebSockets are long-lived; the default 300 s cuts sessions off |
| `--session-affinity` | Keeps a browser pinned to the instance holding its session |
| `--min-instances 1` | A cold start is a silent pause on the first "hello" |
| `--concurrency 12` | Each session holds an open Live connection and a CPU share |
| `--cpu 2` | Audio pumping plus tool execution alongside the model stream |

Session state lives in the serving process, so a restart ends open
conversations — acceptable for a demo, and the reason for session affinity. A
production deployment would move it to Redis or Firestore.

> **Region note.** Cloud Run runs where your users are (`europe-west4` for
> Germany). Live API model availability differs, so `MODEL_LOCATION` is
> separate and defaults to `us-central1`. Check the
> [Live API docs](https://cloud.google.com/vertex-ai/generative-ai/docs/live-api)
> for current regions and model ids before a demo — both move during preview.

---

## Repository layout

```
backend/
  app/
    main.py               FastAPI: /ws, /api/journeys, /healthz, SPA hosting
    live_session.py       Gemini Live orchestration, tool execution, A2UI streaming
    config.py             Environment configuration
    a2ui/
      protocol.py         A2UI v0.9 envelopes + tree validation
      components.py       Typed builders for every allowed component
      surface.py          One composed surface, create-or-update aware
      composer_*.py       Domain results -> advisory surfaces
    journeys/
      base.py             Journey definition + shared prompt and tools
      energie.py          Energieberater: prompt, tools, handlers
      mobilitaet.py       Autoberater: prompt, tools, handlers
    domain/
      demo_data.py        German market demo values (single source of numbers)
      energie.py          Wärmebedarf, JAZ, Szenarien, Förderung, Amortisation
      mobilitaet.py       Reichweite, Ladeoptionen, TCO, Fahrzeugpassung
  scripts/generate_fixtures.py
  tests/                  59 tests: protocol, domain, journey contracts, session

frontend/
  src/
    a2ui/
      schemas.ts          Zod component APIs (the agent's contract)
      catalog.ts          Catalog registration
      components/         React implementations + inline SVG charts
    live/
      audio.ts            Capture (16 kHz) and playback (24 kHz) with barge-in
      session.ts          WebSocket client
    ui/                   Landing, Stage, TranscriptPanel, VoiceDock
    useAdvisory.ts        Ties socket, audio and MessageProcessor together
    preview/              Offline catalog preview
  scripts/check-catalog.mjs
```

---

## Tests

```bash
make test
```

- **Backend** (`pytest`) — the A2UI wire format, the advisory arithmetic, and
  the journey contracts: every declared tool has a handler, every tool produces
  a renderable tree from bare arguments, and every data binding resolves
  against the data model it ships with.
- **Frontend** (`tsc`) — typecheck.
- **Catalog check** (Playwright) — renders every captured surface in a real
  browser in light and dark mode and fails on a missing-child placeholder, an
  unknown component, an empty chart or a page that scrolls sideways.

---

## Adapting it

**Rebrand.** The accent colour, wordmark and type stack are the only things a
rebrand touches: `frontend/src/styles/theme.css` and `VITE_BRAND_NAME`. The
demo ships deliberately brand-neutral.

**Change the numbers.** Everything lives in `backend/app/domain/demo_data.py`
with a `STAND` date that is surfaced in the UI. Nothing else hardcodes a price.

**Add a building block.** Define the Zod API in `frontend/src/a2ui/schemas.ts`,
implement it in `components/blocks.tsx`, add it to `ADVISORY_COMPONENTS`, and
add a matching builder in `backend/app/a2ui/components.py`.

**Add a journey.** Copy `backend/app/journeys/energie.py`: a system
instruction, tool declarations, handlers and a state dataclass. Register it in
`journeys/__init__.py` and the landing page picks it up from `/api/journeys`.

---

## Demo data and scope

All figures are **clearly marked demo values** (`Demo-Annahmen, Stand Q3/2026`),
chosen to be plausible for the German market — heat demand by building age,
BEG funding logic, charging tariffs, TCO components. They illustrate the
experience; they are not advice and not a quote. Funding rules in particular
change often and are shown with that caveat in the UI.

The demo asks for no personal data — no name, address or contract number — and
keeps the conversation in the session. Nothing is persisted.
