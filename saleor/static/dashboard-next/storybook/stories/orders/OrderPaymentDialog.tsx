import { storiesOf } from "@storybook/react";
import * as React from "react";

import OrderPaymentDialog from "../../../orders/components/OrderPaymentDialog";
import Decorator from "../../Decorator";

storiesOf("Orders / OrderPaymentDialog", module)
  .addDecorator(Decorator)
  .add("capture payment", () => (
    <OrderPaymentDialog
      confirmButtonState="default"
      initial={0}
      variant="capture"
      open={true}
      onClose={undefined}
      onSubmit={undefined}
    />
  ))
  .add("refund payment", () => (
    <OrderPaymentDialog
      confirmButtonState="default"
      initial={0}
      variant="refund"
      open={true}
      onClose={undefined}
      onSubmit={undefined}
    />
  ));
