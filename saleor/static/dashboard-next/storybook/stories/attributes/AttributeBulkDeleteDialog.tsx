import { storiesOf } from "@storybook/react";
import * as React from "react";

import AttributeBulkDeleteDialog, {
  AttributeBulkDeleteDialogProps
} from "../../../attributes/components/AttributeBulkDeleteDialog";
import Decorator from "../../Decorator";

const props: AttributeBulkDeleteDialogProps = {

};

storiesOf("Attributes / AttributeBulkDeleteDialog", module)
  .addDecorator(Decorator)
  .add("default", () => <AttributeBulkDeleteDialog {...props} />);
