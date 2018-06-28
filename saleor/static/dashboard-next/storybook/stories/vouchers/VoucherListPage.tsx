import { storiesOf } from "@storybook/react";
import * as React from "react";

import { pageListProps } from "../../../fixtures";
import VoucherListPage from "../../../vouchers/components/VoucherListPage";
import { vouchers } from "../../../vouchers/fixtures";
import Decorator from "../../Decorator";

storiesOf("Views / Vouchers / Voucher list", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <VoucherListPage
      currency="USD"
      vouchers={vouchers}
      {...pageListProps.default}
    />
  ))
  .add("when loading", () => <VoucherListPage {...pageListProps.loading} />)
  .add("no data", () => (
    <VoucherListPage vouchers={[]} {...pageListProps.loading} />
  ));
