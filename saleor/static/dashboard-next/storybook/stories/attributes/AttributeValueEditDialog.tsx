import { storiesOf } from "@storybook/react";
import * as React from "react";

import AttributeValueEditDialog, {
  AttributeValueEditDialogProps
} from "../../../attributes/components/AttributeValueEditDialog";
import Decorator from "../../Decorator";

const props: AttributeValueEditDialogProps = {

};

storiesOf("Attributes / AttributeValueEditDialog", module)
  .addDecorator(Decorator)
  .add("default", () => <AttributeValueEditDialog {...props} />);
