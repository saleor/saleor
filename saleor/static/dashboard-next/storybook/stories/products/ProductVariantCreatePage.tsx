import { storiesOf } from "@storybook/react";
import * as React from "react";

import * as placeholderImage from "../../../../images/placeholder255x255.png";
import ProductVariantCreatePage from "../../../products/components/ProductVariantCreatePage";
import { product as productFixture } from "../../../products/fixtures";
import Decorator from "../../Decorator";

const product = productFixture(placeholderImage);
const errors = [
  {
    field: "cost_price",
    message: "Generic error"
  },
  {
    field: "price_override",
    message: "Generic error"
  },
  {
    field: "sku",
    message: "Generic error"
  },
  {
    field: "stock",
    message: "Generic error"
  }
];

storiesOf("Views / Products / Create product variant", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <ProductVariantCreatePage
      errors={[]}
      header="Add variant"
      loading={false}
      product={product}
      onBack={() => undefined}
      onSubmit={() => undefined}
      onVariantClick={undefined}
    />
  ))
  .add("with errors", () => (
    <ProductVariantCreatePage
      errors={errors}
      header="Add variant"
      loading={false}
      product={product}
      onBack={() => undefined}
      onSubmit={() => undefined}
      onVariantClick={undefined}
    />
  ))
  .add("when loading data", () => (
    <ProductVariantCreatePage
      errors={[]}
      header="Add variant"
      loading={true}
      onBack={() => undefined}
      onSubmit={() => undefined}
      onVariantClick={undefined}
    />
  ));
