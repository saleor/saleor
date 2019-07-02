import { storiesOf } from "@storybook/react";
import React from "react";

import AttributeBulkDeleteDialog, {
  AttributeBulkDeleteDialogProps
} from "../../../attributes/components/AttributeBulkDeleteDialog";
import Decorator from "../../Decorator";

const props: AttributeBulkDeleteDialogProps = {
  confirmButtonState: "default",
  onClose: () => undefined,
  onConfirm: () => undefined,
  open: true,
  quantity: "5"
};

storiesOf("Attributes / Delete multiple attributes", module)
  .addDecorator(Decorator)
  .add("default", () => <AttributeBulkDeleteDialog {...props} />);
