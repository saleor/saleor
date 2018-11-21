import { storiesOf } from "@storybook/react";
import * as React from "react";

import OrderDraftFinalize, { OrderDraftFinalizeProps } from "../../../orders/components/OrderDraftFinalize";
import Decorator from "../../Decorator";

const props:OrderDraftFinalizeProps = {

}

storiesOf("Orders / OrderDraftFinalize", module)
  .addDecorator(Decorator)
  .add("default", () => <OrderDraftFinalize {...OrderDraftFinalizeProps} />)
  .add("other", () => <OrderDraftFinalize {...OrderDraftFinalizeProps} />);
