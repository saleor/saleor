import { storiesOf } from "@storybook/react";
import * as React from "react";

import { attributes } from "@saleor/attributes/fixtures";
import { formError } from "@saleor/storybook/misc";
import { AttributeValueType } from "@saleor/types/globalTypes";
import AttributeValueEditDialog, {
  AttributeValueEditDialogProps
} from "../../../attributes/components/AttributeValueEditDialog";
import Decorator from "../../Decorator";

const props: AttributeValueEditDialogProps = {
  attributeValue: {
    ...attributes[0].values[0],
    sortOrder: 0,
    type: AttributeValueType.STRING,
    value: ""
  },
  confirmButtonState: "default",
  disabled: false,
  errors: [],
  onClose: () => undefined,
  onSubmit: () => undefined,
  open: true
};

storiesOf("Attributes / Attribute value edit", module)
  .addDecorator(Decorator)
  .add("default", () => <AttributeValueEditDialog {...props} />)
  .add("form errors", () => (
    <AttributeValueEditDialog
      {...props}
      errors={["name", "slug"].map(formError)}
    />
  ));
