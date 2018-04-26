import { storiesOf } from "@storybook/react";
import * as React from "react";

import * as placeholder from "../../../../images/placeholder255x255.png";
import ProductDetailsPage from "../../../products/components/ProductDetailsPage";
import { product } from "../../../products/fixtures";

product.images.edges = product.images.edges.map(edge => ({
  ...edge,
  node: { ...edge.node, url: placeholder }
}));

storiesOf("Products / ProductDetailsPage", module)
  .add("when loading data", () => (
    <ProductDetailsPage
      placeholderImage={placeholder}
      onBack={() => {}}
      onCollectionShow={() => {}}
      onDelete={() => {}}
      onEdit={() => {}}
      onImageReorder={() => {}}
      onProductPublish={() => {}}
      onProductShow={() => {}}
      onVariantShow={() => {}}
      onImageUpload={() => {}}
      onImageEdit={() => () => {}}
    />
  ))
  .add("when loaded data", () => (
    <ProductDetailsPage
      product={product}
      placeholderImage={placeholder}
      onBack={() => {}}
      onCollectionShow={() => {}}
      onDelete={() => {}}
      onEdit={() => {}}
      onImageReorder={() => {}}
      onProductPublish={() => {}}
      onProductShow={() => {}}
      onVariantShow={() => {}}
      onImageUpload={() => {}}
      onImageEdit={() => () => {}}
    />
  ));
