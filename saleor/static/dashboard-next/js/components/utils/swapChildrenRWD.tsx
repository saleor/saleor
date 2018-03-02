import * as React from "react";
import { Component, Fragment } from "react";

interface SwapChildrenProps {
  down?: number;
  up?: number;
}

interface SwapChildrenState {
  order: boolean;
}

export class SwapChildrenRWD extends Component<
  SwapChildrenProps,
  SwapChildrenState
> {
  static defaultProps = {
    down: Infinity,
    up: 0
  };
  state = {
    order:
      window.innerWidth >= this.props.up && window.innerWidth < this.props.down
  };

  constructor(props) {
    super(props);
    this.updateDimensions = this.updateDimensions.bind(this);
  }

  updateDimensions() {
    const order =
      window.innerWidth >= this.props.up && window.innerWidth < this.props.down;
    if (order !== this.state.order) {
      this.setState({ order });
    }
  }

  componentDidMount() {
    this.updateDimensions();
    window.addEventListener("resize", this.updateDimensions);
  }

  componentWillUnmount() {
    window.removeEventListener("resize", this.updateDimensions);
  }

  render() {
    // This is kind of a hack - Array.prototype.reverse() operates on variable state instead of copying it.
    // So, since this.props is read-only, we need to manually copy and reverse Array.
    const children = this.state.order
      ? [].concat(this.props.children).reverse()
      : this.props.children;
    return <Fragment>{children}</Fragment>;
  }
}
