import { storiesOf } from "@storybook/react";
import * as React from "react";

import CustomerDetails from "../../../customers/components/CustomerDetails";
import Decorator from "../../Decorator";

storiesOf("Customers / CustomerDetails", module)
  .addDecorator(Decorator)
  .add("default", () => <CustomerDetails />)
  .add("other", () => <CustomerDetails />);
