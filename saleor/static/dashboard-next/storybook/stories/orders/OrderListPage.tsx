import { storiesOf } from "@storybook/react";
import * as React from "react";

import { pageListProps } from "../../../fixtures";
import OrderListPage from "../../../orders/components/OrderListPage";
import { orders } from "../../../orders/fixtures";
import Decorator from "../../Decorator";

storiesOf("Views / Orders / Order list", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <OrderListPage orders={orders} {...pageListProps.default} />
  ))
  .add("loading", () => <OrderListPage {...pageListProps.loading} />)
  .add("when no data", () => (
    <OrderListPage orders={[]} {...pageListProps.default} />
  ));
