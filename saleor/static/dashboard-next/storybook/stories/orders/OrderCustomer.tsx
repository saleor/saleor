import { storiesOf } from "@storybook/react";
import * as React from "react";

import OrderCustomer, {
  OrderCustomerProps
} from "../../../orders/components/OrderCustomer";
import { order as orderFixture } from "../../../orders/fixtures";
import Decorator from "../../Decorator";

const order = orderFixture("");

const props: OrderCustomerProps = {
  onBillingAddressEdit: undefined,
  onCustomerEditClick: undefined,
  onShippingAddressEdit: undefined,
  order
};

storiesOf("Orders / OrderCustomer", module)
  .addDecorator(Decorator)
  .add("when loading data", () => (
    <OrderCustomer {...props} order={undefined} />
  ))
  .add("when loaded data", () => <OrderCustomer {...props} />)
  .add("with different addresses", () => (
    <OrderCustomer
      {...props}
      order={{
        ...order,
        shippingAddress: { ...order.shippingAddress, id: "a2" }
      }}
    />
  ));
