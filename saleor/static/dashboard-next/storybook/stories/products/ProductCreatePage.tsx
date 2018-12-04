import { storiesOf } from "@storybook/react";
import * as React from "react";

import ProductCreatePage from "../../../products/components/ProductCreatePage";
import { product as productFixture } from "../../../products/fixtures";
import { productTypes } from "../../../productTypes/fixtures";
import Decorator from "../../Decorator";

const product = productFixture("");

storiesOf("Views / Products / Create product", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <ProductCreatePage
      currency="USD"
      disabled={false}
      errors={[]}
      header="Add product"
      collections={product.collections}
      productTypes={productTypes}
      categories={[product.category]}
      onAttributesEdit={undefined}
      onBack={() => undefined}
      onSubmit={() => undefined}
      saveButtonBarState="default"
    />
  ))
  .add("When loading", () => (
    <ProductCreatePage
      currency="USD"
      disabled={true}
      errors={[]}
      header="Add product"
      collections={product.collections}
      productTypes={productTypes}
      categories={[product.category]}
      onAttributesEdit={undefined}
      onBack={() => undefined}
      onSubmit={() => undefined}
      saveButtonBarState="default"
    />
  ));
