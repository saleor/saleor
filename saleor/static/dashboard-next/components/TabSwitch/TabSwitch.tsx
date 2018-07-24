import * as React from "react";

interface TabSwitchProps {
  children:
    | ((
        props: {
          currentTab: string;
          handleChange: (event: React.ChangeEvent<any>, value: string) => void;
        }
      ) => React.ReactElement<any>)
    | React.ReactNode;
  initial: string;
}
interface TabSwitchState {
  value: string;
}

class TabSwitch extends React.Component<TabSwitchProps, TabSwitchState> {
  constructor(props) {
    super(props);
    this.state = {
      value: this.props.initial
    };
  }

  handleChange = (event: React.ChangeEvent<any>, value: string) =>
    this.setState({ value });

  render() {
    const { children } = this.props;
    if (typeof children === "function") {
      return children({
        currentTab: this.state.value,
        handleChange: this.handleChange
      });
    }
    return children;
  }
}
export default TabSwitch;
