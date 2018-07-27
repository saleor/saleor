import * as React from 'react';
import { render } from 'react-dom';
import { BrowserRouter, Route, Switch } from 'react-router-dom';

import css from './css/index.css';

import Home from './components/Home';

render(
  <BrowserRouter basename="/">
    <Switch>
      <Route path="/" render={routeProps => <Home {...routeProps} />} />
    </Switch>
  </BrowserRouter>,
  document.getElementById('root')
);