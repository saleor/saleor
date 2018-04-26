import { storiesOf } from "@storybook/react";
import * as React from "react";

import ProductCategoryAndCollectionsForm from "../../../products/components/ProductCategoryAndCollectionsForm";

const category = "876752";
const collections = [
  { value: "1", label: "Winter collection" },
  { value: "2", label: "Emperor's choice" }
];
const categories = [
  {
    value: "123123",
    label: "Lorem ipsum dolor"
  },
  {
    value: "876752",
    label: "Mauris vehicula tortor vulputate"
  }
];
const productCollections = ["1"];

storiesOf("Products / ProductCategoryAndCollectionsForm", module)
  .add("while loading data", () => (
    <ProductCategoryAndCollectionsForm onChange={() => {}} loading={true} />
  ))
  .add("when data is loaded", () => (
    <ProductCategoryAndCollectionsForm
      onChange={() => {}}
      collections={collections}
      categories={categories}
      category={category}
      productCollections={productCollections}
    />
  ));
