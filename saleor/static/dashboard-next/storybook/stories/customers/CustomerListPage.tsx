import { storiesOf } from "@storybook/react";
import * as React from "react";

import CustomerListPage from "../../../customers/components/CustomerListPage";
import { customers } from "../../../customers/fixtures";
import { pageListProps } from "../../../fixtures";
import Decorator from "../../Decorator";

storiesOf("Views / Customers / Customer list", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <CustomerListPage customers={customers} {...pageListProps.default} />
  ))
  .add("when loading", () => <CustomerListPage {...pageListProps.loading} />);
