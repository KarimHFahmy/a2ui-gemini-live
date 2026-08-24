/**
 * Which surface is context and which is conversation.
 *
 * The agent streams every advisory surface through the same channel; the only
 * one that behaves differently is the profile. It is not a step in the
 * conversation — it is what the agent currently believes about the client, and
 * it changes throughout — so it lives in its own column rather than in the
 * flow.
 */

import type {ReactComponentImplementation} from '@a2ui/react/v0_9';
import type {SurfaceModel} from '@a2ui/web_core/v0_9';

export type Surface = SurfaceModel<ReactComponentImplementation>;

/** Must match the surface id the composers use for "Das habe ich verstanden". */
export const PROFILE_SURFACE_ID = 'profil';

export function splitSurfaces(surfaces: Surface[]): {
  profile: Surface | null;
  flow: Surface[];
} {
  return {
    profile: surfaces.find(surface => surface.id === PROFILE_SURFACE_ID) ?? null,
    flow: surfaces.filter(surface => surface.id !== PROFILE_SURFACE_ID),
  };
}
