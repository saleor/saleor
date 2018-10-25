import { storiesOf } from "@storybook/react";
import * as React from "react";

import CustomerDetailsPage, {
  CustomerDetailsPageProps
} from "../../../customers/components/CustomerDetailsPage";
import { customer } from "../../../customers/fixtures";
import Decorator from "../../Decorator";

const props: CustomerDetailsPageProps = {
  customer,
  disabled: false,
  onAddressManageClick: () => undefined,
  onBack: () => undefined,
  onRowClick: () => undefined,
  onSubmit: () => undefined,
  onViewAllOrdersClick: () => undefined
};

storiesOf("Views / Customers / Customer details", module)
  .addDecorator(Decorator)
  .add("default", () => <CustomerDetailsPage {...props} />)
  .add("loading", () => (
    <CustomerDetailsPage {...props} customer={undefined} disabled={true} />
  ));
