import { storiesOf } from "@storybook/react";
import * as React from "react";

import CustomerListPage from "../../../customers/components/CustomerListPage";
import { customers } from "../../../customers/fixtures";
import Decorator from "../../Decorator";

storiesOf("Views / Customers / Customer list", module)
  .addDecorator(Decorator)
  .add("default", () => <CustomerListPage customers={customers} />)
  .add("with ability to add new customer", () => (
    <CustomerListPage customers={customers} onAddCustomer={() => {}} />
  ))
  .add("with clickable rows", () => (
    <CustomerListPage customers={customers} onRowClick={() => () => {}} />
  ))
  .add("when loading", () => <CustomerListPage />);
