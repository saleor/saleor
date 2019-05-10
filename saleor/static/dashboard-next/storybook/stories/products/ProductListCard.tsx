import { storiesOf } from "@storybook/react";
import * as React from "react";

import * as placeholderImage from "../../../../images/placeholder255x255.png";
import { category as categoryFixture } from "../../../categories/fixtures";
import { Filter } from "../../../components/TableFilter";
import { listActionsProps, pageListProps } from "../../../fixtures";
import ProductListCard from "../../../products/components/ProductListCard";
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
      currentTab="all"
      products={products}
      {...listActionsProps}
      {...pageListProps.default}
      onAllProducts={() => undefined}
      onAvailable={() => undefined}
      onOfStock={() => undefined}
      onCustomFilter={() => undefined}
    />
  ))
  .add("with custom filters", () => (
    <ProductListCard
      products={products}
      {...listActionsProps}
      {...pageListProps.default}
      filtersList={filtersList}
      currentTab="custom"
      onAllProducts={() => undefined}
      onAvailable={() => undefined}
      onOfStock={() => undefined}
      onCustomFilter={() => undefined}
    />
  ))
  .add("loading", () => (
    <ProductListCard
      {...listActionsProps}
      {...pageListProps.loading}
      products={undefined}
      filtersList={undefined}
      currentTab={undefined}
      onAllProducts={() => undefined}
      onAvailable={() => undefined}
      onOfStock={() => undefined}
      onCustomFilter={() => undefined}
    />
  ))
  .add("no data", () => (
    <ProductListCard
      products={[]}
      {...listActionsProps}
      {...pageListProps.default}
      filtersList={[]}
      currentTab="all"
      onAllProducts={() => undefined}
      onAvailable={() => undefined}
      onOfStock={() => undefined}
      onCustomFilter={() => undefined}
    />
  ));
