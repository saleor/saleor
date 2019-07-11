import * as React from "react";

import classNames from "classnames";
import ReactCSSTransitionGroup from "react-addons-css-transition-group";
import { Button, ButtonProps } from "..";

interface AddToCartButtonState {
  animate: boolean;
  disabled: boolean;
}

class AddToCartButton extends React.PureComponent<
  ButtonProps,
  AddToCartButtonState
> {
  state = { animate: false, disabled: false };
  animationTimeout = 800;
  timeout;

  handleAnimation = (evt: React.MouseEvent<HTMLButtonElement>) => {
    if (!this.state.disabled) {
      this.props.onClick(evt);

      this.setState({ animate: true, disabled: true }, () => {
        this.timeout = setTimeout(() => {
          this.setState({ animate: false }, () => {
            this.timeout = setTimeout(
              () => this.setState({ disabled: false }),
              this.animationTimeout
            );
          });
        }, this.animationTimeout);
      });
    }
  };

  componentWillUnmount() {
    clearTimeout(this.timeout);
  }

  render() {
    const { animate } = this.state;

    return (
      <Button
        {...this.props}
        className={classNames(this.props.className, {
          "product-description__action--fade": animate,
        })}
        onClick={this.handleAnimation}
      >
        <ReactCSSTransitionGroup
          transitionName="product-description__action--fade"
          transitionEnterTimeout={this.animationTimeout}
          transitionLeaveTimeout={this.animationTimeout}
        >
          {animate ? (
            <span key="text">Added</span>
          ) : (
            <span key="children">{this.props.children}</span>
          )}
        </ReactCSSTransitionGroup>
      </Button>
    );
  }
}

export default AddToCartButton;
