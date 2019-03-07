import { storiesOf } from "@storybook/react";
import * as React from "react";

import AddressEdit from "../../../components/AddressEdit";
import { customer } from "../../../customers/fixtures";
import { transformAddressToForm } from "../../../misc";
import { countries } from "../../../orders/fixtures";
import Decorator from "../../Decorator";

storiesOf("Generics / AddressEdit", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <div
      style={{
        margin: "auto",
        width: 768
      }}
    >
      <AddressEdit
        errors={{}}
        data={transformAddressToForm(customer.defaultBillingAddress)}
        countries={countries}
        onChange={undefined}
      />
    </div>
  ));
