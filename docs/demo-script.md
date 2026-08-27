# Demo script

Two runs of roughly four minutes. Both start from the landing page.

The point to land is not that the assistant answers well. It is that the
**interface is built for this person, while they talk** — and that it says the
uncomfortable thing when the numbers call for it.

---

## Starter lines

The first thing you say. Everything else follows from it, so it is worth
picking one on purpose rather than improvising at the microphone.

The agent opens by naming the three things it can help with, and the empty
screen lists the same three — so you can also just wait, read them, and answer.
The lines below are what to say if you want to steer the run somewhere
specific.

Each line is written the way a real client opens — a situation and a worry, not
a list of parameters — and each lands somewhere different. The outcomes below
are what the domain modules actually produce, not what would be nice.

### Mein Zuhause

> „Wir haben ein Einfamilienhaus von 1985, etwa 160 Quadratmeter, vier
> Personen. Gasheizung, die langsam in die Jahre kommt."

The neutral opening. The agent has building and heating and will ask about the
radiators next — which is the question that decides the whole consultation.

> „Meine Gasheizung ist 22 Jahre alt und der Schornsteinfeger hat was gesagt.
> Ich weiß aber nicht, ob eine Wärmepumpe bei uns überhaupt funktioniert."

Starts on the worry rather than the data, so the agent has to draw the building
out of you. Good for showing that it asks one question at a time instead of
presenting a form.

> „Rechnet sich das überhaupt? Ich höre da sehr viel Widersprüchliches."

Goes at the economics first. Expect the agent to insist on the suitability
question before it will talk about money — that ordering is deliberate, and
saying so out loud lands well.

> „Altbau von 1975, 220 Quadratmeter, unsaniert, Ölheizung."

The strongest case in the demo: a big heat bill is what a heat pump pays back
against. Break-even inside a decade.

**Then the sentence that decides it.** The agent will ask what the radiators
look like, and the answer moves the whole verdict:

| Your answer | Vorlauf | JAZ | Verdict |
|---|---|---|---|
| „Fußbodenheizung." | 35 °C | 4,3 | 90/100 · gut geeignet |
| „Große flache Heizkörper, großzügig ausgelegt." | 45 °C | 3,8 | 90/100 · gut geeignet |
| „Ganz normale Heizkörper, nichts Besonderes." | 55 °C | 3,2 | 75/100 · gut geeignet |
| „Alte schmale Rippenheizkörper." | 65 °C | 2,6 | 55/100 · geeignet mit Vorbereitung |

The last row is the one to use if you want to show the advice being careful
rather than encouraging.

### Meine Mobilität

> „Ich fahre jeden Tag rund 40 Kilometer zur Arbeit, am Wochenende manchmal
> weiter. Ob ein E-Auto für mich Sinn ergibt, weiß ich ehrlich gesagt nicht."

The neutral opening, and an honest outcome: at 16.500 km im Jahr the EV comes
out about **40 € a month behind** without a home charger — and still slightly
behind with one. Low mileage is the case where it does not pay off yet, and the
advice says so.

> „Ich habe Angst, mit einem E-Auto auf der Autobahn liegen zu bleiben. Wir
> fahren regelmäßig 400 Kilometer zu meiner Schwester."

Straight at Reichweitenangst. The Alltagstauglichkeit surface answers it with
the client's own week and their own 400 km trip, broken into real charging
stops — the moment the fear usually stops being abstract.

> „Wir wohnen zur Miete, ich kann zu Hause gar nicht laden. Lohnt sich das
> trotzdem?"

The journey's actual argument: charging location beats model choice. Expect
around **940 € a year** of difference between the charging options.

> „Ich pendle 80 Kilometer am Tag, fünf Tage die Woche, und wir haben eine
> Wallbox in der Garage."

The favourable case: 29.300 km im Jahr, winter range 3,2× the daily need, and
about **52 € a month cheaper** over six years. See "The happy path" below for
the full run.

