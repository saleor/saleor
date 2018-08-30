import * as React from "react";

interface ToggleProps {
  children:
    | ((
        value: boolean,
        funcs: { disable(); enable(); toggle() }
      ) => React.ReactElement<any>)
    | React.ReactNode;
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
    if (typeof children === "function") {
      return children(this.state.value, {
        disable: this.disable,
        enable: this.enable,
        toggle: this.toggle
      });
    }
    if (React.Children.count(children) > 0) {
      return React.Children.only(children);
    }
    return null;
  }
}

export default Toggle;
