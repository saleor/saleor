import { storiesOf } from "@storybook/react";
import React from "react";

import ActionDialog from "@saleor/components/ActionDialog";
import Decorator from "../../Decorator";

storiesOf("Generics / ActionDialog", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <ActionDialog
      title="Example title"
      open={true}
      onClose={undefined}
      onConfirm={undefined}
      confirmButtonState="default"
    >
      Example content
    </ActionDialog>
  ));
