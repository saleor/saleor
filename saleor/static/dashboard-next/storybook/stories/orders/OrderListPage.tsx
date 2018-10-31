import { storiesOf } from "@storybook/react";
import * as React from "react";

import { pageListProps } from "../../../fixtures";
import OrderListPage from "../../../orders/components/OrderListPage";
import { orders } from "../../../orders/fixtures";
import { Filter } from "../../../products/components/ProductListCard";
import Decorator from "../../Decorator";

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

storiesOf("Views / Orders / Order list", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <OrderListPage
      orders={orders}
      {...pageListProps.default}
      filtersList={[]}
      currentTab={0}
    />
  ))
  .add("with custom filters", () => (
    <OrderListPage
      orders={orders}
      {...pageListProps.loading}
      filtersList={filtersList}
      currentTab={0}
    />
  ))
  .add("loading", () => (
    <OrderListPage
      orders={undefined}
      {...pageListProps.loading}
      filtersList={undefined}
      currentTab={undefined}
    />
  ))
  .add("when no data", () => (
    <OrderListPage
      orders={[]}
      {...pageListProps.default}
      filtersList={[]}
      currentTab={0}
    />
  ));
