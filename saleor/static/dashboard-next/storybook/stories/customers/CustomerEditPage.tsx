import { storiesOf } from "@storybook/react";
import * as React from "react";

import CustomerEditPage from "../../../customers/components/CustomerEditPage";
import { customer } from "../../../customers/fixtures";
import Decorator from "../../Decorator";

const errors = [
  { field: "email", message: "This field cannot be empty" },
  { field: "note", message: "this field cannot be empty" }
];
const callbacks = {
  onBack: undefined,
  onSubmit: () => undefined
};

storiesOf("Views / Customers / Edit customer", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <CustomerEditPage customer={customer} variant="edit" {...callbacks} />
  ))
  .add("with errors", () => (
    <CustomerEditPage
      customer={customer}
      variant="edit"
      errors={errors}
      {...callbacks}
    />
  ))
  .add("when adding new customer", () => (
    <CustomerEditPage variant="add" {...callbacks} />
  ))
  .add("when loading", () => (
    <CustomerEditPage disabled={true} variant="edit" {...callbacks} />
  ));
