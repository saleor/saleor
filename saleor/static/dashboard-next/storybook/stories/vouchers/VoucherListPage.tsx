import { storiesOf } from "@storybook/react";
import * as React from "react";

import VoucherListPage from "../../../vouchers/components/VoucherListPage";
import { vouchers } from "../../../vouchers/fixtures";
import Decorator from "../../Decorator";

storiesOf("Views / Vouchers / Voucher list", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <VoucherListPage
      currency="USD"
      vouchers={vouchers}
      onRowClick={() => () => {}}
    />
  ))
  .add("when loading", () => <VoucherListPage />);
