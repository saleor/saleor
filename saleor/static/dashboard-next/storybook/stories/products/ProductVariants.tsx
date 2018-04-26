import { storiesOf } from "@storybook/react";
import * as React from "react";

import ProductVariants from "../../../products/components/ProductVariants";
import { variants } from "../../../products/fixtures";

storiesOf("Products / ProductVariants", module)
  .add("when loading data", () => <ProductVariants />)
  .add("when product has no variants", () => <ProductVariants variants={[]} />)
  .add("when product has variants", () => (
    <ProductVariants
      variants={variants}
      fallbackGross="80%"
      fallbackPrice="90.00 USD"
    />
  ))
  .add("with clickable rows", () => (
    <ProductVariants
      variants={variants}
      onRowClick={() => {}}
      fallbackGross="80%"
      fallbackPrice="90.00 USD"
    />
  ));
