import * as React from "react";

interface MenuToggleProps {
  ariaOwns?: string;
  children:
    | ((
        props: {
          anchor: HTMLElement;
          actions: {
            open: (event: React.MouseEvent<any>) => void;
            close: () => void;
          };
        }
      ) => React.ReactElement<any>)
    | React.ReactNode;
}

interface MenuToggleState {
  anchor: HTMLElement | null;
}

class MenuToggle extends React.Component<MenuToggleProps, MenuToggleState> {
  state = {
    anchor: null
  };

  handleClick = (event: React.MouseEvent<any>) => {
    this.setState({ anchor: event.currentTarget });
  };

  handleClose = () => {
    this.setState({ anchor: null });
  };

  render() {
    const { children } = this.props;
    const { anchor } = this.state;

    if (typeof children === "function") {
      return children({
        actions: { open: this.handleClick, close: this.handleClose },
        anchor
      });
    }
    return children;
  }
}

export default MenuToggle;
