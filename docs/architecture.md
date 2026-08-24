# Architecture notes

Detail that does not belong in the README: why the pieces are shaped the way
they are, and what would have to change to take this past a demo.

## Standing on Google's pieces

Three decisions define the shape of this codebase, and all three are about
using something official rather than building it:

1. **ADK owns the runtime.** `Runner.run_live()` handles the Live API
   connection, the session store, tool dispatch and the event stream. The
   hand-rolled equivalent it replaced was ~350 lines of queue pumping and
   response demultiplexing that had to track the SDK.
2. **The A2UI renderer is Google's.** `@a2ui/react` v0.9, unmodified, including
   its Markdown pipeline and its Generic Binder.
3. **The catalog is Google's, plus two.** Everything the agent composes with
   comes from the official basic catalog, except a chart and a comparison
   table, which have no official equivalent.

What is left is the part that is actually this demo: the German advisory
domain, the conversation design, and the composers that turn one into the
other.

### Why tools push UI through `UiWidget`

An ADK tool returns a value to the model. Getting a *second* payload to the
browser needs a channel, and there were three candidates: session state deltas,
smuggling the payload through the tool's return value, or ADK's UI-widget
channel.

`ToolContext.render_ui_widget` is the right one. It exists for exactly this —
its `provider` field is documented as the dispatch key for rendering
strategies, with `mcp` as the first one — so `provider="a2ui"` is an intended
extension rather than a workaround. The payload travels on the same event as
the tool call, ordering with the audio is preserved, and it never enters the
model's context, so a 3 kB surface costs no tokens.

The state-delta route would also work but conflates "what the session knows"
with "what the screen shows", and the return-value route would put the whole
component tree into the model's context on every call.

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

So `frontend/src/a2ui/catalog.ts` registers one catalog containing the basic
catalog's 18 components plus our two, under
`urn:a2ui:catalog:adaptive-advisory:1.0`. The basic catalog stays registered
under its own id as well, so a surface created against the standard id still
renders.

The id is duplicated in two places by necessity — `protocol.ADVISORY_CATALOG_ID`
and `catalog.ts` — and a mismatch is a blank surface, so both carry a comment
pointing at the other.

### Only two custom components

The first version of this demo had ten. Collapsing them to two was not
minimalism for its own sake — it changed what has to be maintained.

A `Card` containing a heading, a big number and a paragraph does not need to be
a component; it needs a *function that composes those three*. That is what
`SurfaceBuilder.stat_card()` is: server-side, no renderer contract, no schema,
no CSS. The same applies to headers, timelines, ranked lists and calls to
action. What survived is the two things the basic catalog genuinely cannot
express — a chart and a table.

The cost is real and worth naming: the tone of an insight is now a leading
glyph (`✓ → !`) rather than a coloured stripe, because the basic catalog has no
tone affordance to theme. That is the price of the agent composing from
approved primitives instead of from bespoke widgets.

### Semantic tools instead of generated UI

The obvious way to wire an LLM to A2UI is to let it emit A2UI JSON directly.
This demo does not, for three reasons.

**Latency.** A live voice conversation cannot wait for a few hundred tokens of
UI JSON between the client finishing a sentence and the agent responding.
A tool call with six arguments is an order of magnitude cheaper, and the
surface is composed in microseconds. (The Flutter reference this demo borrows
from, `VGVentures/genui_life_goal_simulator`, takes the other route — the model
generates the widget tree — which works well for a turn-based chat and would
be felt immediately in a voice session.)

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

One `AdvisorySession` per WebSocket, wrapping an ADK `InMemoryRunner` and a
`LiveRequestQueue`. The conversation state — the profile built up over the
call, the chosen scenario, the set of surfaces already on screen — lives in
ADK's session state, written by tools through `tool_context.state` and read
back on the next call.

That last one is what makes a refinement feel right. The first call to a tool
sends `createSurface` + `updateDataModel` + `updateComponents`; every later call
to the same tool sends only the two updates, so the card the client is already
reading changes in place instead of a near-duplicate appearing below it.

The profile surface lives in its own column beside the conversation and is
updated on every turn; everything else stacks in the stage in creation order.
That split is the point: the profile is context — what the agent currently
believes about the client — while the stage is the conversation, and the
screen grows with it rather than presenting a dashboard up front.

There is no transcript. A live voice API answers by speaking, and the column
it used to occupy is worth more to the advice than to a reading-along panel.
The backend still transcribes both sides for the handover payload and the
logs; the client simply renders none of it.

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

## Theming the official components

The basic catalog's components carry their own inline styles, built from
`--a2ui-*` custom properties: `--a2ui-card-padding`, `--a2ui-column-gap`,
`--a2ui-modal-padding`, `--a2ui-text-caption-color` and so on. Those are the
supported way to restyle them — a stylesheet rule targeting `.a2ui-card` loses
to the inline `var()` it reads.

`theme.css` maps the whole set onto this demo's tokens once, and a context like
the profile column narrows them locally:

```css
.aside {
  --a2ui-card-padding: 0;
  --a2ui-card-border: none;
  --a2ui-card-background: transparent;
}
```

The exceptions are `Button`, `TextField` and `ChoicePicker`, which expose no
variables and ship without their class names (see the packaging note in the
README). Those are styled by element, in one marked section of `blocks.css`.

## Guardrails

| Concern | Where it is enforced |
|---|---|
| Only approved components render | Renderer catalog whitelist; unknown types render as an explicit error |
| Agent text cannot inject markup | The official Markdown renderer sanitises with DOMPurify |
| No invented numbers | Every figure comes from `app/domain/*`; the prompt forbids the model from stating others |
| Malformed UI never reaches the browser | `protocol.validate_tree` runs before every emit; a bad tree is logged and dropped, the conversation continues |
| A failing tool does not end the call | ADK returns the error to the model as the function response, and the agent speaks on |
| A dying session is never silent | `_drain_session` reports an unexpected end to the browser |
| Assumptions are visible | `AssumptionNote` on every surface carrying a number |
| No personal data | The prompts do not ask for it; nothing is persisted |

## What a production version would change

**State.** `InMemoryRunner` keeps sessions in-process, which is why the
deployment uses session affinity and why a restart ends open conversations.
Swapping in ADK's `DatabaseSessionService` or `VertexAiSessionService` is a
constructor change; the Live API's session resumption is already requested in
`RunConfig`.

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
