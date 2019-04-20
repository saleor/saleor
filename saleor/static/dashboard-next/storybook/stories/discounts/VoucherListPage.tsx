import { storiesOf } from "@storybook/react";
import * as React from "react";

import VoucherListPage, {
  VoucherListPageProps
} from "../../../discounts/components/VoucherListPage";
import { voucherList } from "../../../discounts/fixtures";
import { listActionsProps, pageListProps } from "../../../fixtures";
import Decorator from "../../Decorator";

const props: VoucherListPageProps = {
  ...listActionsProps,
  ...pageListProps.default,
  defaultCurrency: "USD",
  vouchers: voucherList
};

storiesOf("Views / Discounts / Voucher list", module)
  .addDecorator(Decorator)
  .add("default", () => <VoucherListPage {...props} />)
  .add("loading", () => <VoucherListPage {...props} vouchers={undefined} />)
  .add("no data", () => <VoucherListPage {...props} vouchers={[]} />);
