import { storiesOf } from "@storybook/react";
import * as React from "react";

import OrderDraftCancelDialog, { OrderDraftCancelDialogProps } from "../../../orders/components/OrderDraftCancelDialog";
import Decorator from "../../Decorator";

const props:OrderDraftCancelDialogProps = {

}

storiesOf("Orders / OrderDraftCancelDialog", module)
  .addDecorator(Decorator)
  .add("default", () => <OrderDraftCancelDialog {...OrderDraftCancelDialogProps} />)
  .add("other", () => <OrderDraftCancelDialog {...OrderDraftCancelDialogProps} />);
