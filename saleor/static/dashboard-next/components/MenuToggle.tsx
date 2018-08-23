import * as React from "react";

interface MenuToggleProps {
  ariaOwns?: string;
  children:
    | ((
        props: {
          actions: {
            open: (event: React.MouseEvent<any>) => void;
            close: () => void;
          };
          open: boolean;
        }
      ) => React.ReactElement<any>)
    | React.ReactNode;
}

interface MenuToggleState {
  open: boolean;
}

class MenuToggle extends React.Component<MenuToggleProps, MenuToggleState> {
  state = {
    open: false
  };

  handleClick = (event: React.MouseEvent<any>) => {
    this.setState({ open: true });
  };

  handleClose = () => {
    this.setState({ open: false });
  };

  render() {
    const { children } = this.props;
    const { open } = this.state;

    if (typeof children === "function") {
      return children({
        actions: { open: this.handleClick, close: this.handleClose },
        open
      });
    }
    return children;
  }
}

export default MenuToggle;
