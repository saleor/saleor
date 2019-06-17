import { storiesOf } from "@storybook/react";
import * as React from "react";

import AttributeValueDeleteDialog, {
  AttributeValueDeleteDialogProps
} from "../../../attributes/components/AttributeValueDeleteDialog";
import Decorator from "../../Decorator";

const props: AttributeValueDeleteDialogProps = {

};

storiesOf("Attributes / AttributeValueDeleteDialog", module)
  .addDecorator(Decorator)
  .add("default", () => <AttributeValueDeleteDialog {...props} />);
