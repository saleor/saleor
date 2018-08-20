import { storiesOf } from "@storybook/react";
import * as React from "react";

import OrderCustomer from "../../../orders/components/OrderCustomer";
import { order } from "../../../orders/fixtures";
import Decorator from "../../Decorator";

const differentAddress = { ...order("").billingAddress, id: "a2" };

storiesOf("Orders / OrderCustomer", module)
  .addDecorator(Decorator)
  .add("when loading data", () => <OrderCustomer />)
  .add("when loaded data", () => (
    <OrderCustomer
      client={order("").client}
      shippingAddress={order("").shippingAddress}
      billingAddress={order("").billingAddress}
      onBillingAddressEdit={undefined}
      onShippingAddressEdit={undefined}
    />
  ))
  .add("with different addresses", () => (
    <OrderCustomer
      client={order("").client}
      shippingAddress={order("").shippingAddress}
      billingAddress={differentAddress}
      onBillingAddressEdit={undefined}
      onShippingAddressEdit={undefined}
    />
  ));
