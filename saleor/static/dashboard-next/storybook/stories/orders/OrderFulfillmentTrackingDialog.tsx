import { storiesOf } from "@storybook/react";
import * as React from "react";

import OrderFulfillmentTrackingDialog from "../../../orders/components/OrderFulfillmentTrackingDialog";
import Decorator from "../../Decorator";

storiesOf("Orders / OrderFulfillmentTrackingDialog", module)
  .addDecorator(Decorator)
  .add("add code", () => (
    <OrderFulfillmentTrackingDialog
      open={true}
      variant="add"
      onChange={() => {}}
      onConfirm={() => {}}
      onClose={() => {}}
      trackingCode="123"
    />
  ))
  .add("edit code", () => (
    <OrderFulfillmentTrackingDialog
      open={true}
      variant="edit"
      onChange={() => {}}
      onConfirm={() => {}}
      onClose={() => {}}
      trackingCode="123"
    />
  ));
