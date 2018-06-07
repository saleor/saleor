import { storiesOf } from "@storybook/react";
import * as React from "react";

import AddressFormatter from "../../../components/AddressFormatter";
import { customer } from "../../../customers/fixtures";
import Decorator from "../../Decorator";

storiesOf("Generics / AddressFormatter", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <AddressFormatter address={customer.defaultBillingAddress} />
  ))
  .add("when loading", () => <AddressFormatter />);
