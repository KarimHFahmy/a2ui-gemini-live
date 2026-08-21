/**
 * The advisory building blocks — the "freigegebener Komponenten-Katalog".
 *
 * Each is a `createComponentImplementation`, so the Generic Binder resolves
 * every data binding before the component renders and re-renders it when the
 * agent patches the data model.
 */

import {createComponentImplementation} from '@a2ui/react/v0_9';

import {
  AdvisoryHeaderApi,
  AssumptionNoteApi,
  ComparisonTableApi,
  InsightCardApi,
  MetricChartApi,
  NextStepCTAApi,
  ProfileSummaryApi,
  RecommendationApi,
  ScenarioSelectorApi,
  TimelineApi,
  asList,
  asStrings,
  type Column,
  type Fact,
  type Row,
  type ScenarioCard,
  type Step,
} from '../schemas';
import {Chart} from './Chart';
import {Eyebrow, Icon, RichText} from './primitives';

export const AdvisoryHeader = createComponentImplementation(AdvisoryHeaderApi, ({props}) => (
  <header className="adv-header">
    <Eyebrow>{props.eyebrow}</Eyebrow>
    <h2 className="adv-header__title">
      {props.icon ? (
        <span className="adv-header__icon" aria-hidden="true">
          <Icon name={props.icon} size={20} />
        </span>
      ) : null}
      {props.title}
    </h2>
    {props.subtitle ? <p className="adv-header__subtitle">{props.subtitle}</p> : null}
  </header>
));

