import { storiesOf } from "@storybook/react";
import * as React from "react";

import ProductAttributesForm from "../../../products/components/ProductAttributesForm";
import { product as productFixture } from "../../../products/fixtures";

const product = productFixture("");

storiesOf("Products / ProductAttributesForm", module)
  .add("when loading data", () => (
    <ProductAttributesForm disabled={true} onChange={() => {}} />
  ))
  .add("when data loaded", () => (
    <ProductAttributesForm
      attributes={product.attributes}
      data={product.attributes}
      onChange={() => {}}
    />
  ));
