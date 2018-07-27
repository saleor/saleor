import React, { Component } from 'react';

class Layout extends Component {
  constructor(props) {
    super(props);
  }

  render() {
    console.log(this.props);
    return (
      <div className="layout">Start</div>
    );
  }
}

export default Layout;