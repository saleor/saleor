import { storiesOf } from "@storybook/react";
import * as React from "react";

import CollectionAssignProductDialog, { CollectionAssignProductDialogProps } from "../../../collections/components/CollectionAssignProductDialog";
import Decorator from "../../Decorator";

const props:CollectionAssignProductDialogProps = {

}

storiesOf("Collections / CollectionAssignProductDialog", module)
  .addDecorator(Decorator)
  .add("default", () => <CollectionAssignProductDialog {...CollectionAssignProductDialogProps} />)
  .add("other", () => <CollectionAssignProductDialog {...CollectionAssignProductDialogProps} />);
