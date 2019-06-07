import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { storiesOf } from "@storybook/react";
import * as React from "react";

import AddressEdit from "@saleor/components/AddressEdit";
import { customer } from "../../../customers/fixtures";
import { transformAddressToForm } from "../../../misc";
import { countries } from "../../../orders/fixtures";
import Decorator from "../../Decorator";

storiesOf("Generics / AddressEdit", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <Card
      style={{
        margin: "auto",
        width: 768
      }}
    >
      <CardContent>
        <AddressEdit
          errors={{}}
          data={transformAddressToForm(customer.defaultBillingAddress)}
          countries={countries}
          onChange={undefined}
        />
      </CardContent>
    </Card>
  ));
