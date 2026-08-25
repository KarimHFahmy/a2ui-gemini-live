/**
 * Where the conversation stands, without turning it into a form.
 *
 * A voice advisory session has no visible structure: the client hears one
 * answer at a time and cannot tell whether they are two minutes or ten from
 * something useful. That is the classic orientation gap, and it is why people
 * abandon otherwise good conversational products.
 *
 * The arc comes from the backend (`Journey.steps`) and a step counts as done
 * only once its surface has actually arrived — so this never promises a step
 * that has not happened, and never gets out of step with the screen. Surfaces
 * that answer a question rather than advance the conversation (a concern, the
 * what-if view) are not steps and deliberately do not appear here.
 */

import type {JourneyStep} from '../live/session';

interface JourneyProgressProps {
  steps: JourneyStep[];
  /** Surface ids currently on screen. */
  present: Set<string>;
}

export function JourneyProgress({steps, present}: JourneyProgressProps) {
  if (steps.length === 0) return null;

  const done = steps.filter(step => present.has(step.surfaceId)).length;
  // The step after the last completed one is what the conversation is heading
  // for — named, so the wait has a subject.
  const next = steps[done];

  return (
    <nav
      className="progress"
      aria-label="Fortschritt der Beratung"
      data-done={done}
      data-total={steps.length}
    >
      <ol className="progress__steps">
        {steps.map((step, index) => (
          <li
            key={step.surfaceId}
            className="progress__step"
            data-state={present.has(step.surfaceId) ? 'done' : index === done ? 'next' : 'todo'}
          >
            <span className="progress__dot" aria-hidden="true" />
            <span className="progress__label">{step.label}</span>
          </li>
        ))}
      </ol>
      <p className="progress__caption">
        {next ? `Als Nächstes: ${next.label}` : 'Alle Schritte durchlaufen'}
        <span className="progress__count">
          {done} / {steps.length}
        </span>
      </p>
    </nav>
  );
}
