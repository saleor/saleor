import { storiesOf } from "@storybook/react";
import * as React from "react";

import ProductTypeBulkAttributeUnassignDialog, {
  ProductTypeBulkAttributeUnassignDialogProps
} from "../../../productTypes/components/ProductTypeBulkAttributeUnassignDialog";
import Decorator from "../../Decorator";

const props: ProductTypeBulkAttributeUnassignDialogProps = {
  attributeQuantity: "4",
  confirmButtonState: "default",
  onClose: () => undefined,
  onConfirm: () => undefined,
  open: true,
  productTypeName: "Shoes"
};

storiesOf("Views / Product types / Unassign multiple attributes", module)
  .addDecorator(Decorator)
  .add("default", () => <ProductTypeBulkAttributeUnassignDialog {...props} />);