### If the agent asks

Short answers that keep a demo moving, for the questions that come up most:

- **Wärmebedarf / Gasverbrauch** — „Rund 20.000 Kilowattstunden im Jahr." Or
  „Weiß ich nicht auswendig" — it will estimate and mark the estimate as one.
- **Stellplatz** — „Ja, eigene Garage." Or „Nein, nur Straßenparken", which
  removes the wallbox option entirely.
- **Haltedauer** — „Sechs, sieben Jahre." Longer holding periods favour the EV.
- **Einkommensbonus** — do not volunteer it. The agent is instructed not to ask.
- **Anything you would rather not answer** — say so. „Das möchte ich nicht
  sagen" is handled, and the open point shows up in the right-hand column.

---

## 01 — Der persönliche Energieberater

Pick **Mein Zuhause**. The agent greets you, says in one sentence what it can
help with — whether a heat pump suits your house, what the switch costs and when
it pays back, and what funding you get — and then asks one open question. The
same three are listed on the empty screen while it speaks, so nobody has to hold
them in their head.

**Say:**
> „Unser Haus ist von 1985, etwa 160 Quadratmeter, vier Personen. Wir heizen mit
> Gas und die Heizung ist alt. Ich habe Sorge, dass eine Wärmepumpe im Winter
> nicht reicht und sich die Investition nicht lohnt."

„Das habe ich verstanden" fills in on the right, with the estimated heat demand
marked as estimated and the progress above it moving to step one. The agent
asks about the radiators — large and flat, or narrow and
old — because that, not the outside temperature, decides the answer.

**Say:**
> „Ganz normale Heizkörper, nichts Besonderes."

→ **Wärmepumpen-Check.** Flow temperature 55 °C, seasonal performance factor,
design heat load, and the winter heat load month by month. The line to listen
for: *entscheidend ist nicht die Außentemperatur, sondern wie warm das Wasser
in Ihren Heizkörpern sein muss.*

**Say:**
> „Und was kostet mich das jetzt konkret?"

→ **Szenarienvergleich**, then the **20-Jahres-Kurve** with the break-even
marked. Click a different scenario card: the comparison table re-highlights
instantly and the agent picks the change up in speech a moment later. That is
worth pointing out — the UI does not wait for the model.

**Say — and say it sceptically:**
> „Naja, das rechnet ihr euch doch schön. Was, wenn der Strompreis steigt?"

→ **Was wäre wenn.** The advice hands over the controls: a slider for the gas
price and one for the heat-pump electricity price. **Drag them while you talk.**
The heating costs, the monthly difference and the twenty-year balance move with
your hand — no spinner, no pause, nothing sent to the model. Push electricity
to 45 cents and watch the case get thin; that honesty is the point.

Then tap **Mit diesen Preisen weiterrechnen**. The agent confirms out loud that
it is now calculating with *their* prices, and the earlier surfaces rebuild
behind it. Open the assumptions afterwards: they now read „Ihre eigenen
Annahmen".

This is the moment to name what is happening technically, if the room is
technical: the sliders and the figures are bound to the same A2UI data model,
the arithmetic runs in the browser, and the backend only shipped the
coefficients. Instant preview, authoritative commit.

**Say:**
> „Gibt es dafür Förderung?"

→ **Förderung und Fahrplan.** The five steps, with the antrag-before-order
warning called out.

**Close:**
> „Was wäre mein nächster Schritt?"

→ Summary, recommendation with its open points named honestly, and a
vor-Ort-check as the handover.

---

## 02 — Der persönliche Autoberater

Pick **Meine Mobilität**.

**Say:**
> „Ich fahre täglich 55 Kilometer zur Arbeit, am Wochenende häufiger
> Langstrecke, so 450 Kilometer zu meinen Eltern. Eine Wallbox habe ich nicht.
> Ist ein E-Auto wirklich praktikabel für mich?"

