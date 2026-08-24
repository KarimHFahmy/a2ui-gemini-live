/**
 * "Das habe ich verstanden", in its own column.
 *
 * The profile is persistent context rather than a step in the conversation, so
 * it sits beside the advisory surfaces instead of above them. As a sticky top
 * band it cost the stage a third of its height for something the client only
 * glances at.
 */

import {A2uiSurface} from '@a2ui/react/v0_9';

import type {Surface} from './surfaces';

export function ProfileAside({surface}: {surface: Surface}) {
  return (
    <aside className="aside" aria-label="Ihre Situation">
      <div className="aside__inner surface">
        <A2uiSurface surface={surface} />
      </div>
    </aside>
  );
}
