import { storiesOf } from "@storybook/react";
import * as React from "react";

import MenuCreateItemDialog, {
  MenuCreateItemDialogProps
} from "../../../navigation/components/MenuCreateItemDialog";
import Decorator from "../../Decorator";

const props: MenuCreateItemDialogProps = {
  categories: [
    {
      __typename: "Category",
      id: "1",
      name: "Chairs"
    },
    {
      __typename: "Category",
      id: "2",
      name: "Desks"
    }
  ],
  collections: [],
  confirmButtonState: "default",
  disabled: false,
  loading: false,
  onClose: () => undefined,
  onQueryChange: () => undefined,
  onSubmit: () => undefined,
  open: true
};

storiesOf("Navigation / Menu item create", module)
  .addDecorator(Decorator)
  .add("default", () => <MenuCreateItemDialog {...props} />);
