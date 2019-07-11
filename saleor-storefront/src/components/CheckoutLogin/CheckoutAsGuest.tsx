import React from "react";

import { Link } from "react-router-dom";
import { Button, OverlayTheme, OverlayType } from "..";
import { OverlayContextInterface } from "../Overlay";

const CheckoutAsGuest: React.FC<{
  overlay: OverlayContextInterface;
  checkoutUrl: string;
}> = ({ overlay, checkoutUrl }) => (
  <div className="checkout-login__guest">
    <h3 className="checkout__header">Continue as a guest</h3>
    <p>
      If you don’t wish to register an account, don’t worry. You can checkout as
      a guest. We care about you just as much as any registered user.
    </p>
    <Link to={checkoutUrl}>
      <Button>Continue as a guest</Button>
    </Link>

    <p>
      or you can{" "}
      <span
        className="u-link"
        onClick={() => overlay.show(OverlayType.register, OverlayTheme.right)}
      >
        create an account
      </span>
    </p>
  </div>
);

export default CheckoutAsGuest;
