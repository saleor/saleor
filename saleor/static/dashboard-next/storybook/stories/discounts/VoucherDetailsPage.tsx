import { storiesOf } from "@storybook/react";
import * as React from "react";

import VoucherDetailsPage, {
  VoucherDetailsPageProps
} from "../../../discounts/components/VoucherDetailsPage";
import { voucherDetails } from "../../../discounts/fixtures";
import { pageListProps } from "../../../fixtures";
import Decorator from "../../Decorator";

const props: VoucherDetailsPageProps = {
  ...pageListProps.default,
  defaultCurrency: "USD",
  onBack: () => undefined,
  voucher: voucherDetails
};

storiesOf("Views / Discounts / Voucher Details", module)
  .addDecorator(Decorator)
  .add("default", () => <VoucherDetailsPage {...props} />)
  .add("loading", () => (
    <VoucherDetailsPage {...props} disabled={true} voucher={undefined} />
  ));
