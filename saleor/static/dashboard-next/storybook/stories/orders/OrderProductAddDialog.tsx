import { storiesOf } from "@storybook/react";
import * as React from "react";

import * as placeholderImage from "../../../../images/placeholder60x60.png";
import OrderProductAddDialog from "../../../orders/components/OrderProductAddDialog";
import { orderLineSearch } from "../../../orders/fixtures";
import Decorator from "../../Decorator";

storiesOf("Orders / OrderProductAddDialog", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <OrderProductAddDialog
      confirmButtonState="default"
      loading={false}
      open={true}
      onClose={undefined}
      onSubmit={undefined}
      hasMore={false}
      onFetch={() => undefined}
      onFetchMore={() => undefined}
      products={orderLineSearch(placeholderImage)}
    />
  ));
