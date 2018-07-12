import { storiesOf } from "@storybook/react";
import * as React from "react";

import * as placeholderImage from "../../../../images/placeholder255x255.png";
import { categories } from "../../../categories/fixtures";
import ProductUpdatePage from "../../../products/components/ProductUpdatePage";
import { product as productFixture } from "../../../products/fixtures";
import Decorator from "../../Decorator";

const product = productFixture(placeholderImage);

storiesOf("Views / Products / Product edit", module)
  .addDecorator(Decorator)
  .add("when data is fully loaded", () => (
    <ProductUpdatePage
      onBack={() => {}}
      onSubmit={() => {}}
      product={product}
      collections={product.collections.edges.map(edge => edge.node)}
      categories={[product.category]}
      placeholderImage={placeholderImage}
      images={product.images.edges.map(edge => edge.node)}
      variants={product.variants.edges.map(edge => edge.node)}
      productCollections={product.collections.edges.map(edge => edge.node)}
      onDelete={() => {}}
      onProductShow={() => {}}
      onVariantAdd={() => {}}
      onVariantShow={() => {}}
    />
  ))
  .add("when loading data", () => (
    <ProductUpdatePage
      categories={[]}
      onBack={() => {}}
      onSubmit={() => {}}
      disabled={true}
      placeholderImage={placeholderImage}
    />
  ));
