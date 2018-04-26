import { storiesOf } from "@storybook/react";
import * as React from "react";

import * as placeholderImage from "../../../../images/placeholder255x255.png";
import ProductVariantImages from "../../../products/components/ProductVariantImages";
import { variantProductImages as imagesFixture } from "../../../products/fixtures";

const images = imagesFixture(placeholderImage);

storiesOf("Products / ProductVariantImages", module)
  .add("when loading data", () => (
    <ProductVariantImages
      onImageAdd={() => {}}
      loading={true}
      placeholderImage={placeholderImage}
    />
  ))
  .add("when loaded data", () => (
    <ProductVariantImages
      images={images}
      onImageAdd={() => {}}
      placeholderImage={placeholderImage}
    />
  ));
