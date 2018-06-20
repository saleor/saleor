import { storiesOf } from "@storybook/react";
import * as React from "react";

import CustomerAddress from "../../../customers/components/CustomerAddress";
import Decorator from "../../Decorator";

storiesOf("Customers / CustomerAddress", module)
  .addDecorator(Decorator)
  .add("default", () => <CustomerAddress />)
  .add("other", () => <CustomerAddress />);
