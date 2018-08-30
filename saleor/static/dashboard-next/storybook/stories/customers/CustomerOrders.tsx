import { storiesOf } from "@storybook/react";
import * as React from "react";

import CustomerOrders from "../../../customers/components/CustomerOrders";
import Decorator from "../../Decorator";

storiesOf("Customers / CustomerOrders", module)
  .addDecorator(Decorator)
  .add("default", () => <CustomerOrders />)
  .add("other", () => <CustomerOrders />);
