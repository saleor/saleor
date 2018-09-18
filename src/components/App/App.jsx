import React, { Component, Fragment } from 'react';
import {
  BrowserRouter as Router,
  Route,
  Link,
  Switch
} from 'react-router-dom';
import { CookiesProvider } from 'react-cookie';
import { Home, Header, Footer, PrivacyPolicy, Roadmap, Feature } from '..';
import css from './css/index.css';

class App extends Component {

  render() {
    return (
      <Router>
        <Fragment>
          <CookiesProvider>
            <Header cookies={this.props.cookies} />
          </CookiesProvider>
          <section className="container">
            <Switch>
              <Route exact path="/" component={Home} />
              <Route path="/features" component={Feature} />
              <Route path="/privacy-policy" component={PrivacyPolicy} />
              <Route path="/roadmap" component={Roadmap} />
            </Switch>
          </section>
          <Footer />
        </Fragment>
      </Router>
    );
  }
}

export default App;