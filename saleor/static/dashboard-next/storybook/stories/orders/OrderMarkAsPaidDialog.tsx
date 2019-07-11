import { storiesOf } from "@storybook/react";
import React from "react";

import OrderMarkAsPaidDialog, {
  OrderMarkAsPaidDialogProps
} from "../../../orders/components/OrderMarkAsPaidDialog";
import Decorator from "../../Decorator";

const props: OrderMarkAsPaidDialogProps = {
  confirmButtonState: "default",
  onClose: () => undefined,
  onConfirm: () => undefined,
  open: true
};

storiesOf("Orders / OrderMarkAsPaidDialog", module)
  .addDecorator(Decorator)
  .add("default", () => <OrderMarkAsPaidDialog {...props} />);
