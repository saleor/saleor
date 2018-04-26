import { storiesOf } from "@storybook/react";
import * as React from "react";

import ProductVariantPrice from "../../../products/components/ProductVariantPrice";
import { variant as variantFixture } from "../../../products/fixtures";

const variant = variantFixture("");

storiesOf("Products / ProductVariantPrice", module)
  .add("when loading data", () => (
    <ProductVariantPrice onChange={() => {}} loading={true} />
  ))
  .add("when loaded data", () => (
    <ProductVariantPrice
      costPrice={variant.priceOverride.amount}
      onChange={() => {}}
      priceOverride={variant.priceOverride.amount}
      currencySymbol={variant.priceOverride.currency}
    />
  ));
