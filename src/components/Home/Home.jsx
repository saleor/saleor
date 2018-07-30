import React, { Component } from 'react';

import css from './home.css';

class Home extends Component {
  constructor(props) {
    super(props);
  }

  render() {
    return (
      <div id="home">
        <section className="hero">
          <div className="plane">
            <h1>A graphql-first ecommerce <span class="primaryColor">platform for perfectionists</span></h1>
            <a href="#" className="btn btn-secondary">See demo</a>
            <a href="#" className="btn btn-primary">Brief us</a>
          </div>
        </section>
      </div>
    );
  }
}

export default Home;