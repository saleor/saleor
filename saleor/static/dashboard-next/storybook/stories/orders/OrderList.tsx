import { storiesOf } from "@storybook/react";
import * as React from "react";

import OrderList from "../../../orders/components/OrderList";
import { flatOrders } from "../../../orders/fixtures";
import Decorator from "../../Decorator";

storiesOf("Orders / OrderList", module)
  .addDecorator(Decorator)
  .add("when loading data", () => <OrderList />)
  .add("when loaded data", () => <OrderList orders={flatOrders} />)
  .add("with clickable rows", () => (
    <OrderList orders={flatOrders} onRowClick={() => {}} />
  ))
  .add("when no data", () => <OrderList orders={[]} />);
