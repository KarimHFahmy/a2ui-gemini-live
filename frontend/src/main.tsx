import {StrictMode} from 'react';
import {createRoot} from 'react-dom/client';

import {injectStyles} from '@a2ui/react/styles';
// Component styles for the basic catalog (CSS Modules, emitted as one sheet).
// Not in the package's export map, so it is imported by path.
import '../node_modules/@a2ui/react/v0_9/index.css';
import {injectBasicCatalogStyles} from '@a2ui/web_core/v0_9/basic_catalog';

import './styles/theme.css';
import './styles/app.css';
import './styles/blocks.css';

import App from './App';

// The renderer ships its structural and basic-catalog CSS as injectable
// strings rather than as a stylesheet asset. Injecting before the first render
// means our own tokens (loaded above) win on specificity where they overlap.
injectStyles();
injectBasicCatalogStyles();

const container = document.getElementById('root');
if (!container) throw new Error('Root element missing');

createRoot(container).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
