import { storiesOf } from "@storybook/react";
import * as React from "react";

import { Filter } from "../../../components/TableFilter/";
import { listActionsProps, pageListProps } from "../../../fixtures";
import OrderListPage from "../../../orders/components/OrderListPage";
import { orders } from "../../../orders/fixtures";
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
      {...listActionsProps}
      {...pageListProps.default}
      filtersList={[]}
      onAllProducts={() => undefined}
      currentTab="all"
      onToFulfill={() => undefined}
      onToCapture={() => undefined}
      onCustomFilter={() => undefined}
    />
  ))
  .add("with custom filters", () => (
    <OrderListPage
      orders={orders}
      {...listActionsProps}
      {...pageListProps.loading}
      filtersList={filtersList}
      currentTab="custom"
      onAllProducts={() => undefined}
      onToFulfill={() => undefined}
      onToCapture={() => undefined}
      onCustomFilter={() => undefined}
    />
  ))
  .add("loading", () => (
    <OrderListPage
      orders={undefined}
      {...listActionsProps}
      {...pageListProps.loading}
      filtersList={undefined}
      currentTab={undefined}
      onAllProducts={() => undefined}
      onToFulfill={() => undefined}
      onToCapture={() => undefined}
      onCustomFilter={() => undefined}
    />
  ))
  .add("when no data", () => (
    <OrderListPage
      orders={[]}
      {...listActionsProps}
      {...pageListProps.default}
      filtersList={[]}
      currentTab="all"
      onAllProducts={() => undefined}
      onToFulfill={() => undefined}
      onToCapture={() => undefined}
      onCustomFilter={() => undefined}
    />
  ));
