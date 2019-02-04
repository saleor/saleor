import { storiesOf } from "@storybook/react";
import * as React from "react";

import OrderCancelDialog from "../../../orders/components/OrderCancelDialog";
import Decorator from "../../Decorator";

storiesOf("Orders / OrderCancelDialog", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <OrderCancelDialog
      confirmButtonState="default"
      open={true}
      number="123"
      onSubmit={undefined}
      onClose={undefined}
    />
  ));
