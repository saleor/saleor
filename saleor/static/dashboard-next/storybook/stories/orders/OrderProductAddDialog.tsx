import { storiesOf } from "@storybook/react";
import * as React from "react";

import OrderProductAddDialog from "../../../orders/components/OrderProductAddDialog";
import { variants } from "../../../orders/fixtures";
import Decorator from "../../Decorator";

storiesOf("Orders / OrderProductAddDialog", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <OrderProductAddDialog
      confirmButtonState="default"
      loading={false}
      open={true}
      onClose={undefined}
      variants={variants}
      fetchVariants={undefined}
      onSubmit={undefined}
    />
  ));
