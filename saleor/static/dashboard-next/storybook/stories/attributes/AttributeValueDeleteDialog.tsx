import { storiesOf } from "@storybook/react";
import React from "react";

import AttributeValueDeleteDialog, {
  AttributeValueDeleteDialogProps
} from "../../../attributes/components/AttributeValueDeleteDialog";
import Decorator from "../../Decorator";

const props: AttributeValueDeleteDialogProps = {
  attributeName: "Size",
  confirmButtonState: "default",
  name: "XS",
  onClose: () => undefined,
  onConfirm: () => undefined,
  open: true
};

storiesOf("Attributes / Attribute value delete", module)
  .addDecorator(Decorator)
  .add("default", () => <AttributeValueDeleteDialog {...props} />);
