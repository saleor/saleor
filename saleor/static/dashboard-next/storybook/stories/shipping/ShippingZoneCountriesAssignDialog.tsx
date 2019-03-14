import { storiesOf } from "@storybook/react";
import * as React from "react";

import ShippingZoneCountriesAssignDialog, {
  ShippingZoneCountriesAssignDialogProps
} from "../../../shipping/components/ShippingZoneCountriesAssignDialog";
import Decorator from "../../Decorator";
import { countries } from "../taxes/fixtures";

const props: ShippingZoneCountriesAssignDialogProps = {
  confirmButtonState: "default",
  countries,
  initial: ["PL", "GB", "DE"],
  isDefault: false,
  onClose: () => undefined,
  onConfirm: () => undefined,
  open: true
};

storiesOf("Shipping / Assign countries", module)
  .addDecorator(Decorator)
  .add("default", () => <ShippingZoneCountriesAssignDialog {...props} />);
