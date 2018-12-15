import { Omit } from "@material-ui/core";
import { storiesOf } from "@storybook/react";
import * as React from "react";

import OrderCustomer, {
  OrderCustomerProps
} from "../../../orders/components/OrderCustomer";
import { clients, order as orderFixture } from "../../../orders/fixtures";
import Decorator from "../../Decorator";

const order = orderFixture("");

const props: Omit<OrderCustomerProps, "classes"> = {
  canEditAddresses: false,
  canEditCustomer: true,
  fetchUsers: () => undefined,
  onBillingAddressEdit: undefined,
  onCustomerEdit: undefined,
  onShippingAddressEdit: undefined,
  order,
  users: clients
};

storiesOf("Orders / OrderCustomer", module)
  .addDecorator(Decorator)
  .add("default", () => <OrderCustomer {...props} />)
  .add("loading", () => <OrderCustomer {...props} order={undefined} />)
  .add("with different addresses", () => (
    <OrderCustomer
      {...props}
      order={{
        ...order,
        shippingAddress: { ...order.shippingAddress, id: "a2" }
      }}
    />
  ))
  .add("editable", () => (
    <OrderCustomer {...props} canEditAddresses={true} canEditCustomer={true} />
  ));
