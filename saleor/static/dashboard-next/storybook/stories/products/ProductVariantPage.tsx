import { storiesOf } from "@storybook/react";
import * as React from "react";

import * as placeholderImage from "../../../../images/placeholder60x60.png";
import ProductVariantPage from "../../../products/components/ProductVariantPage";
import { variant as variantFixture } from "../../../products/fixtures";
import Decorator from "../../Decorator";

const variant = variantFixture(placeholderImage);

storiesOf("Views / Products / Product variant details", module)
  .addDecorator(Decorator)
  .add("when loaded data", () => (
    <ProductVariantPage
      variant={variant}
      onBack={() => () => {}}
      onDelete={() => {}}
      onImageSelect={() => {}}
      onSubmit={() => {}}
      onVariantClick={() => () => {}}
    />
  ))
  .add("when loading data", () => (
    <ProductVariantPage
      loading={true}
      onBack={() => () => {}}
      placeholderImage={placeholderImage}
      onDelete={() => {}}
      onImageSelect={() => {}}
      onSubmit={() => {}}
      onVariantClick={() => () => {}}
    />
  ));
