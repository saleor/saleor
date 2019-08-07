import { storiesOf } from "@storybook/react";
import * as React from "react";

import ProductTypeAttributeUnassignDialog, {
  ProductTypeAttributeUnassignDialogProps
} from "../../../productTypes/components/ProductTypeAttributeUnassignDialog";
import Decorator from "../../Decorator";

const props: ProductTypeAttributeUnassignDialogProps = {
  attributeName: "Size",
  confirmButtonState: "default",
  onClose: () => undefined,
  onConfirm: () => undefined,
  open: true,
  productTypeName: "Shoes"
};

storiesOf("Views / Product types / Unassign attribute", module)
  .addDecorator(Decorator)
  .add("default", () => <ProductTypeAttributeUnassignDialog {...props} />);
