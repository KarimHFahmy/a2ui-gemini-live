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

import {useLocale} from '../LocaleContext';

/**
 * Each readout the check produces, in the order it appears.
 *
 * The unit is separate from the value because the mono sets them differently —
 * the figure carries the weight, the unit trails it, the way a gauge reads.
 * The figures themselves are language-dependent — 3,8 against 3.8 — so they
 * come from the catalog with everything else rather than being formatted here.
 */
const READOUTS = [1, 2] as const;

export function HeroDemo() {
  const {locale, t} = useLocale();
  const quote =
    locale === 'de' ? `\u201e${t('hero.spoken')}\u201c` : `\u201c${t('hero.spoken')}\u201d`;

  return (
    <div className="hero" aria-label={t('hero.aria')}>
      <figure className="hero__said">
        <span className="hero__ear" aria-hidden="true">
          <span className="hero__ear-dot" />
          {t('hero.listening')}
        </span>
        <blockquote className="hero__quote">{quote}</blockquote>
      </figure>

      <div className="hero__panel">
        <p className="hero__eyebrow">{t('hero.eyebrow')}</p>
        <h2 className="hero__verdict">
          {t('hero.verdict.before')}
          <strong>{t('hero.verdict.strong')}</strong>
        </h2>

        <dl className="hero__readouts">
          {READOUTS.map(index => {
            const unit = t(`hero.readout.${index}.unit` as const);
            return (
              <div className="hero__readout" key={index}>
                <dt>{t(`hero.readout.${index}.label` as const)}</dt>
                <dd>
                  <span className="hero__value">
                    {t(`hero.readout.${index}.value` as const)}
                    {unit ? <span className="hero__unit">{unit}</span> : null}
                  </span>
                  <span className="hero__note">{t(`hero.readout.${index}.note` as const)}</span>
                </dd>
              </div>
            );
          })}
        </dl>

        <p className="hero__caption">{t('hero.caption')}</p>
      </div>
    </div>
  );
}
