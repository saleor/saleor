import { Omit } from "@material-ui/core";
import { storiesOf } from "@storybook/react";
import React from "react";

import CustomerDetailsPage, {
  CustomerDetailsPageProps
} from "../../../customers/components/CustomerDetailsPage";
import { customer } from "../../../customers/fixtures";
import Decorator from "../../Decorator";
import { formError } from "../../misc";

const props: Omit<CustomerDetailsPageProps, "classes"> = {
  customer,
  disabled: false,
  errors: [],
  onAddressManageClick: () => undefined,
  onBack: () => undefined,
  onDelete: () => undefined,
  onRowClick: () => undefined,
  onSubmit: () => undefined,
  onViewAllOrdersClick: () => undefined,
  saveButtonBar: "default"
};

interface CustomerDetailsPageErrors {
  firstName: string;
  email: string;
  lastName: string;
  note: string;
}

storiesOf("Views / Customers / Customer details", module)
  .addDecorator(Decorator)
  .add("default", () => <CustomerDetailsPage {...props} />)
  .add("loading", () => (
    <CustomerDetailsPage {...props} customer={undefined} disabled={true} />
  ))
  .add("form errors", () => (
    <CustomerDetailsPage
      {...props}
      errors={(["email", "firstName", "lastName"] as Array<
        keyof CustomerDetailsPageErrors
      >).map(field => formError(field))}
    />
  ))
  .add("different addresses", () => (
    <CustomerDetailsPage
      {...props}
      customer={{
        ...customer,
        defaultBillingAddress: {
          ...customer.defaultBillingAddress,
          id: "AvSduf72="
        }
      }}
    />
  ))
  .add("never logged", () => (
    <CustomerDetailsPage
      {...props}
      customer={{
        ...customer,
        lastLogin: null
      }}
    />
  ))
  .add("never placed order", () => (
    <CustomerDetailsPage
      {...props}
      customer={{
        ...customer,
        lastPlacedOrder: {
          ...customer.lastPlacedOrder,
          edges: []
        }
      }}
    />
  ))
  .add("no default billing address", () => (
    <CustomerDetailsPage
      {...props}
      customer={{
        ...customer,
        defaultBillingAddress: null
      }}
    />
  ))
  .add("no default shipping address", () => (
    <CustomerDetailsPage
      {...props}
      customer={{
        ...customer,
        defaultShippingAddress: null
      }}
    />
  ))
  .add("no address at all", () => (
    <CustomerDetailsPage
      {...props}
      customer={{
        ...customer,
        defaultBillingAddress: null,
        defaultShippingAddress: null
      }}
    />
  ));
