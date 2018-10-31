import { storiesOf } from "@storybook/react";
import * as React from "react";

import * as placeholderImage from "../../../../images/placeholder255x255.png";
import { category as categoryFixture } from "../../../categories/fixtures";
import { pageListProps } from "../../../fixtures";
import ProductListCard from "../../../products/components/ProductListCard";
import Decorator from "../../Decorator";

const products = categoryFixture(placeholderImage).products.edges.map(
  edge => edge.node
);

storiesOf("Views / Products / Product list", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <ProductListCard products={products} {...pageListProps.default} />
  ))
  .add("loading", () => (
    <ProductListCard {...pageListProps.loading} products={undefined} />
  ))
  .add("no data", () => (
    <ProductListCard products={[]} {...pageListProps.default} />
  ));
