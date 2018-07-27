import React, { Component } from 'react';

import Layout from '../Layout';

class Home extends Component {
  constructor(props) {
    super(props);
  }

  render() {
    console.log(this.props);
    return (
      <div className="home">
        <Layout>
          Start
        </Layout>
      </div>
    );
  }
}

export default Home;