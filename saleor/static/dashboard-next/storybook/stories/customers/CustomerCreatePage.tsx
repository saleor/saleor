import { storiesOf } from "@storybook/react";
import * as React from "react";

import CustomerCreatePage, {
  CustomerCreatePageProps
} from "../../../customers/components/CustomerCreatePage";
import Decorator from "../../Decorator";

const props: CustomerCreatePageProps = {
  countries: [
    { __typename: "CountryDisplay", code: "UK", country: "United Kingdom" },
    { __typename: "CountryDisplay", code: "PL", country: "Poland" }
  ],
  disabled: false,
  onBack: () => undefined
};

storiesOf("Views / Customers / Create customer", module)
  .addDecorator(Decorator)
  .add("default", () => <CustomerCreatePage {...props} />)
  .add("loading", () => <CustomerCreatePage {...props} disabled={true} />);
