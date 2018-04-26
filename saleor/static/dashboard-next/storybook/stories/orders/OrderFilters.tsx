import { storiesOf } from "@storybook/react";
import * as React from "react";

import OrderFilters from "../../../orders/components/OrderFilters";

storiesOf("orders / OrderFilters", module)
  .add("default", () => <OrderFilters />)
  .add("other", () => <OrderFilters />);