→ **Alltagstauglichkeit.** Their week as bars against the winter range as a
threshold line — the bars sit well under it — plus the 450 km trip as a
timeline with real charging stops and the honest extra time.

**Say:**
> „Und rechnet sich das?"

→ **Ladelösungen zuerst.** This is the demo's best moment. With public charging
only, the EV costs about the same per 100 km as petrol. The advice is not
"buy this car", it is *sort out where you charge — that is worth around 1.800 €
a year, more than any model choice*.

→ **Kostenvergleich** then shows the EV coming out slightly *behind* on the
client's current setup, and says so. Let that land. A demo that admits an
unfavourable answer is the one people believe.

**Say:**
> „Naja, 55 Kilometer ist geschätzt. Und ich könnte schon öfter zu Hause laden."

→ **Was wäre wenn.** Two sliders: kilometres on a typical day, and the share
charged at home. Drag the home share from 0 to 80 % and watch the electricity
figure fall past the petrol figure in real time. This is the whole argument of
the journey in one gesture — *where you charge decides it, not which car you
buy* — and the client makes it themselves.

Tap **Mit diesen Werten weiterrechnen** and the cost comparison rebuilds on
their numbers.

**Say:**
> „Und wenn ich doch eine Wallbox bekomme?"

The agent updates the profile, recomputes, and the picture flips.

**Close:**
> „Was empfehlen Sie mir?"

→ Ladecheck as the next step, not a test drive. The recommendation follows the
numbers.

---

## The happy path

The two runs above are built to be *credible*: the mobility one deliberately
lands on "das rechnet sich für Sie heute nicht". That is the right demo for a
sceptical room, and the wrong one when you want to show the experience at its
best in three minutes — to a client, at a stand, on a screen behind you.

These two profiles make every number come out well while staying plausible.
Both are chosen so the advice is genuinely positive, not so the model is
steered: say these things and the arithmetic does the rest.

### Mein Zuhause — the well-suited house

The trick is that a heat pump's economics improve with the *size* of the heat
bill and the *lowness* of the flow temperature. A large, older, gas-heated house
with generously sized radiators is the case where everything lines up.

**Say:**
> „Wir haben ein Einfamilienhaus von 1985, gut 200 Quadratmeter, vier Personen.
> Gasheizung, die ist jetzt bald vierzig Jahre alt. Fenster und Dach haben wir
> vor ein paar Jahren machen lassen."

**Then, when it asks about the radiators:**
> „Große flache Heizkörper. Die waren damals ziemlich großzügig ausgelegt."

That is the sentence that decides it. Expect:

| | |
|---|---|
| Vorlauftemperatur | **45 °C** → JAZ 3,8, Eignung **90/100, „gut geeignet"** |
| Heizkosten heute | 3.929 € im Jahr |
| Mit Wärmepumpe | 2.193 € im Jahr — rund **1.700 € weniger** |
| Investition | 33.200 €, davon **15.000 € Förderung** (30 % Grund + 20 % Klimageschwindigkeit) |
| Eigenanteil | 18.200 € |
| Break-even | **9 Jahre** |
| CO₂ | 6,2 t → 2,7 t im Jahr |

**Then ask for money, then funding, then close:**
> „Und was kostet mich das?" … „Gibt es Förderung?" … „Was wäre mein nächster Schritt?"

**The what-if, if you have time.** Say „Und wenn der Gaspreis weiter steigt?"
Push the gas slider from 12 to 20 Cent: the monthly difference goes from 145 €
to 351 € and the twenty-year balance from 16.522 € to 65.976 €. Then be fair and
push electricity to 40 Cent as well — 273 €/Monat, still clearly positive. The
honest end of the range is gas at 8 and electricity at 45, where it turns
*negative*; showing that is what makes the rest believable.

### Meine Mobilität — the commuter with a wallbox

