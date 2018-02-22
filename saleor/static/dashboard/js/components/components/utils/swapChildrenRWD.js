import React, { Component, Fragment } from 'react';
import PropTypes from 'prop-types';
import _ from 'lodash';

class SwapChildrenRWD extends Component {
  static propTypes = {
    up: PropTypes.number,
    down: PropTypes.number
  };
  static defaultProps = {
    up: 0,
    down: Infinity
  };

  constructor(props) {
    super(props);
    this.state = { order: _.inRange(window.innerWidth, props.up, props.down) };
    this.updateDimensions = this.updateDimensions.bind(this);
  }

  updateDimensions() {
    this.setState({ order: _.inRange(window.innerWidth, this.props.up, this.props.down) });
  }

  componentWillMount() {
    this.updateDimensions();
  }

  componentDidMount() {
    window.addEventListener('resize', this.updateDimensions);
  }

  componentWillUnmount() {
    window.removeEventListener('resize', this.updateDimensions);
  }

  render() {
    const children = this.state.order ? this.props.children.reverse() : this.props.children;
    return (
      <Fragment>
        {children}
      </Fragment>
    )
  }
}

export default SwapChildrenRWD;
