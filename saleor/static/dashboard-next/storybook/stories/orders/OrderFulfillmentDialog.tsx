import { storiesOf } from "@storybook/react";
import * as React from "react";

import * as placeholderImage from "../../../../images/placeholder60x60.png";
import OrderFulfillmentDialog from "../../../orders/components/OrderFulfillmentDialog";
import { order as orderFixture } from "../../../orders/fixtures";
import Decorator from "../../Decorator";

const order = orderFixture(placeholderImage);

storiesOf("Orders / OrderFulfillmentDialog", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <OrderFulfillmentDialog
      open={true}
      products={order.products}
      onChange={undefined}
      data={{}}
    />
  ));
