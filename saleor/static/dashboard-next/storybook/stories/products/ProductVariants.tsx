import { storiesOf } from "@storybook/react";
import * as React from "react";

import ProductVariants from "../../../products/components/ProductVariants";
import { product as productFixture } from "../../../products/fixtures";

const product = productFixture("");
const variants = product.variants.edges.map(edge => edge.node);

storiesOf("Products / ProductVariants", module)
  .add("when loading data", () => <ProductVariants />)
  .add("when product has no variants", () => <ProductVariants variants={[]} />)
  .add("when product has variants", () => (
    <ProductVariants variants={variants} fallbackPrice={product.price} />
  ))
  .add("with clickable rows", () => (
    <ProductVariants
      variants={variants}
      onRowClick={() => {}}
      fallbackPrice={product.price}
    />
  ));
