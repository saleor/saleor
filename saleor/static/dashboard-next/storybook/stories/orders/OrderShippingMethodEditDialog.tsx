import { storiesOf } from "@storybook/react";
import * as React from "react";

import OrderShippingMethodEditDialog from "../../../orders/components/OrderShippingMethodEditDialog";
import { order as orderFixture } from "../../../orders/fixtures";
import Decorator from "../../Decorator";

const order = orderFixture("");

storiesOf("Orders / OrderShippingMethodEditDialog", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <OrderShippingMethodEditDialog
      confirmButtonState="default"
      onClose={undefined}
      onSubmit={undefined}
      open={true}
      shippingMethod={null}
      shippingMethods={order.availableShippingMethods}
    />
  ));
