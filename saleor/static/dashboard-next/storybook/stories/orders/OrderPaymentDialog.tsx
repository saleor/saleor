import { storiesOf } from "@storybook/react";
import * as React from "react";

import OrderPaymentDialog from "../../../orders/components/OrderPaymentDialog";
import Decorator from "../../Decorator";

storiesOf("Orders / OrderPaymentDialog", module)
  .addDecorator(Decorator)
  .add("capture payment", () => (
    <OrderPaymentDialog
      variant="capture"
      open={true}
      onChange={undefined}
      value={120}
    />
  ))
  .add("refund payment", () => (
    <OrderPaymentDialog
      variant="refund"
      open={true}
      onChange={undefined}
      value={140}
    />
  ));
