import { storiesOf } from "@storybook/react";
import React from "react";

import { formError } from "@saleor/storybook/misc";
import placeholderImage from "../../../../images/placeholder60x60.png";
import ProductVariantPage from "../../../products/components/ProductVariantPage";
import { variant as variantFixture } from "../../../products/fixtures";
import Decorator from "../../Decorator";

const variant = variantFixture(placeholderImage);

storiesOf("Views / Products / Product variant details", module)
  .addDecorator(Decorator)
  .add("when loaded data", () => (
    <ProductVariantPage
      header={variant.name || variant.sku}
      errors={[]}
      variant={variant}
      onAdd={() => undefined}
      onBack={() => undefined}
      onDelete={undefined}
      onImageSelect={() => undefined}
      onSubmit={() => undefined}
      onVariantClick={() => undefined}
      saveButtonBarState="default"
    />
  ))
  .add("when loading data", () => (
    <ProductVariantPage
      header={undefined}
      errors={[]}
      loading={true}
      onBack={() => undefined}
      placeholderImage={placeholderImage}
      onAdd={() => undefined}
      onDelete={undefined}
      onImageSelect={() => undefined}
      onSubmit={() => undefined}
      onVariantClick={() => undefined}
      saveButtonBarState="default"
    />
  ))
  .add("attribute errors", () => (
    <ProductVariantPage
      header={variant.name || variant.sku}
      variant={variant}
      onAdd={() => undefined}
      onBack={() => undefined}
      onDelete={undefined}
      onImageSelect={() => undefined}
      onSubmit={() => undefined}
      onVariantClick={() => undefined}
      saveButtonBarState="default"
      errors={["attributes:Borders", "attributes:Legacy"].map(formError)}
    />
  ));
