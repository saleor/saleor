import { storiesOf } from "@storybook/react";
import React from "react";

import OrderBulkCancelDialog, {
  OrderBulkCancelDialogProps
} from "../../../orders/components/OrderBulkCancelDialog";
import Decorator from "../../Decorator";

const props: OrderBulkCancelDialogProps = {
  confirmButtonState: "default",
  numberOfOrders: "10",
  onClose: () => undefined,
  onConfirm: () => undefined,
  open: true
};

storiesOf("Orders / OrderBulkCancelDialog", module)
  .addDecorator(Decorator)
  .add("default", () => <OrderBulkCancelDialog {...props} />);
