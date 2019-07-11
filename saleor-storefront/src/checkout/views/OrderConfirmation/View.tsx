import "./scss/index.scss";

import React from "react";
import { generatePath, Link, RouteComponentProps } from "react-router-dom";

import { Button, NotFound } from "../../../components";
import { BASE_URL } from "../../../core/config";
import { guestOrderDetailsUrl } from "../../../routes";
import { userOrderDetailsUrl } from "../../../userAccount/routes";

const View: React.FC<RouteComponentProps> = ({
  history: {
    location: { state },
  },
}) => {
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
        Thank you for <br /> your order
      </h3>
      <p className="order-confirmation__info">
        We’ve emailed you a order confirmation
        <br />
        and we’ll notify you when order has
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
};

export default View;
