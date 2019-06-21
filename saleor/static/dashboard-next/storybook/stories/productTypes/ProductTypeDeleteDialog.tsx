import { storiesOf } from "@storybook/react";
import * as React from "react";

import ProductTypeDeleteDialog, {
  ProductTypeDeleteDialogProps
} from "../../../productTypes/components/ProductTypeDeleteDialog";
import Decorator from "../../Decorator";

const props: ProductTypeDeleteDialogProps = {
  confirmButtonState: "default",
  name: "Shoes",
  onClose: () => undefined,
  onConfirm: () => undefined,
  open: true
};

storiesOf("Product types / ProductTypeDeleteDialog", module)
  .addDecorator(Decorator)
  .add("default", () => <ProductTypeDeleteDialog {...props} />);
