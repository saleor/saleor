import { storiesOf } from "@storybook/react";
import React from "react";

import CustomerAddressListPage, {
  CustomerAddressListPageProps
} from "../../../customers/components/CustomerAddressListPage";
import { customer } from "../../../customers/fixtures";
import Decorator from "../../Decorator";

const props: CustomerAddressListPageProps = {
  customer,
  disabled: false,
  onAdd: () => undefined,
  onBack: () => undefined,
  onEdit: () => undefined,
  onRemove: () => undefined,
  onSetAsDefault: () => undefined
};

storiesOf("Views / Customers / Address Book", module)
  .addDecorator(Decorator)
  .add("default", () => <CustomerAddressListPage {...props} />)
  .add("loading", () => (
    <CustomerAddressListPage {...props} customer={undefined} disabled={true} />
  ))
  .add("no data", () => (
    <CustomerAddressListPage
      {...props}
      customer={{ ...customer, addresses: [] }}
    />
  ));
