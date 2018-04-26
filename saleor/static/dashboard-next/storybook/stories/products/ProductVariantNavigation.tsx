import { storiesOf } from "@storybook/react";
import * as React from "react";

import ProductVariantNavigation from "../../../products/components/ProductVariantNavigation";
import { variantSiblings as variantSiblingsFixture } from "../../../products/fixtures";

storiesOf("Products / ProductVariantNavigation", module)
  .add("when loading data", () => <ProductVariantNavigation loading={true} />)
  .add("when loaded data", () => (
    <ProductVariantNavigation variants={variantSiblingsFixture("")} />
  ))
  .add("with clickable rows", () => (
    <ProductVariantNavigation
      variants={variantSiblingsFixture("")}
      onRowClick={() => {}}
    />
  ));
