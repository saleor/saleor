import { storiesOf } from "@storybook/react";
import * as React from "react";

import ProductDetailsForm from "../../../products/components/ProductDetailsForm";
import { product as productFixture } from "../../../products/fixtures";

const product = productFixture("");

storiesOf("Products / ProductDetailsForm", module)
  .add("with no initial data", () => (
    <ProductDetailsForm onBack={() => {}} onChange={() => {}} />
  ))
  .add("with initial data", () => (
    <ProductDetailsForm
      onBack={() => {}}
      onChange={() => {}}
      name={product.name}
      description={product.description}
      currencySymbol={product.price.currency}
      price={product.price.amount}
    />
  ))
  .add("when loading data", () => (
    <ProductDetailsForm onBack={() => {}} onChange={() => {}} disabled={true} />
  ));
