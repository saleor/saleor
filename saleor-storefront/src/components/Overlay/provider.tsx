import * as React from "react";
import { RouteComponentProps, withRouter } from "react-router";
import {
  InnerOverlayContextInterface,
  OverlayContext,
  OverlayContextInterface,
  OverlayTheme,
  OverlayType
} from "./context";

class Provider extends React.Component<
  RouteComponentProps<{}>,
  OverlayContextInterface
> {
  notificationCloseDelay = 2500;
  constructor(props) {
    super(props);
    this.state = {
      context: null,
      hide: this.hide,
      show: this.show,
      theme: null,
      type: null,
    };
  }

  componentDidUpdate(prevProps) {
    if (
      this.props.location.pathname !== prevProps.location.pathname &&
      this.state.type !== OverlayType.message
    ) {
      this.hide();
    }
  }

  show = (
    type: OverlayType,
    theme?: OverlayTheme,
    context?: InnerOverlayContextInterface
  ) => {
    this.setState({ type, theme, context });
    document.body.style.overflow = type !== OverlayType.message ? "hidden" : "";
    if (type === OverlayType.message) {
      setTimeout(this.hide, this.notificationCloseDelay);
    }
  };

  hide = () => {
    this.setState({ type: null });
    document.body.style.overflow = "";
  };

  render() {
    return (
      <OverlayContext.Provider value={this.state}>
        {this.props.children}
      </OverlayContext.Provider>
    );
  }
}

export default withRouter(Provider);
