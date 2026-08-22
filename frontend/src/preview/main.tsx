import {StrictMode} from 'react';
import {createRoot} from 'react-dom/client';

import {injectStyles} from '@a2ui/react/styles';
import '../../node_modules/@a2ui/react/v0_9/index.css';
import {injectBasicCatalogStyles} from '@a2ui/web_core/v0_9/basic_catalog';

import '../styles/theme.css';
import '../styles/app.css';
import '../styles/blocks.css';

import Preview from './Preview';

injectStyles();
injectBasicCatalogStyles();

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Preview />
  </StrictMode>,
);
