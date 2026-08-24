/**
 * Inline SVG charts for the advisory catalog.
 *
 * Hand-rolled rather than pulled from a chart library: the shapes needed here
 * are few, the visual language has to match the rest of the catalog exactly,
 * and a live demo benefits from a small bundle. Every chart also renders a
 * table-shaped accessible summary, since the numbers are the point.
 */

import {useId} from 'react';

import {formatValue, type Series} from '../schemas';

type ChartType = 'bar' | 'groupedBar' | 'stackedBar' | 'line' | 'donut';
type ValueFormat = 'number' | 'currency' | 'percent';

interface ChartProps {
  chartType: ChartType;
  categories: string[];
  series: Series[];
  unit?: string;
  valueFormat?: ValueFormat;
}

const SERIES_COLORS = [
  'var(--series-1)',
  'var(--series-2)',
  'var(--series-3)',
  'var(--series-4)',
  'var(--series-5)',
];

const WIDTH = 720;
const HEIGHT = 300;
const PAD = {top: 16, right: 16, bottom: 40, left: 64};

export function Chart({chartType, categories, series, unit, valueFormat = 'number'}: ChartProps) {
  const clean = series.filter(s => Array.isArray(s?.werte));

  if (categories.length === 0 || clean.length === 0) {
    return <p className="chart__empty">Noch keine Daten für dieses Diagramm.</p>;
  }

  const plotWidth = WIDTH - PAD.left - PAD.right;
  const plotHeight = HEIGHT - PAD.top - PAD.bottom;

  /**
   * A stacked chart's axis has to hold the column total, not the tallest
   * single value — otherwise the top segment runs off the plot.
   */
  const maxValue =
    chartType === 'stackedBar'
      ? Math.max(...categories.map((_, i) => clean.reduce((sum, s) => sum + (s.werte[i] ?? 0), 0)))
      : Math.max(...clean.flatMap(s => s.werte.map(v => v ?? 0)));
  const minValue = Math.min(0, ...clean.flatMap(s => s.werte.map(v => v ?? 0)));

  const {bottom, top, step} = axisScale(minValue, maxValue);
  const span = top - bottom || 1;

  const y = (value: number) => PAD.top + plotHeight - ((value - bottom) / span) * plotHeight;
  const ticks: number[] = [];
  for (let tick = bottom; tick <= top + step / 2; tick += step) ticks.push(tick);

  return (
    <figure className="chart__figure">
      <div className="chart__scroll">
        <svg
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          className="chart__svg"
          role="img"
          aria-label={`Diagramm mit ${clean.length} Datenreihen über ${categories.length} Kategorien`}
          preserveAspectRatio="xMidYMid meet"
        >
          {/* Gridlines and value axis */}
          {ticks.map(tick => (
            <g key={tick}>
              <line
                x1={PAD.left}
                x2={WIDTH - PAD.right}
                y1={y(tick)}
                y2={y(tick)}
                className={tick === 0 ? 'chart__axis' : 'chart__grid'}
              />
              <text
                x={PAD.left - 10}
                y={y(tick)}
                className="chart__tick"
                textAnchor="end"
                dy="0.32em"
              >
                {compact(tick, valueFormat)}
              </text>
            </g>
          ))}

          {chartType === 'line' ? (
            <LineSeries
              series={clean}
              categories={categories}
              y={y}
              plotWidth={plotWidth}
              padLeft={PAD.left}
            />
          ) : (
            <BarSeries
              chartType={chartType}
              series={clean}
              categories={categories}
              y={y}
              plotWidth={plotWidth}
              padLeft={PAD.left}
              baseline={y(Math.max(bottom, 0))}
            />
          )}

          {/* Category axis. Bars occupy a band per category, so their labels
              sit at the band centre; a line's points sit *on* the category, so
              its labels have to share the point's x or they read shifted. */}
          {categories.map((category, index) => (
            <text
              key={index}
              x={categoryX(chartType, index, categories.length, plotWidth, PAD.left)}
              y={HEIGHT - PAD.bottom + 20}
              className="chart__label"
              textAnchor={
                chartType === 'line' && index === 0
                  ? 'start'
                  : chartType === 'line' && index === categories.length - 1
                    ? 'end'
                    : 'middle'
              }
            >
              {category}
            </text>
          ))}
        </svg>
      </div>

      <figcaption className="chart__legend">
        {clean.map((s, index) => (
          <span className="chart__legend-item" key={index}>
            <span
              className="chart__swatch"
              style={{background: SERIES_COLORS[index % SERIES_COLORS.length]}}
              aria-hidden="true"
            />
            {s.label}
          </span>
        ))}
        {unit ? <span className="chart__unit">in {unit}</span> : null}
      </figcaption>

      {/* The same numbers, reachable by screen readers and by anyone who wants
          to read the figures rather than the shapes. */}
      <details className="chart__data">
        <summary>Datenwerte anzeigen</summary>
        <div className="chart__scroll">
          <table className="chart__table">
            <thead>
              <tr>
                <th scope="col" />
                {categories.map(category => (
                  <th scope="col" key={category}>
                    {category}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {clean.map((s, index) => (
                <tr key={index}>
                  <th scope="row">{s.label}</th>
                  {categories.map((_, i) => (
                    <td key={i}>{formatValue(s.werte[i] ?? 0, valueFormat)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </figure>
  );
}

function BarSeries({
  chartType,
  series,
  categories,
  y,
  plotWidth,
  padLeft,
  baseline,
}: {
  chartType: ChartType;
  series: Series[];
  categories: string[];
  y: (value: number) => number;
  plotWidth: number;
  padLeft: number;
  baseline: number;
}) {
  const step = plotWidth / categories.length;
  const groupPad = step * 0.18;
  const groupWidth = step - groupPad * 2;

  /**
   * A single bar series plus a flat comparison series is the "fits under the
   * line" pattern (weekly driving against winter range). Drawing the second
   * series as a threshold line rather than a second bar makes the comparison
   * readable at a glance.
   */
  const thresholdIndex =
    chartType === 'bar' && series.length === 2 && isFlat(series[1].werte) ? 1 : -1;

  const barSeries = series.filter((_, i) => i !== thresholdIndex);
  const perBar =
    chartType === 'groupedBar' ? groupWidth / Math.max(barSeries.length, 1) : groupWidth;

  return (
    <>
      {categories.map((_, categoryIndex) => {
        const groupX = padLeft + step * categoryIndex + groupPad;
        let stackTop = baseline;

        return (
          <g key={categoryIndex}>
            {barSeries.map((s, seriesIndex) => {
              const value = s.werte[categoryIndex] ?? 0;
              const color = SERIES_COLORS[series.indexOf(s) % SERIES_COLORS.length];

              if (chartType === 'stackedBar') {
                const height = Math.abs(baseline - y(value));
                stackTop -= height;
                return (
                  <rect
                    key={seriesIndex}
                    x={groupX}
                    y={stackTop}
                    width={groupWidth}
                    height={Math.max(height, 0)}
                    fill={color}
                    rx={2}
                  >
                    <title>{`${s.label}: ${value}`}</title>
                  </rect>
                );
              }

              const top = Math.min(y(value), baseline);
              const height = Math.abs(y(value) - baseline);
              return (
                <rect
                  key={seriesIndex}
                  x={groupX + perBar * seriesIndex}
                  y={top}
                  width={Math.max(perBar - 3, 2)}
                  height={Math.max(height, 1)}
                  fill={color}
                  rx={3}
                >
                  <title>{`${s.label}: ${value}`}</title>
                </rect>
              );
            })}
          </g>
        );
      })}

      {thresholdIndex >= 0 ? (
        <Threshold
          value={series[thresholdIndex].werte[0] ?? 0}
          label={series[thresholdIndex].label}
          y={y}
          padLeft={padLeft}
          plotWidth={plotWidth}
          color={SERIES_COLORS[thresholdIndex % SERIES_COLORS.length]}
        />
      ) : null}
    </>
  );
}

function Threshold({
  value,
  label,
  y,
  padLeft,
  plotWidth,
  color,
}: {
  value: number;
  label: string;
  y: (value: number) => number;
  padLeft: number;
  plotWidth: number;
  color: string;
}) {
  return (
    <g>
      <line
        x1={padLeft}
        x2={padLeft + plotWidth}
        y1={y(value)}
        y2={y(value)}
        stroke={color}
        strokeWidth={2}
        strokeDasharray="6 4"
      />
      <text x={padLeft + plotWidth} y={y(value) - 8} className="chart__threshold" textAnchor="end">
        {label}
      </text>
    </g>
  );
}

function LineSeries({
  series,
  categories,
  y,
  plotWidth,
  padLeft,
}: {
  series: Series[];
  categories: string[];
  y: (value: number) => number;
  plotWidth: number;
  padLeft: number;
}) {
  const gradientId = useId();
  const step = categories.length > 1 ? plotWidth / (categories.length - 1) : plotWidth;
  const x = (index: number) => padLeft + step * index;

  return (
    <>
      {series.map((s, seriesIndex) => {
        const color = SERIES_COLORS[seriesIndex % SERIES_COLORS.length];
        const points = categories.map((_, i) => `${x(i)},${y(s.werte[i] ?? 0)}`).join(' ');

        return (
          <g key={seriesIndex}>
            <polyline
              points={points}
              fill="none"
              stroke={color}
              strokeWidth={2.5}
              strokeLinejoin="round"
              strokeLinecap="round"
            />
            {categories.map((_, i) => (
              <circle key={i} cx={x(i)} cy={y(s.werte[i] ?? 0)} r={3.5} fill={color}>
                <title>{`${s.label}: ${s.werte[i] ?? 0}`}</title>
              </circle>
            ))}
          </g>
        );
      })}
      <defs>
        <linearGradient id={gradientId} />
      </defs>
    </>
  );
}

/** Where a category sits on the x axis, which differs by chart type. */
function categoryX(
  chartType: ChartType,
  index: number,
  count: number,
  plotWidth: number,
  padLeft: number,
): number {
  if (chartType === 'line') {
    return count > 1 ? padLeft + (plotWidth / (count - 1)) * index : padLeft + plotWidth / 2;
  }
  const step = plotWidth / count;
  return padLeft + step * index + step / 2;
}

function isFlat(values: number[]): boolean {
  return values.length > 1 && values.every(v => v === values[0]);
}

const TICK_TARGET = 5;
/** Step sizes that produce axis labels a reader can do arithmetic with. */
const NICE_STEPS = [1, 1.5, 2, 2.5, 3, 5, 10];

/**
 * Picks a readable axis range.
 *
 * Rounding the maximum alone leaves charts sitting in the bottom third of
 * their plot (a 258 km threshold under a 500 km axis). Choosing the step
 * first, then snapping the bounds to it, keeps the data filling the frame
 * while every gridline still lands on a round number.
 */
function axisScale(min: number, max: number): {bottom: number; top: number; step: number} {
  if (max <= 0 && min >= 0) return {bottom: 0, top: 1, step: 0.25};

  const range = Math.max(max - Math.min(min, 0), Math.abs(max)) || 1;
  const rawStep = range / TICK_TARGET;
  const magnitude = 10 ** Math.floor(Math.log10(rawStep));
  const normalised = rawStep / magnitude;
  const step = (NICE_STEPS.find(candidate => candidate >= normalised) ?? 10) * magnitude;

  return {
    bottom: min < 0 ? Math.floor(min / step) * step : 0,
    top: Math.ceil(max / step) * step,
    step,
  };
}

/** Axis labels need to stay short: 70.000 € becomes 70 Tsd. €. */
function compact(value: number, format: ValueFormat): string {
  const abs = Math.abs(value);
  const suffix = format === 'currency' ? ' €' : '';
  if (abs >= 1_000_000) return `${(value / 1_000_000).toLocaleString('de-DE')} Mio.${suffix}`;
  if (abs >= 10_000) return `${Math.round(value / 1000).toLocaleString('de-DE')} Tsd.${suffix}`;
  return formatValue(value, format === 'currency' ? 'number' : format) + suffix;
}
