import { storiesOf } from "@storybook/react";
import * as React from "react";

import * as placeholderImage from "../../../../images/placeholder255x255.png";
import { category as categoryFixture } from "../../../categories/fixtures";
import { Filter } from "../../../components/TableFilter";
import { listActionsProps, pageListProps } from "../../../fixtures";
import ProductListCard, {
  ProductListCardProps
} from "../../../products/components/ProductListCard";
import Decorator from "../../Decorator";

const products = categoryFixture(placeholderImage).products.edges.map(
  edge => edge.node
);

const filtersList: Filter[] = [
  {
    label: "Property X is ",
    onClick: () => undefined
  },
  {
    label: "Property Y is ",
    onClick: () => undefined
  },
  {
    label: "Property Z is ",
    onClick: () => undefined
  },
  {
    label: "Property X is ",
    onClick: () => undefined
  },
  {
    label: "Property Y is ",
    onClick: () => undefined
  },
  {
    label: "Property Z is ",
    onClick: () => undefined
  },
  {
    label: "Property X is ",
    onClick: () => undefined
  },
  {
    label: "Property Y is ",
    onClick: () => undefined
  },
  {
    label: "Property Z is ",
    onClick: () => undefined
  },
  {
    label: "Property X is ",
    onClick: () => undefined
  },
  {
    label: "Property Y is ",
    onClick: () => undefined
  },
  {
    label: "Property Z is ",
    onClick: () => undefined
  },
  {
    label: "Property X is ",
    onClick: () => undefined
  },
  {
    label: "Property Y is ",
    onClick: () => undefined
  },
  {
    label: "Property Z is ",
    onClick: () => undefined
  }
].map((filter, filterIndex) => ({
  ...filter,
  label: filter.label + filterIndex
}));

const props: ProductListCardProps = {
  ...listActionsProps,
  ...pageListProps.default,
  currencySymbol: "USD",
  currentTab: "all",
  filtersList: [],
  onAllProducts: () => undefined,
  onAvailable: () => undefined,
  onCustomFilter: () => undefined,
  onOfStock: () => undefined,
  onSearchChange: val => console.log(val),
  products
};

storiesOf("Views / Products / Product list", module)
  .addDecorator(Decorator)
  .add("default", () => <ProductListCard {...props} />)
  .add("with custom filters", () => (
    <ProductListCard {...props} filtersList={filtersList} currentTab="custom" />
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
