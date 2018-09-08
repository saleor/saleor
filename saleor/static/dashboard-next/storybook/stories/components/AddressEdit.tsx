import { storiesOf } from "@storybook/react";
import * as React from "react";

import AddressEdit from "../../../components/AddressEdit";
import { Container } from "../../../components/Container";
import { customer } from "../../../customers/fixtures";
import { countries, prefixes } from "../../../orders/fixtures";
import Decorator from "../../Decorator";

storiesOf("Generics / AddressEdit", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <Container width="sm">
      <AddressEdit
        data={customer.defaultBillingAddress}
        prefixes={prefixes}
        countries={countries}
        onChange={undefined}
      />
    </Container>
  ));
