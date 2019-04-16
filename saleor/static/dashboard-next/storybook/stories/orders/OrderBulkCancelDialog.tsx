import { storiesOf } from "@storybook/react";
import * as React from "react";

import OrderBulkCancelDialog, {
  OrderBulkCancelDialogProps
} from "../../../orders/components/OrderBulkCancelDialog";
import Decorator from "../../Decorator";

const props: OrderBulkCancelDialogProps = {

};

storiesOf("Orders / OrderBulkCancelDialog", module)
  .addDecorator(Decorator)
  .add("default", () => <OrderBulkCancelDialog {...props} />);