The EV case is carried by mileage and by charging at home. Eighty kilometres a
day with a wallbox is an ordinary German commute and a comfortable win.

**Say:**
> „Ich pendle jeden Tag rund 80 Kilometer, fünf Tage die Woche. Ein-, zweimal im
> Monat fahren wir 350 Kilometer zu meinen Eltern. Wir haben eine eigene Garage
> mit Wallbox. Das Auto würde ich sechs, sieben Jahre fahren."

Expect:

| | |
|---|---|
| Fahrleistung | 29.300 km im Jahr |
| Winterreichweite | 258 km — **3,2× Ihres Tagesbedarfs** |
| Autobahn im Winter | 208 km (der ehrlichste Wert) |
| Die 350-km-Fahrt | 2 Ladestopps, **60 Minuten** mehr als mit dem Verbrenner |
| Energie | **6,53 € je 100 km** gegen 11,39 € Benzin |
| Gesamtkosten über 6 Jahre | 50.635 € gegen 54.377 € — **3.742 € Vorteil, 52 € im Monat** |
| CO₂ | **− 2,3 t** im Jahr |

**The what-if.** Say „Ich lade eigentlich fast immer zu Hause." Drag the
home-charging slider from 80 to 100 %: the energy advantage goes from 111 € to
139 € a month. Drag it *down* to 50 % and it falls to 70 € — the point of the
journey, in one gesture: der Ladeort entscheidet, nicht das Modell.

**Close:**
> „Welches Auto würden Sie mir empfehlen?"

→ Mittelklasse/Limousine, Passung 92/100, 306 km im Winter, ein Ladestopp auf
der Langstrecke, ab 489 € im Monat — with its trade-offs named.

### Without a voice session

`make preview-happy` captures exactly these two runs and serves them at
`/preview.html`, so you can click through the favourable version — sliders
included — with no Vertex AI session at all. `make fixtures` puts the credible
run back; that is the one the catalog check expects, so restore it before
committing.

### If you only have ninety seconds

Run **Mein Zuhause**, say the two lines above, wait for the Wärmepumpen-Check
and the twenty-year curve, then go straight to „Naja, das rechnet ihr euch doch
schön" and drag the sliders while you talk. That single sequence carries the
whole idea: the interface is built live, the numbers are the client's own, and
the advice says the uncomfortable thing when the sliders call for it.

---

## Points worth narrating

- **The profile card is the trust anchor.** Estimated values are marked as
  estimates, open questions are listed, and correcting the agent mid-sentence
  updates it.
- **Every number has its assumptions one click away.** Open an
  `Annahmen`-Block during the run.
- **The screen grows with the conversation.** Nothing is pre-rendered; there is
  no dashboard waiting to be filled in.
- **The interface is generated, not scripted.** A different opening produces a
  different sequence of surfaces — the agent chooses which tool the moment
  calls for.
- **The catalog is fixed.** The agent composes from Google's own A2UI basic
  catalog plus three additions, and cannot invent a component or a number.
- **The chips and the table are one binding.** Clicking a scenario chip
  re-highlights the comparison table instantly, before the agent has said
  anything — that is A2UI's reactive data model, not a round trip.
- **The sliders are the same idea, taken further.** The figures under them are
  A2UI function calls over the data model, so they recompute at drag speed.
  Nothing about that is bespoke code — it is what the protocol does.
- **The consultation admits what it does not know.** Handing over the price
  assumption is a stronger trust move than defending it, and it is the reason
  the client believes the number they end up with: it is theirs.
- **The column on the right says where you are.** Six steps, and one only
  counts as done once its surface is actually on screen.
- **It says it is an AI.** The `KI-Beratung` badge sits in the frame for the
  whole session, next to `Demo-Daten`. Worth a sentence in a German room.

## If the room has no microphone

Every session accepts typed input in the dock, and the same tools fire. For a
pure design review, `/preview.html` renders every surface of both journeys
from captured fixtures with no API session at all.
