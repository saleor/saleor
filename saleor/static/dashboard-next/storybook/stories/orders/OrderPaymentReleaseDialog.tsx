import { storiesOf } from "@storybook/react";
import * as React from "react";

import OrderPaymentReleaseDialog from "../../../orders/components/OrderPaymentReleaseDialog";
import Decorator from "../../Decorator";

storiesOf("Orders / OrderPaymentReleaseDialog", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <OrderPaymentReleaseDialog
      open={true}
      onConfirm={undefined}
      onClose={undefined}
    />
  ));
