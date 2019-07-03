import { storiesOf } from "@storybook/react";
import React from "react";

import DeleteFilterTabDialog, {
  DeleteFilterTabDialogProps
} from "@saleor/components/DeleteFilterTabDialog";
import Decorator from "../../Decorator";

const props: DeleteFilterTabDialogProps = {
  confirmButtonState: "default",
  onClose: () => undefined,
  onSubmit: () => undefined,
  open: true,
  tabName: "Out of stock"
};

storiesOf("Generics / Delete filter tab", module)
  .addDecorator(Decorator)
  .add("default", () => <DeleteFilterTabDialog {...props} />);
