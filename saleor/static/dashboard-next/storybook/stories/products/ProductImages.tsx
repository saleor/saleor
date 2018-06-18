import { storiesOf } from "@storybook/react";
import * as React from "react";

import * as placeholderImage from "../../../../images/placeholder255x255.png";
import ProductImages from "../../../products/components/ProductImages";
import { product as productFixture } from "../../../products/fixtures";

const images = productFixture(placeholderImage).images.edges.map(
  edge => edge.node
);

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
      placeholderImage={placeholderImage}
      onImageReorder={() => {}}
      onImageUpload={() => {}}
    />
  ));
