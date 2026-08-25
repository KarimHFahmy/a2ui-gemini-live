/**
 * The context column: where the conversation stands, and what I understood.
 *
 * Neither is a step in the conversation, and both change throughout it, so
 * they sit beside the advisory surfaces rather than in the flow. The column
 * exists from the first frame — the arc arrives with the session — so the
 * screen is never entirely blank while the agent is still listening.
 */

import {A2uiSurface} from '@a2ui/react/v0_9';

import {JourneyProgress} from './JourneyProgress';
import type {JourneyStep} from '../live/session';
import type {Surface} from './surfaces';

interface ContextAsideProps {
  /** "Das habe ich verstanden" — absent until the agent has understood something. */
  profile: Surface | null;
  steps: JourneyStep[];
  present: Set<string>;
}

export function ContextAside({profile, steps, present}: ContextAsideProps) {
  // Nothing to be context *about* yet — before the session frame lands, or
  // against a backend that publishes no arc. An empty bordered column would
  // read as a rendering failure.
  if (steps.length === 0 && !profile) return null;

  return (
    <aside className="aside" aria-label="Ihre Situation">
      <div className="aside__inner surface">
        <JourneyProgress steps={steps} present={present} />
        {profile ? <A2uiSurface surface={profile} /> : null}
      </div>
    </aside>
  );
}
