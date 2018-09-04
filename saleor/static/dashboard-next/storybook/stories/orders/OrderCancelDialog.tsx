import { storiesOf } from "@storybook/react";
import * as React from "react";

import OrderCancelDialog from "../../../orders/components/OrderCancelDialog";
import Decorator from "../../Decorator";

storiesOf("Orders / OrderCancelDialog", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <OrderCancelDialog
      open={true}
      id="123"
      onConfirm={undefined}
      onClose={undefined}
    />
  ));
