import * as React from "react";

import { Checkout } from "../../../checkout/types/Checkout";
import { CartLineInterface } from "../../../components/CartProvider/context";
import { getTotal } from "../../../components/CartProvider/uitls";
import { ShopContext } from "../../../components/ShopProvider/context";
import { maybe } from "../../../core/utils";
import { VariantList } from "../../../views/Product/types/VariantList";

const Subtotal: React.FC<{
  checkout: Checkout | null;
  lines: CartLineInterface[];
  variants?: VariantList;
}> = ({ checkout, lines, variants }) => (
  <ShopContext.Consumer>
    {({ defaultCountry, geolocalization }) => {
      const locale = maybe(
        () => geolocalization.country.code,
        defaultCountry.code
      );
      return (
        <div className="cart-summary__totals">
          <h4>Subtotal</h4>
          <h4>
            {checkout
              ? checkout.subtotalPrice.gross.localized
              : getTotal(variants, lines, locale)}
          </h4>
        </div>
      );
    }}
  </ShopContext.Consumer>
);

export default Subtotal;
