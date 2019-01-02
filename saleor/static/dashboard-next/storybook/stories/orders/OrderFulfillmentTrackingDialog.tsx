import { storiesOf } from "@storybook/react";
import * as React from "react";

import OrderFulfillmentTrackingDialog from "../../../orders/components/OrderFulfillmentTrackingDialog";
import Decorator from "../../Decorator";

storiesOf("Orders / OrderFulfillmentTrackingDialog", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <OrderFulfillmentTrackingDialog
      confirmButtonState="default"
      open={true}
      trackingNumber="21kn7526v1"
      onConfirm={undefined}
      onClose={undefined}
    />
  ));
