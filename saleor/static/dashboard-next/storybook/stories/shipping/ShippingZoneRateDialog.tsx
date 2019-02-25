import { storiesOf } from "@storybook/react";
import * as React from "react";

import ShippingZoneRateDialog, {
  ShippingZoneRateDialogProps
} from "../../../shipping/components/ShippingZoneRateDialog";
import { shippingZone } from "../../../shipping/fixtures";
import Decorator from "../../Decorator";

const props: ShippingZoneRateDialogProps = {
  action: "edit",
  confirmButtonState: "default",
  defaultCurrency: "USD",
  disabled: false,
  onClose: () => undefined,
  onSubmit: () => undefined,
  open: true,
  rate: shippingZone.shippingMethods[0],
  variant: "price"
};

storiesOf("Shipping / Rate details", module)
  .addDecorator(Decorator)
  .add("default", () => <ShippingZoneRateDialog {...props} />)
  .add("loading", () => (
    <ShippingZoneRateDialog {...props} disabled={true} rate={undefined} />
  ))
  .add("new", () => (
    <ShippingZoneRateDialog {...props} rate={undefined} action="create" />
  ))
  .add("weight", () => <ShippingZoneRateDialog {...props} variant="weight" />);
