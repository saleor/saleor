import { storiesOf } from "@storybook/react";
import * as React from "react";

import ProductFilters from "../../../category/components/ProductFilters";

const productTypes = [
  { id: "123123123", name: "Type 1" },
  { id: "123123124", name: "Type 2" },
  { id: "123123125", name: "Type 3" },
  { id: "123123126", name: "Type 4" }
];
const productFilters = {
  highlighted: "false",
  name: "Lorem ipsum",
  price_max: "50",
  price_min: "30",
  productTypes: ["123123123", "123123126"],
  published: "true"
};

storiesOf("Categories / ProductFilters", module)
  .add("with initial data", () => (
    <ProductFilters
      formState={productFilters}
      handleClear={() => {}}
      handleSubmit={() => {}}
      productTypes={productTypes}
    />
  ))
  .add("without initial data", () => (
    <ProductFilters
      handleClear={() => {}}
      handleSubmit={() => {}}
      productTypes={productTypes}
    />
  ));
