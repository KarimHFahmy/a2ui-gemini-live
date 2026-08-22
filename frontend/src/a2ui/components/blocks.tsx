/**
 * The two additions to Google's basic catalog.
 *
 * Both are `createComponentImplementation`, so the Generic Binder resolves
 * every data binding before the component renders and re-renders it when the
 * agent patches the data model.
 */

import {createComponentImplementation} from '@a2ui/react/v0_9';

import {
  ComparisonTableApi,
  MetricChartApi,
  asKey,
  asList,
  asStrings,
  type Column,
  type Row,
} from '../schemas';
import {Chart} from './Chart';

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

export const ADVISORY_COMPONENTS = [MetricChart, ComparisonTable];
