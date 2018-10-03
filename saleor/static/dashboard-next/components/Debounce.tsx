import * as React from "react";

export interface DebounceProps {
  change: (event: React.ChangeEvent<any>) => void;
  children:
    | ((
        props: (event: React.ChangeEvent<any>) => void
      ) => React.ReactElement<any>)
    | React.ReactNode;
  submit: (event: React.FormEvent<any>) => void;
}
export interface DebounceState {
  timer: any | null;
}

export class Debounce extends React.Component<DebounceProps, DebounceState> {
  state: DebounceState = {
    timer: null
  };

  handleChange = (event: React.ChangeEvent<any>) => {
    const { timer } = this.state;
    if (timer) {
      clearTimeout(timer);
    }
    this.setState({
      timer: setTimeout(this.props.submit, 200)
    });
    this.props.change(event);
  };

  render() {
    const { children } = this.props;
    if (typeof children === "function") {
      return children(this.handleChange);
    }
    return children;
  }
}
export default Debounce;
