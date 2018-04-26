import { storiesOf } from "@storybook/react";
import * as React from "react";

import * as placeholderImage from "../../../../images/placeholder60x60.png";
import ProductVariantProduct from "../../../products/components/ProductVariantProduct";
import { variant as variantFixture } from "../../../products/fixtures";

const product = variantFixture(placeholderImage).product;

storiesOf("Products / ProductVariantProduct", module)
  .add("when loading data", () => (
    <ProductVariantProduct loading={true} placeholderImage={placeholderImage} />
  ))
  .add("when loaded data", () => <ProductVariantProduct product={product} />);
