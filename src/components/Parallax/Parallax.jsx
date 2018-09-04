import React, { Component } from 'react';

class Parallax extends Component {

  constructor(props) {
    super(props);
    this.state = { 
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
    const bodyRect = document.body.getBoundingClientRect();
    const parallaxRect = this.refs.parallax.getBoundingClientRect();
    const offset = bodyRect.top - parallaxRect.top;
    const positionValue = Math.round(offset * this.props.speed);

    const backgroundPosition = '0 0, 50% ' + positionValue + 'px';
    this.refs.parallax.style.backgroundPosition = backgroundPosition;
    
    this.setState({
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
      <div id="parallax" ref="parallax">
        {this.props.children}
      </div>
    );
  };
}

export default Parallax;
