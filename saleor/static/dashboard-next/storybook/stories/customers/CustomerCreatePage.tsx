import { storiesOf } from "@storybook/react";
import * as React from "react";

import CustomerCreatePage, {
  CustomerCreatePageProps
} from "../../../customers/components/CustomerCreatePage";
import Decorator from "../../Decorator";

const props: CustomerCreatePageProps = {
  disabled: false,
  onBack: () => undefined
};

storiesOf("Views / Customers / Create customer", module)
  .addDecorator(Decorator)
  .add("default", () => <CustomerCreatePage {...props} />)
  .add("loading", () => <CustomerCreatePage {...props} disabled={true} />);
