import { storiesOf } from "@storybook/react";
import * as React from "react";

import { transformAddressToForm } from "../../../orders";
import OrderAddressEditDialog from "../../../orders/components/OrderAddressEditDialog";
import {
  countries,
  order as orderFixture,
  prefixes
} from "../../../orders/fixtures";
import Decorator from "../../Decorator";

const order = orderFixture("");

storiesOf("Orders / OrderAddressEditDialog", module)
  .addDecorator(Decorator)
  .add("shipping address", () => (
    <OrderAddressEditDialog
      open={true}
      variant="shipping"
      data={transformAddressToForm(order.shippingAddress)}
      onChange={undefined}
      countries={countries}
      prefixes={prefixes}
    />
  ))
  .add("billing address", () => (
    <OrderAddressEditDialog
      open={true}
      variant="billing"
      data={transformAddressToForm(order.billingAddress)}
      onChange={undefined}
      prefixes={prefixes}
      countries={countries}
    />
  ));
