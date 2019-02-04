import * as React from "react";

export interface ToggleFuncs {
  disable();
  enable();
  toggle();
}
export type ToggleChildren = (
  value: boolean,
  funcs: ToggleFuncs
) => React.ReactElement<any>;

interface ToggleProps {
  children: ToggleChildren;
  initial?: boolean;
}

interface ToggleState {
  value: boolean;
}

class Toggle extends React.Component<ToggleProps, ToggleState> {
  state = {
    value: this.props.initial !== undefined ? this.props.initial : false
  };

  disable = () => this.setState({ value: false });
  enable = () => this.setState({ value: true });
  toggle = () => this.setState(({ value }) => ({ value: !value }));

  render() {
    const { children } = this.props;
    return children(this.state.value, {
      disable: this.disable,
      enable: this.enable,
      toggle: this.toggle
    });
  }
}

export default Toggle;
