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

The profile card appears at the top with the estimated heat demand marked as
estimated. The agent asks about the radiators — large and flat, or narrow and
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

## If the room has no microphone

Every session accepts typed input in the dock, and the same tools fire. For a
pure design review, `/preview.html` renders every surface of both journeys
from captured fixtures with no API session at all.
