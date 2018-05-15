import { storiesOf } from "@storybook/react";
import * as React from "react";

import OrderAddressEditDialog from "../../../orders/components/OrderAddressEditDialog";
import {
  order as orderFixture,
  prefixes,
  countries
} from "../../../orders/fixtures";
import Decorator from "../../Decorator";

const order = orderFixture("");

storiesOf("Orders / OrderAddressEditDialog", module)
  .addDecorator(Decorator)
  .add("shipping address", () => (
    <OrderAddressEditDialog
      open={true}
      variant="shipping"
      data={order.shippingAddress}
      onChange={() => {}}
      countries={countries}
      prefixes={prefixes}
    />
  ))
  .add("billing address", () => (
    <OrderAddressEditDialog
      open={true}
      variant="billing"
      data={order.billingAddress}
      onChange={() => {}}
      prefixes={prefixes}
      countries={countries}
    />
  ));
