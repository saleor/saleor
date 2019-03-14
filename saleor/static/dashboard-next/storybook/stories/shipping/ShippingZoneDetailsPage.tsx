import { storiesOf } from "@storybook/react";
import * as React from "react";

import ShippingZoneDetailsPage, {
  ShippingZoneDetailsPageProps
} from "../../../shipping/components/ShippingZoneDetailsPage";
import { shippingZone } from "../../../shipping/fixtures";
import Decorator from "../../Decorator";
import { formError } from "../../misc";

const props: ShippingZoneDetailsPageProps = {
  disabled: false,
  errors: [],
  onBack: () => undefined,
  onCountryAdd: () => undefined,
  onCountryRemove: () => undefined,
  onDelete: () => undefined,
  onPriceRateAdd: () => undefined,
  onPriceRateEdit: () => undefined,
  onRateRemove: () => undefined,
  onSubmit: () => undefined,
  onWeightRateAdd: () => undefined,
  onWeightRateEdit: () => undefined,
  saveButtonBarState: "default",
  shippingZone
};

storiesOf("Views / Shipping / Shipping zone details", module)
  .addDecorator(Decorator)
  .add("default", () => <ShippingZoneDetailsPage {...props} />)
  .add("loading", () => (
    <ShippingZoneDetailsPage
      {...props}
      disabled={true}
      shippingZone={undefined}
    />
  ))
  .add("form errors", () => (
    <ShippingZoneDetailsPage {...props} errors={["name"].map(formError)} />
  ));
