import { storiesOf } from "@storybook/react";
import * as React from "react";

import ProductVariantAttributes from "../../../products/components/ProductVariantAttributes";
import { variant as variantFixture } from "../../../products/fixtures";

const variant = variantFixture("");

storiesOf("Products / ProductVariantAttributes", module)
  .add("when loading data", () => (
    <ProductVariantAttributes onChange={() => {}} loading={true} />
  ))
  .add("when loaded data", () => (
    <ProductVariantAttributes
      attributes={variant.attributes}
      onChange={() => {}}
    />
  ));
