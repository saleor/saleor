import { storiesOf } from "@storybook/react";
import * as React from "react";

import OrderCustomer, {
  OrderCustomerProps
} from "../../../orders/components/OrderCustomer";
import { order } from "../../../orders/fixtures";
import Decorator from "../../Decorator";

const differentAddress = { ...order("").billingAddress, id: "a2" };

const props: OrderCustomerProps = {
  billingAddress: order("").billingAddress,
  customer: order("").user,
  onBillingAddressEdit: undefined,
  onShippingAddressEdit: undefined,
  shippingAddress: order("").shippingAddress
};

storiesOf("Orders / OrderCustomer", module)
  .addDecorator(Decorator)
  .add("when loading data", () => (
    <OrderCustomer {...props} customer={undefined} />
  ))
  .add("when loaded data", () => <OrderCustomer {...props} />)
  .add("with different addresses", () => (
    <OrderCustomer {...props} billingAddress={differentAddress} />
  ));
