import { storiesOf } from "@storybook/react";
import * as React from "react";

import OrderProducts from "../../../orders/components/OrderProducts";
import Decorator from "../../Decorator";

storiesOf("Orders / OrderProducts", module)
  .addDecorator(Decorator)
  .add("default", () => <OrderProducts />)
  .add("other", () => <OrderProducts />);
