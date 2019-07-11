import { mediumScreen } from "../../../globalStyles/scss/variables.scss";
import "./scss/index.scss";

import React from "react";
import Media from "react-media";

import { CartContext } from "../../../components/CartProvider/context";
import { Checkout } from "../../types/Checkout";
import Cart from "./Cart";

const Wrapper: React.FC<{ checkout?: Checkout }> = ({ children, checkout }) => (
  <div className="checkout__grid">
    <div className={"checkout__grid__content"}>{children}</div>
    <Media
      query={{ minWidth: mediumScreen }}
      render={() => (
        <div className="checkout__grid__cart-summary">
          <CartContext.Consumer>
            {cart => <Cart cart={cart} checkout={checkout} />}
          </CartContext.Consumer>
        </div>
      )}
    />
  </div>
);

export default Wrapper;
