import { storiesOf } from "@storybook/react";
import * as React from "react";

import { attributes } from "@saleor/attributes/fixtures";
import AssignAttributeDialog, {
  AssignAttributeDialogProps
} from "../../../components/AssignAttributeDialog";
import Decorator from "../../Decorator";

const props: AssignAttributeDialogProps = {
  attributes: attributes.slice(0, 5),
  confirmButtonState: "default",
  loading: false,
  onClose: () => undefined,
  onFetch: () => undefined,
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
  ));
