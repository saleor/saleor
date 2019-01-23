import { storiesOf } from "@storybook/react";
import * as React from "react";

import SaleDetailsPage, {
  SaleDetailsPageProps
} from "../../../discounts/components/SaleDetailsPage";
import { sale } from "../../../discounts/fixtures";
import Decorator from "../../Decorator";

const props: SaleDetailsPageProps = {
  activeTab: "categories",
  defaultCurrency: "USD",
  disabled: false,
  onBack: () => undefined,
  onNextPage: () => undefined,
  onPreviousPage: () => undefined,
  onRemove: () => undefined,
  onRowClick: () => () => undefined,
  onSubmit: () => undefined,
  pageInfo: {
    hasNextPage: true,
    hasPreviousPage: false
  },
  sale
};

storiesOf("Views / Discounts / Sale details", module)
  .addDecorator(Decorator)
  .add("default", () => <SaleDetailsPage {...props} />)
  .add("loading", () => (
    <SaleDetailsPage {...props} sale={undefined} disabled={true} />
  ));
