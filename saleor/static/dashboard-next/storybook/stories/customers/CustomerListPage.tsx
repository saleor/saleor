import { storiesOf } from "@storybook/react";
import * as React from "react";

import CustomerListPage, {
  CustomerListPageProps
} from "../../../customers/components/CustomerListPage";
import { customerList } from "../../../customers/fixtures";
import { pageListProps } from "../../../fixtures";
import Decorator from "../../Decorator";

const props: CustomerListPageProps = {
  ...pageListProps.default,
  customers: customerList
};

storiesOf("Views / Customers / Customer list", module)
  .addDecorator(Decorator)
  .add("default", () => <CustomerListPage {...props} />)
  .add("loading", () => (
    <CustomerListPage {...props} disabled={true} customers={undefined} />
  ))
  .add("no data", () => <CustomerListPage {...props} customers={[]} />);
