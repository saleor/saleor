import * as React from 'react';
import { render } from 'react-dom';
import { BrowserRouter, Route, Switch } from 'react-router-dom';
import { CookiesProvider } from 'react-cookie';
import { App } from './components';

render(
  <CookiesProvider>
    <App />
  </CookiesProvider>,
  document.getElementById('root')
);