import { storiesOf } from "@storybook/react";
import * as React from "react";

import AttributeValueBulkDeleteDialog, {
  AttributeValueBulkDeleteDialogProps
} from "../../../attributes/components/AttributeValueBulkDeleteDialog";
import Decorator from "../../Decorator";

const props: AttributeValueBulkDeleteDialogProps = {

};

storiesOf("Attributes / AttributeValueBulkDeleteDialog", module)
  .addDecorator(Decorator)
  .add("default", () => <AttributeValueBulkDeleteDialog {...props} />);
