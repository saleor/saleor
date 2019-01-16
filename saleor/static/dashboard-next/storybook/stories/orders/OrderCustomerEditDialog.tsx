import { storiesOf } from "@storybook/react";
import * as React from "react";

import OrderCustomerEditDialog from "../../../orders/components/OrderCustomerEditDialog";
import { clients as users } from "../../../orders/fixtures";
import Decorator from "../../Decorator";

const user = users[0];

storiesOf("Orders / OrderCustomerEditDialog", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <OrderCustomerEditDialog
      confirmButtonState="default"
      fetchUsers={undefined}
      onChange={undefined}
      onClose={undefined}
      onConfirm={undefined}
      open={true}
      user={{
        label: user.email,
        value: user.id
      }}
      users={users}
    />
  ));
