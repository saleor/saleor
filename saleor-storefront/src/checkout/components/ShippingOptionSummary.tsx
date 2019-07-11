import * as React from "react";

import { Checkout_shippingMethod } from "../types/Checkout";

const ShippingOptionSummary: React.FC<{
  shippingMethod: Checkout_shippingMethod;
}> = ({ shippingMethod: { name, price } }) => (
  <p>{`${name} | +${price.localized}`}</p>
);

export default ShippingOptionSummary;
