import React, { Component, Fragment } from 'react';
import {
  BrowserRouter as Router,
  Route,
  Link,
  Switch,
  Redirect
} from 'react-router-dom';
import { Home, Header, Footer, PrivacyPolicy, Roadmap, Feature } from '..';
import css from './css/index.css';
import { CookiesProvider } from 'react-cookie';

import AppRouter from './AppRouter' 

const App = () => <Router>
<Fragment>
  <section className="container">
    <Switch>
      <Route exact path="/" component={AppRouter}/>
      <Route exact path="/roadmap" component={AppRouter}/>
      <Route exact path="/features" component={AppRouter}/>
      <Route exact path="/privacy-policy" component={AppRouter}/>
      <Route path="/:lang" component={AppRouter}/>
    </Switch>
  </section>
</Fragment>
</Router>
export default App;