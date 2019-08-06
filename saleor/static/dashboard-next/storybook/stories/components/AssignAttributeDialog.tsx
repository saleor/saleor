import { storiesOf } from "@storybook/react";
import * as React from "react";

import { attributes } from "@saleor/attributes/fixtures";
import { fetchMoreProps } from "@saleor/fixtures";
import AssignAttributeDialog, {
  AssignAttributeDialogProps
} from "@saleor/productTypes/components/AssignAttributeDialog";
import { formError } from "@saleor/storybook/misc";
import Decorator from "../../Decorator";

const props: AssignAttributeDialogProps = {
  ...fetchMoreProps,
  attributes: attributes.slice(0, 5),
  confirmButtonState: "default",
  errors: [],
  onClose: () => undefined,
  onSubmit: () => undefined,
  onToggle: () => undefined,
  open: true,
  selected: [attributes[0].id, attributes[3].id]
};

storiesOf("Generics / Assign attributes dialog", module)
  .addDecorator(Decorator)
  .add("default", () => <AssignAttributeDialog {...props} />)
  .add("loading", () => (
    <AssignAttributeDialog {...props} attributes={undefined} loading={true} />
  ))
  .add("errors", () => (
    <AssignAttributeDialog {...props} errors={[formError("").message]} />
  ));
