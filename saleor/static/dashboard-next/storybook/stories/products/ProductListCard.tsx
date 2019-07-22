import { storiesOf } from "@storybook/react";
import React from "react";

import placeholderImage from "../../../../images/placeholder255x255.png";
import { category as categoryFixture } from "../../../categories/fixtures";
import {
  filterPageProps,
  filters,
  listActionsProps,
  pageListProps
} from "../../../fixtures";
import ProductListCard, {
  ProductListCardProps
} from "../../../products/components/ProductListCard";
import Decorator from "../../Decorator";

const products = categoryFixture(placeholderImage).products.edges.map(
  edge => edge.node
);

const props: ProductListCardProps = {
  ...listActionsProps,
  ...pageListProps.default,
  ...filterPageProps,
  products
};

storiesOf("Views / Products / Product list", module)
  .addDecorator(Decorator)
  .add("default", () => <ProductListCard {...props} />)
  .add("with custom filters", () => (
    <ProductListCard {...props} filtersList={filters} />
  ))
  .add("loading", () => (
    <ProductListCard
      {...props}
      products={undefined}
      filtersList={undefined}
      currentTab={undefined}
      disabled={true}
    />
  ))
  .add("no data", () => <ProductListCard {...props} products={[]} />);