export const ProfileSummary = createComponentImplementation(ProfileSummaryApi, ({props}) => {
  const facts = asList<Fact>(props.facts);
  const openPoints = asStrings(props.openPoints);

  return (
    <section className="panel profile">
      {props.title ? <h3 className="panel__title">{props.title}</h3> : null}
      <dl className="profile__facts">
        {facts.map((fact, index) => (
          <div className="profile__fact" key={index}>
            <dt>{fact.label}</dt>
            <dd>
              {fact.wert}
              {fact.geschaetzt ? (
                <span className="chip chip--estimate" title="Von mir geschätzt">
                  geschätzt
                </span>
              ) : null}
            </dd>
          </div>
        ))}
      </dl>

      {openPoints.length > 0 ? (
        <div className="profile__open">
          <span className="profile__open-label">Noch offen</span>
          <ul>
            {openPoints.map((point, index) => (
              <li key={index}>{point}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {props.note ? <p className="panel__note">{props.note}</p> : null}
    </section>
  );
});

export const InsightCard = createComponentImplementation(InsightCardApi, ({props}) => {
  const tone = props.tone ?? 'neutral';

  return (
    <section className={`panel insight insight--${tone}`}>
      <div className="insight__head">
        <span className="insight__icon" aria-hidden="true">
          <Icon name={props.icon} />
        </span>
        <h3 className="insight__title">{props.title}</h3>
      </div>

      {props.metric ? (
        <p className="insight__metric">
          <span className="insight__metric-value">{props.metric}</span>
          {props.metricLabel ? (
            <span className="insight__metric-label">{props.metricLabel}</span>
          ) : null}
        </p>
      ) : null}

      <div className="insight__body">
        <RichText>{props.body}</RichText>
      </div>
    </section>
  );
});

export const ComparisonTable = createComponentImplementation(ComparisonTableApi, ({props}) => {
  const columns = asList<Column>(props.columns);
  const rows = asList<Row>(props.rows);
  const highlight = props.highlight;

  return (
    <section className="panel compare">
      {props.title ? <h3 className="panel__title">{props.title}</h3> : null}
      {/* Wide tables scroll inside their own container so the page never does. */}
      <div className="compare__scroll">
        <table className="compare__table">
          <thead>
            <tr>
              <th scope="col" className="compare__criterion">
                Kriterium
              </th>
              {columns.map(column => (
                <th
                  scope="col"
                  key={column.id}
                  className={column.id === highlight ? 'is-highlight' : undefined}
                >
                  {column.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, rowIndex) => (
              <tr key={rowIndex} className={row.hervorheben ? 'is-emphasis' : undefined}>
                <th scope="row" className="compare__criterion">
                  {row.label}
                </th>
                {columns.map((column, columnIndex) => (
                  <td
                    key={column.id}
                    className={[
                      column.id === highlight ? 'is-highlight' : '',
                      row.akzent ? `is-${row.akzent}` : '',
                    ]
                      .filter(Boolean)
                      .join(' ')}
                  >
                    {row.werte?.[columnIndex] ?? '–'}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
});

export const ScenarioSelector = createComponentImplementation(ScenarioSelectorApi, ({props}) => {
  const scenarios = asList<ScenarioCard>(props.scenarios);

  /**
   * Two-way binding in action: `setSelected` writes straight into the data
   * model, so the comparison table below re-highlights immediately. The action
   * then tells the agent, which reacts in speech — the UI never waits on it.
   */
  const choose = (id: string) => {
    props.setSelected?.(id);
    props.action?.();
  };

  return (
    <section className="panel scenarios">
      {props.title ? <h3 className="panel__title">{props.title}</h3> : null}
      <div className="scenarios__grid" role="radiogroup" aria-label="Szenario auswählen">
        {scenarios.map(scenario => {
          const active = scenario.id === props.selected;
          return (
            <button
              type="button"
              role="radio"
              aria-checked={active}
              key={scenario.id}
              className={`scenario ${active ? 'is-active' : ''}`}
              onClick={() => choose(scenario.id)}
            >
              {scenario.empfohlen ? <span className="scenario__flag">Empfehlung</span> : null}
              <span className="scenario__label">{scenario.label}</span>
              {scenario.kennzahl ? (
                <span className="scenario__metric">
                  <span className="scenario__metric-value">{scenario.kennzahl}</span>
                  {scenario.kennzahlLabel ? (
                    <span className="scenario__metric-label">{scenario.kennzahlLabel}</span>
                  ) : null}
                </span>
              ) : null}
              {scenario.beschreibung ? (
                <span className="scenario__desc">{scenario.beschreibung}</span>
              ) : null}
              {scenario.massnahmen?.length ? (
                <span className="scenario__tags">
                  {scenario.massnahmen.map((measure, index) => (
                    <span className="chip" key={index}>
                      {measure}
                    </span>
                  ))}
                </span>
              ) : null}
            </button>
          );
        })}
      </div>
    </section>
  );
});

export const MetricChart = createComponentImplementation(MetricChartApi, ({props}) => (
  <section className="panel chart">
    {props.title ? <h3 className="panel__title">{props.title}</h3> : null}
    {props.subtitle ? <p className="panel__subtitle">{props.subtitle}</p> : null}
    <Chart
      chartType={props.chartType ?? 'bar'}
      categories={asStrings(props.categories)}
      series={asList(props.series)}
      unit={props.unit}
      valueFormat={props.valueFormat ?? 'number'}
    />
  </section>
));

export const Timeline = createComponentImplementation(TimelineApi, ({props}) => {
  const steps = asList<Step>(props.steps);

  return (
    <section className="panel timeline">
      {props.title ? <h3 className="panel__title">{props.title}</h3> : null}
      <ol className="timeline__list">
        {steps.map((step, index) => (
          <li className={`timeline__step is-${step.status ?? 'default'}`} key={index}>
            <span className="timeline__marker" aria-hidden="true">
              {index + 1}
            </span>
            <div className="timeline__content">
              <div className="timeline__head">
                <h4>{step.titel}</h4>
                {step.dauer ? <span className="timeline__duration">{step.dauer}</span> : null}
              </div>
              {step.detail ? <p>{step.detail}</p> : null}
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
});

export const Recommendation = createComponentImplementation(RecommendationApi, ({props}) => {
  const pros = asStrings(props.pros);
  const cons = asStrings(props.cons);
  const score = typeof props.fitScore === 'number' ? props.fitScore : undefined;

  return (
    <section className="panel recommendation">
      <div className="recommendation__head">
        {typeof props.rank === 'number' ? (
          <span className="recommendation__rank">{props.rank}</span>
        ) : null}
        <div className="recommendation__title-group">
          <h3>{props.title}</h3>
          {props.summary ? <p className="recommendation__summary">{props.summary}</p> : null}
        </div>
        {score !== undefined ? (
          <div
            className="recommendation__fit"
            role="img"
            aria-label={`${props.fitLabel ?? 'Passung'}: ${score} von 100`}
          >
            <div className="recommendation__fit-bar">
              <span style={{width: `${Math.max(0, Math.min(100, score))}%`}} />
            </div>
            <span className="recommendation__fit-value">{score}</span>
            {props.fitLabel ? (
              <span className="recommendation__fit-label">{props.fitLabel}</span>
            ) : null}
          </div>
        ) : null}
      </div>

      {pros.length > 0 || cons.length > 0 ? (
        <div className="recommendation__lists">
          {pros.length > 0 ? (
            <div className="recommendation__list recommendation__list--pro">
              <h4>Dafür spricht</h4>
              <ul>
                {pros.map((item, index) => (
                  <li key={index}>{item}</li>
                ))}
              </ul>
            </div>
          ) : null}
          {cons.length > 0 ? (
            <div className="recommendation__list recommendation__list--con">
              <h4>Zu bedenken</h4>
              <ul>
                {cons.map((item, index) => (
                  <li key={index}>{item}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  );
});

export const NextStepCTA = createComponentImplementation(NextStepCTAApi, ({props}) => (
  <section className="panel cta">
    <div className="cta__text">
      <h3>{props.title}</h3>
      {props.body ? <p>{props.body}</p> : null}
    </div>
    <div className="cta__actions">
      <button type="button" className="btn btn--primary" onClick={() => props.primaryAction?.()}>
        {props.primaryLabel}
      </button>
      {props.secondaryLabel && props.secondaryAction ? (
        <button type="button" className="btn" onClick={() => props.secondaryAction?.()}>
          {props.secondaryLabel}
        </button>
      ) : null}
    </div>
  </section>
));

export const AssumptionNote = createComponentImplementation(AssumptionNoteApi, ({props}) => {
  const assumptions = asStrings(props.assumptions);

  return (
    <details className="assumptions">
      <summary>
        <Icon name="info" size={15} />
        <span>{props.title ?? 'Annahmen und Datenquellen'}</span>
        <span className="assumptions__count">{assumptions.length}</span>
      </summary>
      <ul className="assumptions__list">
        {assumptions.map((item, index) => (
          <li key={index}>{item}</li>
        ))}
      </ul>
      {props.source || props.asOf ? (
        <p className="assumptions__source">
          {[props.source, props.asOf].filter(Boolean).join(' · ')}
        </p>
      ) : null}
    </details>
  );
});

export const ADVISORY_COMPONENTS = [
  AdvisoryHeader,
  ProfileSummary,
  InsightCard,
  ComparisonTable,
  ScenarioSelector,
  MetricChart,
  Timeline,
  Recommendation,
  NextStepCTA,
  AssumptionNote,
];
