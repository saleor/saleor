import { storiesOf } from "@storybook/react";
import * as React from "react";

import { transformAddressToForm } from "../../../misc";
import OrderAddressEditDialog from "../../../orders/components/OrderAddressEditDialog";
import { countries, order as orderFixture } from "../../../orders/fixtures";
import Decorator from "../../Decorator";

const order = orderFixture("");

storiesOf("Orders / OrderAddressEditDialog", module)
  .addDecorator(Decorator)
  .add("shipping address", () => (
    <OrderAddressEditDialog
      errors={{}}
      open={true}
      variant="shipping"
      data={transformAddressToForm(order.shippingAddress)}
      onChange={undefined}
      countries={countries}
    />
  ))
  .add("billing address", () => (
    <OrderAddressEditDialog
      errors={{}}
      open={true}
      variant="billing"
      data={transformAddressToForm(order.billingAddress)}
      onChange={undefined}
      countries={countries}
    />
  ));
