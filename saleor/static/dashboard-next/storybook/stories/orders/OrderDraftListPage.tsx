import { storiesOf } from "@storybook/react";
import * as React from "react";

import { listActionsProps, pageListProps } from "../../../fixtures";
import OrderDraftListPage, {
  OrderDraftListPageProps
} from "../../../orders/components/OrderDraftListPage";
import { orders } from "../../../orders/fixtures";
import Decorator from "../../Decorator";

const props: OrderDraftListPageProps = {
  ...listActionsProps,
  ...pageListProps.default,
  onAdd: () => undefined,
  orders
};

storiesOf("Views / Orders / Draft order list", module)
  .addDecorator(Decorator)
  .add("default", () => <OrderDraftListPage {...props} />)
  .add("loading", () => (
    <OrderDraftListPage {...props} disabled orders={undefined} />
  ))
  .add("when no data", () => <OrderDraftListPage {...props} orders={[]} />);
