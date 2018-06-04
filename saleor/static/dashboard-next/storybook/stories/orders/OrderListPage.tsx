import { storiesOf } from "@storybook/react";
import * as React from "react";

import OrderListPage from "../../../orders/components/OrderListPage";
import { orders } from "../../../orders/fixtures";
import Decorator from "../../Decorator";

storiesOf("Views / Orders / Order list", module)
  .addDecorator(Decorator)
  .add("when loaded data", () => (
    <OrderListPage onBack={() => {}} onRowClick={() => {}} />
  ))
  .add("when loading data", () => (
    <OrderListPage onBack={() => {}} orders={orders} onRowClick={() => {}} />
  ))
  .add("when no data", () => (
    <OrderListPage
      onBack={() => {}}
      orders={{ edges: [] }}
      onRowClick={() => {}}
    />
  ));
