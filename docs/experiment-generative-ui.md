# Experiment: the model writes the A2UI itself

`docs/architecture.md` makes an argument — *semantic tools instead of generated
UI*. The model decides **when** a view is due; deterministic composers decide
**what** it looks like. That is a design choice, and a design choice you never
test against the alternative is just a preference.

So this branch builds the alternative and puts it on the same landing page.
Both advisories appear a second time, marked *frei generiert*. Same renderer,
same transport, same audio, same arithmetic. The only variable is who composes
the tree.

Run it, then run the composed one, and compare.

---

## What changed, exactly

`backend/app/journeys/generative.py`. Nine composer tools become three:

| Tool | Does |
|---|---|
| `profil_merken` | remember what was understood, as free-form JSON |
| `daten_abrufen` | return the computed figures for one area |
| `oberflaeche_zeigen` | take an A2UI component tree and show it |

Nothing else in the stack knows the difference. `oberflaeche_zeigen` parses the
model's JSON, runs it through the same `protocol.validate_tree` every composed
surface goes through, and pushes it down the same WebSocket.

**The figures are still ours.** `daten_abrufen` returns the output of
`app.domain`, unchanged. A version where the model invents the numbers too
would be a strawman — it would fail for reasons nobody disputes. This is the
strongest form of the generative case: real figures, free layout. It is the
only version worth arguing with.

---

## The part that is already measurable

Two things can be counted without ever starting the model, and they are the
first half of the finding.

### The prompt roughly doubles

| Journey | Instruction | Tools |
|---|---|---|
| `energie` | 5.063 chars | 9 |
| `mobilitaet` | 5.117 chars | 9 |
| `energie_frei` | **7.810 chars** | 3 |
| `mobilitaet_frei` | **7.698 chars** | 3 |

The catalog reference alone — the component list, the flat-adjacency rules, the
binding syntax, the house rules about tone and captions — is about 4.100 chars
that has to be in context for every turn of every conversation, including the
turns that are pure listening.

That is the trade in one line: **the composers' knowledge does not disappear
when you delete them, it moves into the prompt** — where it is re-read on every
turn, costs tokens, and is followed approximately rather than exactly.

### Each screen is ~2.900 characters of JSON

From the captured composed streams (`frontend/fixtures.json`):

| | Surfaces | Components | A2UI |
|---|---|---|---|
| Mein Zuhause | 8 | 169 | 23.065 chars |
| Meine Mobilität | 8 | 169 | 23.585 chars |

Median: **~21 components, ~2.900 characters per surface.** In the composed
journeys the model produces a tool name and at most one argument
(`szenario="waermepumpe"`), and the composer produces the rest. Here the model
has to *emit* all of it — as output tokens, in a native-audio session, while
the person waits.

Whether that shows up as a pause is the thing to watch.

---

## What to look for when you run it

The server logs a line per attempt, which is where the rest of the finding is:

```
genui eignung            18 components    2340 chars     0.4 ms
genui kosten             REJECTED after  1870 chars: dangling child 'k3'
```

`generative.metrics(state)` returns the same as a tally: `versuche`,
`angezeigt`, `abgelehnt`, `zeichen_gesamt`, `komponenten_gesamt`, `gruende`.

Five questions, in the order they matter:

1. **Latency.** How long between the model finishing a sentence and the surface
   landing? The composed version is one short tool call. This one is a few
   thousand characters of JSON. If the gap is audible, that is the answer, and
   nothing further down matters much.
2. **Rejection rate.** How often does `oberflaeche_zeigen` come back as a
   correction — and does the model recover on the retry, or on the third try,
   or does it talk its way out of showing anything? A rejection is a full
   re-emit; two of them is a long silence.
3. **Consistency.** Run the same journey twice with the same answers. The
   composed version is identical by construction. Is this one? Two clients
   being shown materially different advice for the same house is a product
   problem before it is a design one.
4. **Whether the house style survives.** The catalog *asks* for a caption over
   every heading, figures in `StatCard` rather than prose, an assumptions modal
   at the foot, and — the one that matters — `tone: caution` on a number that
   means *this costs you more*. Which of those hold up under pressure, and
   which quietly stop happening around the fourth surface?
5. **What it does that a composer would not.** This is the honest reason to
   run the experiment. A composer can only emit the views someone wrote. If the
   model builds something genuinely apt for a question nobody anticipated,
   that is a real argument for the approach and it should be recorded here.

---

## Confounds already removed

Two things would have made the experiment look worse for reasons that have
nothing to do with generated UI, so they are handled in the prompt:

- **The context column** is fed by a surface with the id `profil`. Composers
  push it on every profile change; here nothing would, so the sidebar would sit
  empty all run. The catalog now explains the id and asks for it.
- **The progress rail** marks a step done when a surface with that id arrives.
  The model picks its own ids, so the rail would never advance. The arc's ids
  are now named in the prompt.

`backend/tests/test_generative.py` holds both couplings: if the prompt stops
naming those ids, the tests fail rather than the next demo quietly looking
broken.

---

## What has *not* been verified

**No model has run against this.** The sandbox this was built in has no Vertex
credentials, so everything above is either measured statically (the prompt
sizes, the JSON volume) or verified mechanically:

- a valid tree reaches the renderer,
- an invalid one — malformed JSON, no `root`, a dangling child, duplicate ids —
  is caught server-side and comes back as a correction the model can act on,
- the figures still come from `app.domain`,
- the profile stays typed: unknown fields are refused with the real field list.

That is 30 tests. None of them tell you whether Gemini can hold a 4.100-character
catalog in its head while talking, which is the actual question. Run it.

---

## If the experiment wins

It would not mean deleting the composers. The interesting outcome is a middle:
composers for the four or five views that carry the advice — where consistency,
tone and the assumptions modal are the product — and `oberflaeche_zeigen` kept
as an escape hatch for the question nobody anticipated. The catalog is already
written and the validation path already exists, so that version is a small step
from here.

## If it loses

Then `docs/architecture.md` keeps its argument, and this file is the reason it
is allowed to.
