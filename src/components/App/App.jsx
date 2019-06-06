import React, { Component, Fragment } from "react";
import { BrowserRouter as Router, Route, Link, Switch } from "react-router-dom";
import { CookiesProvider } from "react-cookie";
import {
  Home,
  Header,
  Footer,
  PrivacyPolicy,
  Roadmap,
  Feature,
  ScrollToTop
} from "..";
import css from "./css/index.css";

class App extends Component {
  render() {
    return (
      <Router>
        <ScrollToTop>
          <Fragment>
            <CookiesProvider>
              <Header cookies={this.props.cookies} />
            </CookiesProvider>
            <section className="borderFrame">
              <Switch>
                <Route exact path="/" component={Home} />
                <Route path="/features" component={Feature} />
                <Route
                  path="/privacy-policy-terms-and-conditions"
                  component={PrivacyPolicy}
                />
                <Route path="/roadmap" component={Roadmap} />
              </Switch>
            </section>
            <Footer />
          </Fragment>
        </ScrollToTop>
      </Router>
    );
  }
}

export default App;
