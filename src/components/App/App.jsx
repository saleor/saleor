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

import { I18nProvider } from '@lingui/react';

class App extends Component {

  render() {
    return (
      <I18nProvider language='en'>
        <Router>
          <Fragment>
            <CookiesProvider>
              <Header cookies={this.props.cookies} />
            </CookiesProvider>
            <section className="container">
              <Switch>
                <Route exact path="/:lang(pl|fr|)" component={Home} />
                <Route path=":lang(/pl|/fr|)/features" component={Feature} />
                <Route path=":lang(/pl|/fr|)/privacy-policy" component={PrivacyPolicy} />
                <Route path=":lang(/pl|/fr|)/roadmap" component={Roadmap} />
              </Switch>
            </section>
            <Footer />
          </Fragment>
        </Router>
      </I18nProvider>
    );
  }
}

export default App;