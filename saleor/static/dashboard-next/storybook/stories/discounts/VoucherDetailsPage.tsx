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
  onCategoryAssign: () => undefined,
  onCategoryClick: () => undefined,
  onCollectionAssign: () => undefined,
  onCollectionClick: () => undefined,
  onCountryAssign: () => undefined,
  onCountryUnassign: () => undefined,
  onProductAssign: () => undefined,
  onProductClick: () => undefined,
  onRemove: () => undefined,
  onSubmit: () => undefined,
  saveButtonBarState: "default",
  voucher: voucherDetails
};

storiesOf("Views / Discounts / Voucher details", module)
  .addDecorator(Decorator)
  .add("default", () => <VoucherDetailsPage {...props} />)
  .add("loading", () => (
    <VoucherDetailsPage {...props} disabled={true} voucher={undefined} />
  ));
