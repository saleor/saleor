import { storiesOf } from "@storybook/react";
import React from "react";

import AttributeDeleteDialog, {
  AttributeDeleteDialogProps
} from "../../../attributes/components/AttributeDeleteDialog";
import Decorator from "../../Decorator";

const props: AttributeDeleteDialogProps = {
  confirmButtonState: "default",
  name: "Size",
  onClose: () => undefined,
  onConfirm: () => undefined,
  open: true
};

storiesOf("Attributes / Attribute delete", module)
  .addDecorator(Decorator)
  .add("default", () => <AttributeDeleteDialog {...props} />);
