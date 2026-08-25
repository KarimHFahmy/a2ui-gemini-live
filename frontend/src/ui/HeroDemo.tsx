/**
 * The landing hero: the product doing its one trick, before you ask it to.
 *
 * The most characteristic thing about this experience is not a claim you can
 * put in a headline — it is that the interface assembles itself while someone
 * talks. So the hero shows that instead of describing it: a sentence arrives
 * the way a spoken one does, and the advisory panel builds beside it, piece by
 * piece, in the order the real agent builds it.
 *
 * The figures are the ones the real Wärmepumpen-Check produces for this house
 * (1985, 200 m², große Flächenheizkörper — see docs/demo-script.md). Nothing
 * here is invented for the sake of a nicer screenshot.
 *
 * The whole sequence is CSS with staggered delays: no timers, no state, and
 * `prefers-reduced-motion` lands straight on the finished composition, which is
 * the same thing the animation ends at.
 */

const SPOKEN = 'Unser Haus ist von 1985. Reicht eine Wärmepumpe im Winter?';

/**
 * Each readout the check produces, in the order it appears.
 *
 * The unit is separate from the value because the mono sets them differently —
 * the figure carries the weight, the unit trails it, the way a gauge reads.
 */
const READOUTS = [
  {
    label: 'Vorlauftemperatur',
    value: '45',
    unit: '°C',
    note: 'Ihre Heizkörper sind großzügig ausgelegt',
  },
  {label: 'Jahresarbeitszahl', value: '3,8', unit: '', note: 'aus Vorlauf und Wärmebedarf'},
];

export function HeroDemo() {
  return (
    <div className="hero" aria-label="Beispiel für eine Beratung">
      <figure className="hero__said">
        <span className="hero__ear" aria-hidden="true">
          <span className="hero__ear-dot" />
          hört zu
        </span>
        <blockquote className="hero__quote">{`\u201e${SPOKEN}\u201c`}</blockquote>
      </figure>

      <div className="hero__panel">
        <p className="hero__eyebrow">Wärmepumpen-Check</p>
        <h2 className="hero__verdict">
          Ihr Haus ist <strong>gut geeignet</strong>
        </h2>

        <dl className="hero__readouts">
          {READOUTS.map(readout => (
            <div className="hero__readout" key={readout.label}>
              <dt>{readout.label}</dt>
              <dd>
                <span className="hero__value">
                  {readout.value}
                  {readout.unit ? <span className="hero__unit">{readout.unit}</span> : null}
                </span>
                <span className="hero__note">{readout.note}</span>
              </dd>
            </div>
          ))}
        </dl>

        <p className="hero__caption">
          Entstanden in dem Moment, in dem der Satz oben gesagt wurde – nicht vorher.
        </p>
      </div>
    </div>
  );
}
