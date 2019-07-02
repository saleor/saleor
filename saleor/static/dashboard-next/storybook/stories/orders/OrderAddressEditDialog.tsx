import { storiesOf } from "@storybook/react";
import React from "react";

import { transformAddressToForm } from "../../../misc";
import OrderAddressEditDialog from "../../../orders/components/OrderAddressEditDialog";
import { countries, order as orderFixture } from "../../../orders/fixtures";
import Decorator from "../../Decorator";

const order = orderFixture("");

storiesOf("Orders / OrderAddressEditDialog", module)
  .addDecorator(Decorator)
  .add("shipping address", () => (
    <OrderAddressEditDialog
      confirmButtonState="default"
      address={transformAddressToForm(order.shippingAddress)}
      countries={countries}
      errors={[]}
      onClose={() => undefined}
      onConfirm={() => undefined}
      open={true}
      variant="shipping"
    />
  ))
  .add("billing address", () => (
    <OrderAddressEditDialog
      confirmButtonState="default"
      address={transformAddressToForm(order.billingAddress)}
      countries={countries}
      errors={[]}
      onClose={() => undefined}
      onConfirm={() => undefined}
      open={true}
      variant="billing"
    />
  ));
