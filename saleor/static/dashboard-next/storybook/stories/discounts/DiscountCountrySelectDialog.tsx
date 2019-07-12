import { storiesOf } from "@storybook/react";
import React from "react";

import DiscountCountrySelectDialog, {
  DiscountCountrySelectDialogProps
} from "../../../discounts/components/DiscountCountrySelectDialog";
import Decorator from "../../Decorator";

const props: DiscountCountrySelectDialogProps = {
  confirmButtonState: "default",
  countries: [
    { __typename: "CountryDisplay", code: "AF", country: "Afghanistan" },
    { __typename: "CountryDisplay", code: "AX", country: "Åland Islands" },
    { __typename: "CountryDisplay", code: "AL", country: "Albania" },
    { __typename: "CountryDisplay", code: "DZ", country: "Algeria" },
    { __typename: "CountryDisplay", code: "AS", country: "American Samoa" }
  ],
  initial: ["AX", "AL"],
  onClose: () => undefined,
  onConfirm: () => undefined,
  open: true
};

storiesOf("Discounts / Select countries", module)
  .addDecorator(Decorator)
  .add("default", () => <DiscountCountrySelectDialog {...props} />);
