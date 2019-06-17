import { storiesOf } from "@storybook/react";
import * as React from "react";

import AttributeDeleteDialog, {
  AttributeDeleteDialogProps
} from "../../../attributes/components/AttributeDeleteDialog";
import Decorator from "../../Decorator";

const props: AttributeDeleteDialogProps = {

};

storiesOf("Attributes / AttributeDeleteDialog", module)
  .addDecorator(Decorator)
  .add("default", () => <AttributeDeleteDialog {...props} />);
