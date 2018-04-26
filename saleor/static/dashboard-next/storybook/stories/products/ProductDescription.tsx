import { storiesOf } from "@storybook/react";
import * as React from "react";

import ProductDescription from "../../../products/components/ProductDescription";
import { product } from "../../../products/fixtures";

storiesOf("Products / ProductDescription", module)
  .add("with no description", () => (
    <ProductDescription
      id={product.id}
      name={product.name}
      url={product.url}
      description={""}
      onBack={() => {}}
      onDelete={() => {}}
      onEdit={() => {}}
      onShow={() => {}}
    />
  ))
  .add("with description", () => (
    <ProductDescription
      id={product.id}
      name={product.name}
      description={product.description}
      url={product.url}
      onBack={() => {}}
      onDelete={() => {}}
      onEdit={() => {}}
      onShow={() => {}}
    />
  ))
  .add("when loading data", () => (
    <ProductDescription
      onBack={() => {}}
      onDelete={() => {}}
      onEdit={() => {}}
      onShow={() => {}}
    />
  ));
