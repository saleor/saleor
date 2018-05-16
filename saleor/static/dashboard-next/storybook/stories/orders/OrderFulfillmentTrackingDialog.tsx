import { storiesOf } from "@storybook/react";
import * as React from "react";

import OrderFulfillmentTrackingDialog from "../../../orders/components/OrderFulfillmentTrackingDialog";
import Decorator from "../../Decorator";

storiesOf("Orders / OrderFulfillmentTrackingDialog", module)
  .addDecorator(Decorator)
  .add("add", () => (
    <OrderFulfillmentTrackingDialog
      open={true}
      variant="add code"
      onChange={() => {}}
      onConfirm={() => {}}
      onClose={() => {}}
      trackingCode="123"
    />
  ))
  .add("edit", () => (
    <OrderFulfillmentTrackingDialog
      open={true}
      variant="edit code"
      onChange={() => {}}
      onConfirm={() => {}}
      onClose={() => {}}
      trackingCode="123"
    />
  ));
