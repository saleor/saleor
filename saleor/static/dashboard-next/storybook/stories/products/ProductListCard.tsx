import { storiesOf } from "@storybook/react";
import * as React from "react";

import * as placeholderImage from "../../../../images/placeholder255x255.png";
import { category as categoryFixture } from "../../../categories/fixtures";
import { pageListProps } from "../../../fixtures";
import ProductListCard, {
  Filter
} from "../../../products/components/ProductListCard";
import Decorator from "../../Decorator";

const products = categoryFixture(placeholderImage).products.edges.map(
  edge => edge.node
);

const filtersList: Filter[] = [
  {
    label: "Gardner-Schultz",
    onClick: () => undefined
  },
  {
    label: "Davis, Brown and Ray",
    onClick: () => undefined
  },
  {
    label: "Franklin Inc",
    onClick: () => undefined
  }
];

storiesOf("Views / Products / Product list", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <ProductListCard
      filtersList={[]}
      currentTab={0}
      products={products}
      {...pageListProps.default}
    />
  ))
  .add("with custom filters", () => (
    <ProductListCard
      products={products}
      {...pageListProps.default}
      filtersList={filtersList}
      currentTab={0}
    />
  ))
  .add("loading", () => (
    <ProductListCard
      {...pageListProps.loading}
      products={undefined}
      filtersList={undefined}
      currentTab={undefined}
    />
  ))
  .add("no data", () => (
    <ProductListCard
      products={[]}
      {...pageListProps.default}
      filtersList={[]}
      currentTab={0}
    />
  ));
