import { storiesOf } from "@storybook/react";
import * as React from "react";

import OrderList from "../../../orders/components/OrderList";
import { orders } from "../../../orders/fixtures";

storiesOf("orders / OrderList", module)
  .add("when loading data", () => <OrderList />)
  .add("when loaded data", () => (
    <OrderList orders={orders.edges.map(edge => edge.node)} />
  ))
  .add("when no data", () => <OrderList orders={[]} />);
