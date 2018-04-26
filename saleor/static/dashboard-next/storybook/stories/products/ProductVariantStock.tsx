import { storiesOf } from "@storybook/react";
import * as React from "react";

import ProductVariantStock from "../../../products/components/ProductVariantStock";
import { variant as variantFixture } from "../../../products/fixtures";

const variant = variantFixture("");

storiesOf("Products / ProductVariantStock", module)
  .add("when loading data", () => (
    <ProductVariantStock loading={true} onChange={() => {}} />
  ))
  .add("when loaded data", () => (
    <ProductVariantStock
      onChange={() => {}}
      sku={variant.sku}
      stock={variant.stock}
      stockAllocated={variant.stockAllocated}
    />
  ));
