/** Small shared pieces used across the advisory components. */

import type {ReactNode} from 'react';

/**
 * A tiny icon set drawn inline.
 *
 * Icon names come from the agent, so an unknown name has to degrade to
 * something harmless rather than a broken glyph — it falls back to the dot.
 */
const PATHS: Record<string, string> = {
  home: 'M3 10.5 12 3l9 7.5V21H3z',
  thermometer: 'M12 3v10.5M12 3a2 2 0 0 1 2 2v8.2a4 4 0 1 1-4 0V5a2 2 0 0 1 2-2z',
  efficiency: 'M13 2 4 14h7l-1 8 9-12h-7z',
  power: 'M12 3v9M6.3 6.3a8 8 0 1 0 11.4 0',
  chart: 'M4 20V10M10 20V4M16 20v-7M22 20H2',
  clock: 'M12 7v5l3 2M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z',
  euro: 'M17 5a7 7 0 1 0 0 14M4 10h9M4 14h9',
  trend: 'M3 17 9 11l4 4 8-8M15 7h6v6',
  tools: 'M14 6a4 4 0 0 1 5.5 5.2L21 13l-2 2-1.8-1.5A4 4 0 0 1 12 8zM10 12 3 19l2 2 7-7',
  badge: 'M12 2 4 6v6c0 5 3.4 8.5 8 10 4.6-1.5 8-5 8-10V6z',
  layers: 'M12 3 3 8l9 5 9-5zM3 13l9 5 9-5M3 18l9 5 9-5',
  route: 'M6 4a2 2 0 1 1 0 4 2 2 0 0 1 0-4zM18 16a2 2 0 1 1 0 4 2 2 0 0 1 0-4zM6 8v4a4 4 0 0 0 4 4h4',
  car: 'M5 16v2M19 16v2M3 16h18v-4l-2-5H5l-2 5zM7 13h.01M17 13h.01',
  plug: 'M9 3v6M15 3v6M6 9h12v3a6 6 0 0 1-12 0zM12 18v3',
  highway: 'M12 3v4M12 10v4M12 17v4M4 21 8 3M20 21 16 3',
  snow: 'M12 2v20M4 7l16 10M20 7 4 17',
  leaf: 'M4 20C4 10 11 4 20 4c0 9-6 16-16 16zM4 20l7-7',
  check: 'm4 12 5 5L20 6',
  info: 'M12 8h.01M11 12h1v5h1M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z',
  question: 'M9.1 9a3 3 0 1 1 4.2 2.7c-.8.4-1.3 1.2-1.3 2.1M12 17h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z',
  compare: 'M9 4v16M15 4v16M3 8h4M17 8h4M3 16h4M17 16h4',
  flag: 'M5 21V4M5 4h11l-2 4 2 4H5',
  dot: 'M12 10a2 2 0 1 1 0 4 2 2 0 0 1 0-4z',
};

export function Icon({name, size = 18}: {name?: string; size?: number}) {
  const path = (name && PATHS[name]) || PATHS.dot;
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.6}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      <path d={path} />
    </svg>
  );
}

/**
 * Renders the light Markdown the agent uses in body copy.
 *
 * Deliberately minimal — bold, italic, inline code and `- ` bullets, all
 * escaped first. Agent output is untrusted input, so nothing here ever reaches
 * `dangerouslySetInnerHTML`.
 */
export function RichText({children}: {children?: string}) {
  if (!children) return null;

  const blocks = children.split('\n\n');

  return (
    <>
      {blocks.map((block, blockIndex) => {
        const lines = block.split('\n');
        const isList = lines.every(line => line.trim().startsWith('- '));

        if (isList) {
          return (
            <ul className="rt-list" key={blockIndex}>
              {lines.map((line, i) => (
                <li key={i}>{inline(line.trim().slice(2))}</li>
              ))}
            </ul>
          );
        }

        return (
          <p className="rt-p" key={blockIndex}>
            {lines.map((line, i) => (
              <span key={i}>
                {inline(line)}
                {i < lines.length - 1 ? <br /> : null}
              </span>
            ))}
          </p>
        );
      })}
    </>
  );
}

function inline(text: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  const pattern = /(\*\*[^*]+\*\*|_[^_]+_|`[^`]+`)/g;
  let last = 0;
  let match: RegExpExecArray | null;
  let key = 0;

  while ((match = pattern.exec(text)) !== null) {
    if (match.index > last) nodes.push(text.slice(last, match.index));
    const token = match[0];
    if (token.startsWith('**')) {
      nodes.push(<strong key={key++}>{token.slice(2, -2)}</strong>);
    } else if (token.startsWith('`')) {
      nodes.push(<code key={key++}>{token.slice(1, -1)}</code>);
    } else {
      nodes.push(<em key={key++}>{token.slice(1, -1)}</em>);
    }
    last = pattern.lastIndex;
  }

  if (last < text.length) nodes.push(text.slice(last));
  return nodes;
}

/** de-DE number formatting, used everywhere a figure is shown. */
const numberFormat = new Intl.NumberFormat('de-DE', {maximumFractionDigits: 0});
const currencyFormat = new Intl.NumberFormat('de-DE', {
  style: 'currency',
  currency: 'EUR',
  maximumFractionDigits: 0,
});
const percentFormat = new Intl.NumberFormat('de-DE', {
  style: 'percent',
  maximumFractionDigits: 0,
});

export function formatValue(
  value: number,
  format: 'number' | 'currency' | 'percent' = 'number',
): string {
  if (!Number.isFinite(value)) return '–';
  if (format === 'currency') return currencyFormat.format(value);
  if (format === 'percent') return percentFormat.format(value);
  return numberFormat.format(value);
}

export function Eyebrow({children}: {children?: ReactNode}) {
  if (!children) return null;
  return <span className="eyebrow">{children}</span>;
}
