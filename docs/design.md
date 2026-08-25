# Design notes

The visual direction, why it is this one, and where the boldness is spent.

Written the way the work was done: a compact token system first, criticised
against the brief before any code, then built from the revised plan.

---

## The brief, pinned

**Subject.** A voice-led advisory experience for the German energy transition —
heat pumps and renovation on one side, e-mobility on the other.

**Audience.** German homeowners and commuters, financially cautious, mildly
sceptical, being advised by a utility or a consultancy they did not choose.

**The page's one job.** Make a person trust a number they did not calculate.

Everything below follows from that last line. This is not a product that needs
to feel inspiring; it needs to feel *checked*.

---

## Where the direction came from

The subject's own world is not solar panels at sunset. It is **measurement**:
Vorlauftemperatur, Jahresarbeitszahl, kWh/m²a, Mischpreis je kWh, Zählerstände.
The artefacts a German homeowner actually meets in this decision are the
Energieausweis, the Datenblatt, the utility bill, the Rechenblatt an installer
leaves on the kitchen table.

So the direction is **Messwerte** — readings. Technical stock, print-black type,
instrument blue, figures set the way a datasheet sets them.

The default this replaces is worth naming, because it is what the first version
did: an energy brief lands on sustainability green without anyone deciding to.
`#0f9b6c` was not chosen, it was reached for.

---

## The token system

### Colour — one hue, one meaning

The real problem with the old palette was not the hue, it was the workload. A
single green was the brand, the call to action, the selected state, every
headline figure, the first chart series and the savings number. A colour that
means five things means none of them, and it is what let a figure saying "this
costs you more" render as good news.

| Token | Light | Dark | Says |
|---|---|---|---|
| `--brand-accent` | `#145a6e` | `#4bb2cd` | **you can act here** — buttons, focus, selection, and nothing else |
| `--tone-positive` | `#1a7a5e` | `#35c398` | this is in your favour |
| `--tone-caution` | `#a5620e` | `#e0a34a` | this deserves your attention |
| `--tone-neutral` | ink | ink | this is a fact — most figures |
| `--bg` | `#eef1f4` | `#0b1014` | cool technical stock, not warm paper |
| `--text` | `#131a21` | `#e4eaef` | technical print |

The chart series are deliberately **none of the above** — `#1f6a80`, `#8c6d52`,
`#5d5a8a`, `#3f7a6a`, `#9a5566`. A series is a thing being measured, not a
verdict on it. Green for "Elektro" would call the electric option the good one
even on the chart that shows it costing more.

### Type — two roles with a real job split

- **IBM Plex Sans** for prose, headings and UI.
- **IBM Plex Mono** for *measurements*: units, axis ticks, table figures, slider
  readouts, the wordmark, the counters.

Plex was drawn for an engineering company and reads instrument-grade rather than
startup-generic, which is the point. The split is not decorative: prose is
argued, readings are taken, and setting them differently is most of what makes
the advice look calculated instead of asserted.

Both faces are **self-hosted** (`frontend/public/fonts`, 116 KB, OFL). The
previous stack pulled Inter from a CDN with no local fallback, so on any network
that blocks Google Fonts — a lot of German corporate ones — the design silently
rendered in Arial and nothing said so. `check-catalog.mjs` now fails if the
faces are not actually in use, and fails if anything requests a font CDN.

### Layout

Unchanged, because it was already right: conversation left, context right, dock
pinned. The screen grows with the conversation instead of presenting a dashboard.

### Signature — the stage sits on squared paper

Two CSS gradients at 3–4 % of the ink, 24 px. Rechenpapier.

It is the cheapest possible way to say what the product is — the advice is a
worked calculation, not an opinion — and it is faint enough that you notice it
second, never first. This is the one deliberate risk.

The **what-if surface** is where that ground becomes the point. It is the only
thing in the product nobody else has: figures that recompute under the client's
hand, in the browser, with no round trip. So it is built as an instrument panel
— recessed ground, a finer 12 px rule, components flat *on* it rather than
floating above it, every live figure set in the mono as a readout, and the tone
marks suppressed because everything in it is neutral by construction.

Restraint everywhere else is what lets that land.

---

## The critique pass

Held against the brief before building, looking for anything that would come out
of any similar prompt:

**Rejected — copper as the accent.** Copper is genuinely the material of
electrification: busbars, windings, the heat exchanger, the charging cable. It is
also one letter away from the terracotta-on-cream look that every AI design
produces right now. Not worth spending the one free axis there.

**Rejected — a second green.** Swapping one green for a better green would have
left the real problem untouched: the accent was overloaded, not off-hue.

**Rejected — numbered markers on the journey steps.** `01 / 02 / 03` is the
reflex, and the advisory arc *is* ordered, so it would even be defensible. But
the progress rail already encodes order by position and completion by fill, and
a number on top of that is decoration repeating what the shape says.

**Kept and left alone — motion.** The stage already fades and lifts each surface
in over 340 ms, the mic ring tracks the live audio level, and the dock spins
while a tool runs. That is three moments, which is enough. The temptation was to
add a settle animation to the live figures; a figure that flashes every time a
slider moves would be noise on the one surface that most needs to feel
instrument-steady. Nothing added.

**One thing the palette work caught.** With tone finally visible, the energy card
was marked positive at 11,37 € against 11,39 € per 100 km, because the test was
a bare `<`. Two cents over 100 km is a tie. Colour made a claim the numbers did
not support, and it took making colour honest to see it.

---

## Where a rebrand touches

`--brand-*` and the type stack in `theme.css`, plus `VITE_BRAND_NAME`. The tone
scale and the chart series are semantic and should survive a rebrand; the
squared ground is one rule to delete if a client wants it gone.
