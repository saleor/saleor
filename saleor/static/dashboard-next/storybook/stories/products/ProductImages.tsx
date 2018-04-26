import { storiesOf } from "@storybook/react";
import * as React from "react";

import * as placeholder from "../../../../images/placeholder255x255.png";
import ProductImages from "../../../products/components/ProductImages";
import { images as imagesFixture } from "../../../products/fixtures";

const images = imagesFixture.map(image => ({ ...image, url: placeholder }));

storiesOf("Products / ProductImages", module)
  .add("without data", () => (
    <ProductImages
      images={[]}
      onImageReorder={() => {}}
      onImageUpload={() => {}}
    />
  ))
  .add("with data", () => (
    <ProductImages
      images={images}
      onImageReorder={() => {}}
      onImageUpload={() => {}}
    />
  ))
  .add("when loading data", () => (
    <ProductImages
      placeholderImage={placeholder}
      onImageReorder={() => {}}
      onImageUpload={() => {}}
    />
  ));
