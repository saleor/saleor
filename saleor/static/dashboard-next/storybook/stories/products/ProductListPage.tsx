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
import ProductListPage, {
  ProductListPageProps
} from "../../../products/components/ProductListPage";
import Decorator from "../../Decorator";

const products = categoryFixture(placeholderImage).products.edges.map(
  edge => edge.node
);

const props: ProductListPageProps = {
  ...listActionsProps,
  ...pageListProps.default,
  ...filterPageProps,
  products,
  settings: {
    ...pageListProps.default.settings,
    columns: ["thumbnail"]
  }
};

storiesOf("Views / Products / Product list", module)
  .addDecorator(Decorator)
  .add("default", () => <ProductListPage {...props} />)
  .add("with custom filters", () => (
    <ProductListPage {...props} filtersList={filters} />
  ))
  .add("loading", () => (
    <ProductListPage
      {...props}
      products={undefined}
      filtersList={undefined}
      currentTab={undefined}
      disabled={true}
    />
  ))
  .add("no data", () => <ProductListPage {...props} products={[]} />);
