import React, { Component, Fragment } from 'react';
import {
  BrowserRouter as Router,
  Route,
  Link,
  Switch
} from 'react-router-dom';

import { Home, Header } from '..';
import css from './css/index.css';

class App extends Component {
  render() {
    return (
      <Router>
        <Fragment>
          <Header/>
          <section className="container">
            <Switch>
              <Route exact path="/" component={Home} />
              <Route path="/features" component={Home} />
            </Switch>
          </section>
          <footer></footer>
        </Fragment>
      </Router>
    );
  }
}

export default App;