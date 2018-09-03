import React, { Component } from 'react';

class Parallax extends Component {

  constructor(props) {
    super(props);
    this.state = { 
      parallaxStyle: {
        backgroundPosition: '50% 0'
      },
      scheduledAnimationFrame: false
    }
  }

  componentDidMount() {
    window.addEventListener('scroll', this.handleScroll.bind(this), true);
  }
  
  componentWillUnmount() {
    window.addEventListener('scroll', this.handleScroll.bind(this), false);
  }

  updateBackgroundPosition() {

    const windowYOffset = document.body.scrollTop;
    const backgroundPosition = '50% ' + (windowYOffset * this.props.speed) + 'px';
    this.setState({
      parallaxStyle: {backgroundPosition: backgroundPosition},
      scheduledAnimationFrame: false
    });

  }
  
  handleScroll(event) {
    if (this.state.scheduledAnimationFrame){
      return;
    }
    this.setState({ scheduledAnimationFrame: true  });
    requestAnimationFrame(() => {this.updateBackgroundPosition()});
  }

  render() {
    return (
      <div id="parallax" style={this.state.parallaxStyle}>
        {this.props.children}
      </div>
    );
  };
}

export default Parallax;
