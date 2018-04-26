import { storiesOf } from "@storybook/react";
import * as React from "react";

import OrderListPage from "../../../orders/components/OrderListPage";
import { orders } from "../../../orders/fixtures";

storiesOf("orders / OrderListPage", module)
  .add("default", () => <OrderListPage onBack={() => {}} orders={orders} />)
  .add("other", () => <OrderListPage onBack={() => {}} />);
