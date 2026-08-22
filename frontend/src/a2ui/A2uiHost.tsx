/**
 * Everything the official renderer needs to be fully itself.
 *
 * `@a2ui/react`'s `Text` component renders Markdown through an injected
 * renderer rather than bundling one, so a host that does not provide it gets
 * literal asterisks. This wires up the official `@a2ui/markdown-it` renderer
 * (markdown-it + DOMPurify), which is also what keeps agent-authored text from
 * becoming an XSS vector.
 */

import type {ReactNode} from 'react';
import {MarkdownContext} from '@a2ui/react/v0_9';
import {renderMarkdown} from '@a2ui/markdown-it';

export function A2uiHost({children}: {children: ReactNode}) {
  return <MarkdownContext.Provider value={renderMarkdown}>{children}</MarkdownContext.Provider>;
}
