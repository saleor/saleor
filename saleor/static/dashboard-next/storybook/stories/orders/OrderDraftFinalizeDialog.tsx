import { storiesOf } from "@storybook/react";
import * as React from "react";

import OrderDraftFinalize, {
  OrderDraftFinalizeDialogProps
} from "../../../orders/components/OrderDraftFinalizeDialog";
import Decorator from "../../Decorator";

const props: OrderDraftFinalizeDialogProps = {
  onClose: () => undefined,
  onConfirm: () => undefined,
  open: true,
  orderNumber: "5"
};

storiesOf("Orders / OrderDraftFinalizeDialog", module)
  .addDecorator(Decorator)
  .add("default", () => <OrderDraftFinalize {...props} />);
