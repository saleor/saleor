import React, { Component } from 'react';

class Home extends Component {
  constructor(props) {
    super(props);
  }

  render() {
    console.log(this.props);
    return (
      <div className="home">
          Start
      </div>
    );
  }
}

export default Home;