import { storiesOf } from "@storybook/react";
import * as React from "react";

import VoucherDetailsPage, {
  FormData,
  VoucherDetailsPageProps,
  VoucherDetailsPageTab
} from "../../../discounts/components/VoucherDetailsPage";
import { voucherDetails } from "../../../discounts/fixtures";
import { listActionsProps, pageListProps } from "../../../fixtures";
import Decorator from "../../Decorator";
import { formError } from "../../misc";

const props: VoucherDetailsPageProps = {
  ...listActionsProps,
  ...pageListProps.default,
  activeTab: VoucherDetailsPageTab.products,
  categoryListToolbar: null,
  collectionListToolbar: null,
  defaultCurrency: "USD",
  errors: [],
  onBack: () => undefined,
  onCategoryAssign: () => undefined,
  onCategoryClick: () => undefined,
  onCategoryUnassign: () => undefined,
  onCollectionAssign: () => undefined,
  onCollectionClick: () => undefined,
  onCollectionUnassign: () => undefined,
  onCountryAssign: () => undefined,
  onCountryUnassign: () => undefined,
  onProductAssign: () => undefined,
  onProductClick: () => undefined,
  onProductUnassign: () => undefined,
  onRemove: () => undefined,
  onSubmit: () => undefined,
  onTabClick: () => undefined,
  productListToolbar: null,
  saveButtonBarState: "default",
  voucher: voucherDetails
};

storiesOf("Views / Discounts / Voucher details", module)
  .addDecorator(Decorator)
  .add("default", () => <VoucherDetailsPage {...props} />)
  .add("loading", () => (
    <VoucherDetailsPage {...props} disabled={true} voucher={undefined} />
  ))
  .add("form errors", () => (
    <VoucherDetailsPage
      {...props}
      errors={([
        "applyOncePerOrder",
        "code",
        "discountType",
        "endDate",
        "minAmountSpent",
        "name",
        "startDate",
        "type",
        "usageLimit",
        "discountValue"
      ] as Array<keyof FormData>).map(formError)}
    />
  ));
