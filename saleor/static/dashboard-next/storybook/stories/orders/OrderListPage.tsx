import { storiesOf } from "@storybook/react";
import React from "react";

import OrderListPage, {
  OrderListPageProps
} from "@saleor/orders/components/OrderListPage";
import {
  filterPageProps,
  filters,
  listActionsProps,
  pageListProps
} from "../../../fixtures";
import { orders } from "../../../orders/fixtures";
import Decorator from "../../Decorator";

const props: OrderListPageProps = {
  ...listActionsProps,
  ...pageListProps.default,
  ...filterPageProps,
  orders
};

storiesOf("Views / Orders / Order list", module)
  .addDecorator(Decorator)
  .add("default", () => <OrderListPage {...props} />)
  .add("with custom filters", () => (
    <OrderListPage {...props} filtersList={filters} />
  ))
  .add("loading", () => (
    <OrderListPage
      {...props}
      orders={undefined}
      currentTab={undefined}
      disabled={true}
    />
  ))
  .add("when no data", () => <OrderListPage {...props} orders={[]} />);
