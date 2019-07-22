import { storiesOf } from "@storybook/react";
import React from "react";

import { formError } from "@saleor/storybook/misc";
import placeholderImage from "../../../../images/placeholder255x255.png";
import ProductVariantCreatePage from "../../../products/components/ProductVariantCreatePage";
import { product as productFixture } from "../../../products/fixtures";
import Decorator from "../../Decorator";

const product = productFixture(placeholderImage);

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
      errors={[formError("attributes:color")]}
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
  ))
  .add("add first variant", () => (
    <ProductVariantCreatePage
      currencySymbol="USD"
      errors={[]}
      header="Add variant"
      loading={false}
      product={{
        ...product,
        variants: []
      }}
      onBack={() => undefined}
      onSubmit={() => undefined}
      onVariantClick={undefined}
      saveButtonBarState="default"
    />
  ));
