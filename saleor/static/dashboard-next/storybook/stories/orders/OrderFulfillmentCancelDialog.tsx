import { storiesOf } from "@storybook/react";
import * as React from "react";

import OrderFulfillmentCancelDialog from "../../../orders/components/OrderFulfillmentCancelDialog";
import Decorator from "../../Decorator";

storiesOf("Orders / OrderFulfillmentCancelDialog", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <OrderFulfillmentCancelDialog
      open={true}
      id="123"
      onConfirm={undefined}
      onClose={undefined}
    />
  ));
