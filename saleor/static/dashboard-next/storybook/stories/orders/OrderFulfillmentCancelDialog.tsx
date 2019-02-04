import { storiesOf } from "@storybook/react";
import * as React from "react";

import OrderFulfillmentCancelDialog from "../../../orders/components/OrderFulfillmentCancelDialog";
import Decorator from "../../Decorator";

storiesOf("Orders / OrderFulfillmentCancelDialog", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <OrderFulfillmentCancelDialog
      confirmButtonState="default"
      open={true}
      onConfirm={undefined}
      onClose={undefined}
    />
  ));
