import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

// Self-hosted fonts (strictly local assets, zero Google Fonts requests)
import '@fontsource/ibm-plex-sans/400.css';
import '@fontsource/ibm-plex-sans/500.css';
import '@fontsource/ibm-plex-sans/600.css';
import '@fontsource/ibm-plex-sans/700.css';
import '@fontsource/courier-prime/400.css';
import '@fontsource/courier-prime/700.css';

import './styles/tokens.css';
import './styles/global.css';
import './styles/layout.css';
import './styles/components.css';
import './styles/animations.css';

const rootElement = document.getElementById('root');

if (!rootElement) {
  throw new Error('Fatal: #root element was not found in document.');
}

ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
