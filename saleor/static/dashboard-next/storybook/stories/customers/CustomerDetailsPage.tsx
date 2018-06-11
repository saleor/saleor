import { storiesOf } from "@storybook/react";
import * as React from "react";

import CustomerDetailsPage from "../../../customers/components/CustomerDetailsPage";
import { customer } from "../../../customers/fixtures";
import { flatOrders } from "../../../orders/fixtures";
import Decorator from "../../Decorator";

const callbacks = {
  onBack: () => {},
  onBillingAddressEdit: () => {},
  onCustomerDelete: () => {},
  onCustomerEdit: () => {},
  onEmailClick: () => {},
  onOrderClick: (id: string) => () => {},
  onShippingAddressEdit: () => {}
};

storiesOf("Views / Customers / Customer details", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <CustomerDetailsPage
      customer={customer}
      orders={flatOrders}
      {...callbacks}
    />
  ))
  .add("when loading", () => <CustomerDetailsPage {...callbacks} />);
