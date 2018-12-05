import { Omit } from "@material-ui/core";
import { storiesOf } from "@storybook/react";
import * as React from "react";

import * as placeholderImage from "../../../../images/placeholder60x60.png";
import OrderFulfillmentDialog, {
  OrderFulfillmentDialogProps
} from "../../../orders/components/OrderFulfillmentDialog";
import { order as orderFixture } from "../../../orders/fixtures";
import Decorator from "../../Decorator";

const order = orderFixture(placeholderImage);

const props: Omit<OrderFulfillmentDialogProps, "classes"> = {
  confirmButtonState: "default",
  lines: order.lines,
  onClose: undefined,
  onSubmit: undefined,
  open: true
};

storiesOf("Orders / OrderFulfillmentDialog", module)
  .addDecorator(Decorator)
  .add("default", () => <OrderFulfillmentDialog {...props} />);
