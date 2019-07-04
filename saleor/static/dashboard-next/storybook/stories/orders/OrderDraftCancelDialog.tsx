import { storiesOf } from "@storybook/react";
import React from "react";

import OrderDraftCancelDialog, {
  OrderDraftCancelDialogProps
} from "../../../orders/components/OrderDraftCancelDialog";
import Decorator from "../../Decorator";

const props: OrderDraftCancelDialogProps = {
  confirmButtonState: "default",
  onClose: () => undefined,
  onConfirm: () => undefined,
  open: true,
  orderNumber: "4"
};

storiesOf("Orders / OrderDraftCancelDialog", module)
  .addDecorator(Decorator)
  .add("default", () => <OrderDraftCancelDialog {...props} />);
