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
      currencySymbol="USD"
      errors={[]}
      header="Add variant"
      loading={false}
      product={product}
      onBack={() => undefined}
      onSubmit={() => undefined}
      onVariantClick={undefined}
      saveButtonBarState="default"
    />
  ))
  .add("with errors", () => (
    <ProductVariantCreatePage
      currencySymbol="USD"
      errors={errors}
      header="Add variant"
      loading={false}
      product={product}
      onBack={() => undefined}
      onSubmit={() => undefined}
      onVariantClick={undefined}
      saveButtonBarState="default"
    />
  ))
  .add("when loading data", () => (
    <ProductVariantCreatePage
      currencySymbol="USD"
      errors={[]}
      header="Add variant"
      loading={true}
      product={undefined}
      onBack={() => undefined}
      onSubmit={() => undefined}
      onVariantClick={undefined}
      saveButtonBarState="default"
    />
  ));
