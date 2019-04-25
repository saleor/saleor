import { storiesOf } from "@storybook/react";
import * as React from "react";

import ProductCreatePage, {
  FormData
} from "../../../products/components/ProductCreatePage";

import { formError } from "../../misc";

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
      fetchCategories={() => undefined}
      fetchCollections={() => undefined}
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
      fetchCategories={() => undefined}
      fetchCollections={() => undefined}
      productTypes={productTypes}
      categories={[product.category]}
      onAttributesEdit={undefined}
      onBack={() => undefined}
      onSubmit={() => undefined}
      saveButtonBarState="default"
    />
  ))
  .add("form errors", () => (
    <ProductCreatePage
      currency="USD"
      disabled={false}
      errors={(["name", "productType", "category", "sku"] as Array<
        keyof FormData
      >).map(field => formError(field))}
      header="Add product"
      collections={product.collections}
      fetchCategories={() => undefined}
      fetchCollections={() => undefined}
      productTypes={productTypes}
      categories={[product.category]}
      onAttributesEdit={undefined}
      onBack={() => undefined}
      onSubmit={() => undefined}
      saveButtonBarState="default"
    />
  ));
