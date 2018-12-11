import { storiesOf } from "@storybook/react";
import * as React from "react";

import OrderPaymentVoidDialog from "../../../orders/components/OrderPaymentVoidDialog";
import Decorator from "../../Decorator";

storiesOf("Orders / OrderPaymentVoidDialog", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <OrderPaymentVoidDialog
      confirmButtonState="default"
      open={true}
      onConfirm={undefined}
      onClose={undefined}
    />
  ));
