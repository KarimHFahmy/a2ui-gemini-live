/**
 * The three additions to Google's basic catalog.
 *
 * Both are `createComponentImplementation`, so the Generic Binder resolves
 * every data binding before the component renders and re-renders it when the
 * agent patches the data model.
 */

import {createComponentImplementation} from '@a2ui/react/v0_9';

import {
  ComparisonTableApi,
  MetricChartApi,
  StatCardApi,
  TONE_LABEL,
  asKey,
  asList,
  asStrings,
  asTone,
  type Column,
  type Row,
} from '../schemas';
import {useLocale} from '../../LocaleContext';
import {Chart} from './Chart';

/** The mark that carries tone where colour alone would not be enough. */
const TONE_MARK = {positive: '✓', neutral: '→', caution: '!'} as const;

export const StatCard = createComponentImplementation(StatCardApi, ({props, buildChild}) => {
  const tone = asTone(props.tone);
  const {locale} = useLocale();

  return (
    <section
      className={`stat stat--${tone}`}
      style={props.weight ? {flex: props.weight, minWidth: 0} : undefined}
    >
      <h4 className="stat__title">
        <span className="stat__mark" aria-hidden="true">
          {TONE_MARK[tone]}
        </span>
        <span className="stat__tone-label">{TONE_LABEL[locale][tone]}: </span>
        {props.title}
      </h4>

      {props.metric ? (
        <p className="stat__metric">
          {props.metric}
          {props.metricLabel ? (
            <span className="stat__metric-label">{props.metricLabel}</span>
          ) : null}
        </p>
      ) : null}

      {/* The body stays a child so the official Text renders its Markdown. */}
      {props.child ? <div className="stat__body">{buildChild(props.child)}</div> : null}
    </section>
  );
});

export const MetricChart = createComponentImplementation(MetricChartApi, ({props}) => (
  <section className="chart">
    {props.title ? <h3 className="chart__title">{props.title}</h3> : null}
    {props.subtitle ? <p className="chart__subtitle">{props.subtitle}</p> : null}
    <Chart
      chartType={props.chartType ?? 'bar'}
      categories={asStrings(props.categories)}
      series={asList(props.series)}
      unit={props.unit}
      valueFormat={props.valueFormat ?? 'number'}
    />
  </section>
));

export const ComparisonTable = createComponentImplementation(ComparisonTableApi, ({props}) => {
  const columns = asList<Column>(props.columns);
  const rows = asList<Row>(props.rows);
  const highlight = asKey(props.highlight);

  return (
    <section className="compare">
      {props.title ? <h3 className="compare__title">{props.title}</h3> : null}
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

export const ADVISORY_COMPONENTS = [StatCard, MetricChart, ComparisonTable];
