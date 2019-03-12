import { storiesOf } from "@storybook/react";
import * as React from "react";

import CustomerAddressDialog, {
  CustomerAddressDialogProps
} from "../../../customers/components/CustomerAddressDialog";
import Decorator from "../../Decorator";

const props: CustomerAddressDialogProps = {};

storiesOf("Customers / Address editing dialog", module)
  .addDecorator(Decorator)
  .add("default", () => <CustomerAddressDialog {...props} />);
