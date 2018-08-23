import { storiesOf } from "@storybook/react";
import * as React from "react";

import Form from "../../../components/Form";
import OrderProductAddDialog from "../../../orders/components/OrderProductAddDialog";
import { variants } from "../../../orders/fixtures";
import Decorator from "../../Decorator";

storiesOf("Orders / OrderProductAddDialog", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <Form initial={{ quantity: 0, variant: { label: "", value: "" } }}>
      {({ change, data }) => (
        <OrderProductAddDialog
          open={true}
          onChange={change}
          onConfirm={undefined}
          onClose={undefined}
          variants={variants}
          fetchVariants={undefined}
          quantity={data.quantity}
          variant={data.variant}
        />
      )}
    </Form>
  ));
