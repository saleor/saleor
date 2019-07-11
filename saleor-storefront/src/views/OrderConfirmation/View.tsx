import "./scss/index.scss";

import React from "react";
import { generatePath, Link, RouteComponentProps } from "react-router-dom";

import { Button, NotFound } from "../../components";
import { BASE_URL } from "../../core/config";
import { guestOrderDetailsUrl } from "../../routes";
import { userOrderDetailsUrl } from "../../userAccount/routes";

class View extends React.PureComponent<RouteComponentProps> {
  /**
   * Clear router state on leaving the page to ensure view becames unavailable
   * after leaving.
   */
  componentWillUnmount() {
    const {
      history: { location, replace },
    } = this.props;
    const { state } = location;

    if (state) {
      replace({ ...location, state: undefined });
    }
  }

  render() {
    const {
      history: {
        location: { state },
      },
    } = this.props;

    /**
     * Token or id is passed from review page via router state. If it is not
     * present page should not be displayed.
     */
    if (!state) {
      return <NotFound />;
    }

    const { token, id } = state;
    const guest = !id;
    const orderDetailsRef = guest
      ? generatePath(guestOrderDetailsUrl, { token })
      : generatePath(userOrderDetailsUrl, { id });

    return (
      <div className="order-confirmation">
        <h3>
          Thank you for <br /> your order!
        </h3>
        <p className="order-confirmation__info">
          We’ve emailed you an order confirmation.
          <br />
          We’ll notify you when the order has been
          <br />
          shipped.
        </p>
        <div className="order-confirmation__actions">
          <Link to={BASE_URL}>
            <Button secondary>Continue Shopping</Button>
          </Link>
          <Link to={orderDetailsRef}>
            <Button>Order Details</Button>
          </Link>
        </div>
      </div>
    );
  }
}

export default View;
