import { storiesOf } from "@storybook/react";
import * as React from "react";

import OrderDraftFinalize, {
  OrderDraftFinalizeDialogProps
} from "../../../orders/components/OrderDraftFinalizeDialog";
import Decorator from "../../Decorator";

const props: OrderDraftFinalizeDialogProps = {
  confirmButtonState: "default",
  onClose: () => undefined,
  onConfirm: () => undefined,
  open: true,
  orderNumber: "5",
  warnings: []
};

storiesOf("Orders / OrderDraftFinalizeDialog", module)
  .addDecorator(Decorator)
  .add("default", () => <OrderDraftFinalize {...props} />)
  .add("with warnings", () => (
    <OrderDraftFinalize
      {...props}
      warnings={["no-shipping-method", "no-shipping", "no-billing", "no-user"]}
    />
  ));
