import * as React from 'react';
import { render } from 'react-dom';
import { BrowserRouter, Route, Switch } from 'react-router-dom';
import { App } from './components';

render(
    <App />,
  document.getElementById('root')
);
