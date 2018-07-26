import * as React from 'react';
import { render } from 'react-dom';
import { BrowserRouter, Route, Switch } from 'react-router-dom';

import css from './css/index.css';

import Page from './components/Page';

render(
  <BrowserRouter basename="/">
    <Switch>
      <Route path="/" render={routeProps => <Page {...routeProps} />} />
    </Switch>
  </BrowserRouter>,
  document.getElementById('root')
);