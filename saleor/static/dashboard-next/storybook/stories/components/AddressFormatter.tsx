import { storiesOf } from "@storybook/react";
import React from "react";

import AddressFormatter from "@saleor/components/AddressFormatter";
import { customer } from "../../../customers/fixtures";
import CardDecorator from "../../CardDecorator";
import Decorator from "../../Decorator";

storiesOf("Generics / AddressFormatter", module)
  .addDecorator(CardDecorator)
  .addDecorator(Decorator)
  .add("default", () => (
    <AddressFormatter address={customer.defaultBillingAddress} />
  ))
  .add("when loading", () => <AddressFormatter />);
