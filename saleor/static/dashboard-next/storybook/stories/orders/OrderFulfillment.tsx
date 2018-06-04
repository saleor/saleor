import { storiesOf } from "@storybook/react";
import * as React from "react";

import OrderFulfillment from "../../../orders/components/OrderFulfillment";
import Decorator from "../../Decorator";

storiesOf("Orders / OrderFulfillment", module)
  .addDecorator(Decorator)
  .add("default", () => <OrderFulfillment />)
  .add("other", () => <OrderFulfillment />);
