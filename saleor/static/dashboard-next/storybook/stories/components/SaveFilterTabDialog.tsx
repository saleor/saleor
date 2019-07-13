import { storiesOf } from "@storybook/react";
import React from "react";

import SaveFilterTabDialog, {
  SaveFilterTabDialogProps
} from "@saleor/components/SaveFilterTabDialog";
import Decorator from "../../Decorator";

const props: SaveFilterTabDialogProps = {
  confirmButtonState: "default",
  onClose: () => undefined,
  onSubmit: () => undefined,
  open: true
};

storiesOf("Generics / Save filter tab", module)
  .addDecorator(Decorator)
  .add("default", () => <SaveFilterTabDialog {...props} />);
