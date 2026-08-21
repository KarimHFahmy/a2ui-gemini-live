# Architecture notes

Detail that does not belong in the README: why the pieces are shaped the way
they are, and what would have to change to take this past a demo.

## The A2UI decision

### Targeting v0.9, not v1.0

The A2UI specification has three live versions. v0.9.1 is the current
production release, v1.0 is a release candidate, v0.8 is legacy. The published
renderers — `@a2ui/react@0.10.2`, `@a2ui/web_core@0.10.6` — export `v0_8` and
`v0_9` only.

Using the official renderer matters more here than using the newest
specification. A hand-written renderer would have meant reimplementing data
binding, the function catalog, checks, action dispatch and incremental
component updates, and then maintaining that against a moving spec. So the
backend speaks v0.9.1 and the frontend runs `@a2ui/react/v0_9` unmodified.

What v1.0 would add, when the renderers catch up:

- **Inline UI on `createSurface`** — components and data model in the first
  message, saving two round trips per surface.
- **Per-component `catalogId`** — genuinely mixable catalogs, removing the
  superset workaround below.
- **Typed bidirectional function calls** — `callRendererFunction` would let the
  agent ask the browser for something (screen size, locale, a local
  calculation) instead of inferring it.

### The superset catalog

In v0.9 the renderer resolves a component against `surface.catalog` — the
catalog named in `createSurface`. There is no per-component override. Emitting
`{"component": "Column", "catalogId": "<basic>"}` on a surface created with the
advisory catalog therefore renders "Unknown component: Column".

So `frontend/src/a2ui/catalog.ts` registers one catalog that contains the basic
catalog's 18 components plus the 10 advisory blocks, under
`urn:a2ui:catalog:adaptive-advisory:1.0`. The basic catalog stays registered
under its own id as well, so a surface created against the standard id still
renders.

The id is duplicated in two places by necessity — `protocol.ADVISORY_CATALOG_ID`
and `catalog.ts` — and a mismatch is a blank surface, so both carry a comment
pointing at the other.

### Semantic tools instead of generated UI

The obvious way to wire an LLM to A2UI is to let it emit A2UI JSON directly.
This demo does not, for three reasons.

**Latency.** A live voice conversation cannot wait for a few hundred tokens of
UI JSON between the client finishing a sentence and the agent responding.
A tool call with six arguments is an order of magnitude cheaper, and the
surface is composed in microseconds.

**Correctness.** The numbers in this demo have relationships — a heat pump's
seasonal performance factor follows from the flow temperature, which follows
from the radiator type; total cost of ownership has to add up to the sum of its
parts. A model asked to produce both the layout and the arithmetic will
eventually produce a chart whose bars do not match its own caption.

**Control.** "Freigegebene UI-Komponenten, Regeln und Guardrails" is a
requirement, not a nice-to-have. When the composer is the only thing that
writes a surface, the visual quality and the factual content are both bounded
by code review rather than by prompt engineering.

The cost is expressiveness: the agent can only show what a composer knows how
to build. For a demo with two well-understood journeys that is the right trade.
A general assistant would want the opposite.

## Session model

One `AdvisorySession` per WebSocket, holding:

- the Live API connection,
- the journey's state dataclass (the profile built up over the conversation),
- the set of surface ids already on screen.

That last one is what makes a refinement feel right. The first call to a tool
sends `createSurface` + `updateDataModel` + `updateComponents`; every later call
to the same tool sends only the two updates, so the card the client is already
reading changes in place instead of a near-duplicate appearing below it.

The profile surface is pinned at the top of the stage and updated on every
turn; everything else stacks in creation order. That is the briefing's
progressive disclosure: the screen grows with the conversation rather than
presenting a dashboard up front.

### Interactions are conversational turns

A click on a scenario card does two things. The renderer's two-way binding
writes the selection into the data model, so the comparison table below
re-highlights immediately with no server involved. Separately, the action is
forwarded to the agent as a text turn ("Die Person hat 'szenario_gewaehlt'
ausgelöst"), and the agent reacts in speech.

Splitting those is deliberate: the UI responds at click speed, the voice
responds at conversation speed, and neither blocks the other.

## Audio

The Live API's contract is fixed: 16 kHz PCM16 little-endian in, 24 kHz PCM16
out. Browsers give Float32 at whatever the device runs.

- **Capture** — an `AudioWorklet` buffers 2048 samples (~128 ms at 16 kHz once
  downsampled), the main thread averages down to 16 kHz and converts to Int16.
  The worklet source is inlined as a blob so the build stays one bundle and
  there is no extra request to fail on a cold start.
- **Playback** — incoming chunks are scheduled back to back on an
  `AudioContext` timeline with an 80 ms lead, which is what keeps speech gapless
  when frames arrive unevenly.
- **Barge-in** — on `interrupted`, every scheduled buffer is stopped and the
  timeline reset. Without this the agent keeps talking over the client for as
  long as the buffer runs, which is the single most unnatural thing a voice
  demo can do.

Audio travels as binary WebSocket frames and everything else as JSON text
frames on the same socket, so ordering between "the agent said this" and "the
agent showed this" is preserved by the transport.

## Guardrails

| Concern | Where it is enforced |
|---|---|
| Only approved components render | Renderer catalog whitelist; unknown types render as an explicit error |
| No invented numbers | Every figure comes from `app/domain/*`; the prompt forbids the model from stating others |
| Malformed UI never reaches the browser | `protocol.validate_tree` runs before every emit; a bad tree is logged and dropped, the conversation continues |
| A failing tool does not end the call | `_handle_tool_call` catches, returns an error to the model, and the agent speaks on |
| A dying session is never silent | `_drain_session` reports an unexpected end to the browser |
| Assumptions are visible | `AssumptionNote` on every surface carrying a number |
| No personal data | The prompts do not ask for it; nothing is persisted |

## What a production version would change

**State.** Session state is in-process, which is why the deployment uses
session affinity and why a restart ends open conversations. Redis or Firestore
keyed by session id, plus the Live API's own session resumption, would fix
both.

**Data.** `demo_data.py` would become a service call — real tariffs, real
funding rules with their validity windows, a real vehicle catalog — and the
`AssumptionNote` would carry the actual source and retrieval time it already
has a slot for.

**Handover.** `naechsten_schritt_anbieten` produces a structured summary and
emits it to the browser. In production that is the payload that goes to CRM,
so the sales conversation starts from what the client already explained rather
than from a form.

**Observability.** Tool calls are logged; a real deployment wants traces per
session, tool latency, and the transcripts opted into for quality review.

**Compliance.** DSGVO consent for the recording, a documented retention story,
and the "Beratung und verbindliches Angebot klar trennen" boundary enforced in
the handover payload as well as in the copy.
