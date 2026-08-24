# Adaptive Advisory Experiences

Two voice-led advisory demos for the German market — **Energieberater** and
**Autoberater** — built on **Google's Agent Development Kit (ADK)**, the
**Gemini Live API over Vertex AI**, and **[A2UI](https://github.com/a2ui-project/a2ui)**.
The client talks; the agent listens, understands, and builds the advisory
interface in real time.

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
Browser                        Cloud Run (one container)                Google Cloud
┌────────────────────┐       ┌──────────────────────────────┐        ┌──────────────┐
│ React SPA          │ audio │ FastAPI  /ws                 │  audio │ Vertex AI    │
│ AudioWorklet ──────┼──────>│   └ AdvisorySession          ├───────>│ Gemini Live  │
│ 16 kHz PCM16       │ (bin) │       └ ADK Runner.run_live  │ (WSS)  │ native audio │
│                    │<──────┼─── 24 kHz PCM16              │<───────┤ de-DE        │
│                    │       │            │                 │  tool  │              │
│ @a2ui/react v0_9   │<──────┼─── A2UI envelopes            │  call  └──────────────┘
│  Adaptive Advisory │(text) │            ▲                 │
│  catalog:          │       │      UiWidget(provider=a2ui) │
│   basic catalog    │       │            │                 │
│   + chart, table   │       │   ADK FunctionTool           │
│                    │──────>│      └ Domain calc (no LLM)  │
│ profile + dock     │action │      └ Composer → A2UI       │
└────────────────────┘       └──────────────────────────────┘
```

### ADK does the plumbing

`Runner.run_live()` owns the Live API connection, the session store, tool
dispatch and the event stream. The application code left over is the
translation between ADK events and what a browser needs — audio frames,
transcripts, and the A2UI stream.

Tools are plain Python functions. ADK derives each declaration the model sees
from the signature and docstring, so the contract and the implementation cannot
drift apart:

```python
def waermepumpen_eignung_zeigen(tool_context: ToolContext) -> dict[str, Any]:
    """Zeigt, ob das Haus für eine Wärmepumpe geeignet ist. …"""
    profil = _profil(tool_context)
    push(tool_context, compose.eignung_surface(profil))   # → the browser
    return {"urteil": calc.eignung(profil)["urteil"], ...}  # → the model
```

`push()` uses ADK's own generative-UI channel: `tool_context.render_ui_widget`
attaches a `UiWidget(provider="a2ui", …)` to the event the tool produces, and
the WebSocket layer forwards widgets with that provider. `provider` exists for
exactly this — pluggable rendering strategies — so no side channel is needed.

**The model never emits UI JSON.** It calls semantic tools and the backend
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
and uses the official React renderer unmodified — including its Markdown
pipeline (`@a2ui/markdown-it`, markdown-it + DOMPurify), which is what keeps
agent-authored text from becoming an XSS vector.

v0.9 also resolves every component against the *surface's* catalog — there is
no per-component `catalogId` override yet. So the Adaptive Advisory catalog is
registered as a superset: the basic catalog's components and functions plus our
two additions, under one id (`urn:a2ui:catalog:adaptive-advisory:1.0`, shared
by `backend/app/a2ui/protocol.py` and `frontend/src/a2ui/catalog.ts`).

### The catalog is Google's, plus two

Almost everything on screen is rendered by `@a2ui/react`'s own basic catalog,
themed entirely through its `--a2ui-*` custom properties — no component
overrides:

| Baustein | Rendered with |
|---|---|
| Section headers | `Text` variants `caption` + `h2` |
| Karten mit Leitkennzahl | `Card` › `Column` › `Text` (`h4`, `h1`, `body`) |
| Fakten, Timeline, Empfehlungen | `List` with a `ChildList` **template** over the data model |
| Szenarioauswahl | `ChoicePicker`, `displayStyle: chips` |
| Call-to-action | `Button` with an agent event |
| Annahmen & Datenquellen | `Modal` (trigger + content) |
| Aufzählungen, Hervorhebung | `Text` with Markdown |
| **Diagramm** | `MetricChart` — ours; no official equivalent |
| **Vergleichstabelle** | `ComparisonTable` — ours; no official equivalent |

Two things are worth pointing at during a demo.

**The list template.** A timeline, a fact grid and a ranked recommendation list
are each *one* component definition plus a data array. Adding a step is an
`updateDataModel` message, not a layout change.

**The shared binding.** The `ChoicePicker` and the comparison table's
`highlight` read the same data-model path. Picking a scenario re-highlights the
table immediately — client-side, no round trip — while the Button separately
tells the agent, which reacts in speech. The UI never waits on the model.

> **Note on `@a2ui/react@0.10.2`.** The published package ships its CSS Modules
> without the class-name map, so `Button`, `TextField` and `ChoicePicker`
> render with some `undefined` classes. The elements are semantically correct,
> so `frontend/src/styles/blocks.css` styles them by element — one clearly
> marked section that can be deleted once the package emits its own names.

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
    session.py            ADK Runner.run_live → browser: audio, transcripts, A2UI
    config.py             Environment configuration (also configures ADK)
    a2ui/
      protocol.py         A2UI v0.9 envelopes + tree validation
      builder.py          SurfaceBuilder over the official basic catalog
      surface.py          One composed surface, create-or-update aware
      composer_*.py       Domain results -> advisory surfaces
    journeys/
      base.py             Journey + the UiWidget push, shared prompt fragments
      energie.py          Energieberater: ADK tools, instruction, handover
      mobilitaet.py       Autoberater: ADK tools, instruction, handover
    domain/
      demo_data.py        German market demo values (single source of numbers)
      energie.py          Wärmebedarf, JAZ, Szenarien, Förderung, Amortisation
      mobilitaet.py       Reichweite, Ladeoptionen, TCO, Fahrzeugpassung
  scripts/generate_fixtures.py
  tests/                  98 tests: protocol, domain, tool contracts, session

frontend/
  src/
    a2ui/
      A2uiHost.tsx        Provides the official Markdown renderer
      catalog.ts          Catalog registration (basic catalog + our two)
      schemas.ts          Zod component APIs for MetricChart, ComparisonTable
      components/         Their implementations + the inline SVG chart
    live/
      audio.ts            Capture (16 kHz) and playback (24 kHz) with barge-in
      session.ts          WebSocket client
    ui/                   Landing, Stage, ProfileAside, VoiceDock
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
  the tool contracts: ADK can build a declaration for every tool, every
  parameter is documented, every tool renders from its required arguments
  alone, the profile survives across calls, and every data binding resolves
  against the data model it ships with. The ADK event translation is driven
  with hand-built events, so no runner or credentials are needed.
- **Frontend** (`tsc`) — typecheck.
- **Catalog check** (Playwright) — renders every captured surface in a real
  browser in light and dark mode and fails on a missing-child placeholder, an
  unknown component, an empty chart, literal Markdown on screen (the sign of a
  missing renderer) or a page that scrolls sideways.

---

## Adapting it

**Rebrand.** The accent colour, wordmark and type stack are the only things a
rebrand touches: `frontend/src/styles/theme.css` and `VITE_BRAND_NAME`. The
demo ships deliberately brand-neutral.

**Change the numbers.** Everything lives in `backend/app/domain/demo_data.py`
with a `STAND` date that is surfaced in the UI. Nothing else hardcodes a price.

**Add a surface.** Compose it in a `composer_*.py` with `SurfaceBuilder`, then
call it from a tool. Reach for a new *component* only when the basic catalog
genuinely cannot express the idea — two additions in this whole demo is the
bar. If you do: Zod API in `frontend/src/a2ui/schemas.ts`, implementation in
`components/blocks.tsx`, add it to `ADVISORY_COMPONENTS`, and a matching method
on `SurfaceBuilder`.

**Add a journey.** Copy `backend/app/journeys/energie.py`: an instruction, a
list of tool functions, and a `build()` returning a `Journey`. Register it in
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
