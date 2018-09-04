import { storiesOf } from "@storybook/react";
import * as React from "react";

import { categories } from "../../../categories/fixtures";
import { countries } from "../../../orders/fixtures";
import { products } from "../../../products/fixtures";
import VoucherDetailsPage from "../../../vouchers/components/VoucherDetailsPage";
import { vouchers } from "../../../vouchers/fixtures";
import Decorator from "../../Decorator";

storiesOf("Views / Vouchers / Voucher details", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <VoucherDetailsPage
      onBack={() => undefined}
      currency="USD"
      voucher={vouchers[0]}
      onVoucherDelete={undefined}
      shippingSearchResults={countries}
      categorySearchResults={categories}
      productSearchResults={products("")}
    />
  ))
  .add("when loading", () => (
    <VoucherDetailsPage disabled onBack={() => undefined} />
  ));
