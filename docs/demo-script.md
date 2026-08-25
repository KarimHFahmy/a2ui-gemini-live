# Demo script

Two runs of roughly four minutes. Both start from the landing page.

The point to land is not that the assistant answers well. It is that the
**interface is built for this person, while they talk** — and that it says the
uncomfortable thing when the numbers call for it.

---

## 01 — Der persönliche Energieberater

Pick **Mein Zuhause**. The agent greets and asks one open question.

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
  catalog plus two additions, and cannot invent a component or a number.
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
