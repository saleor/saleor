import { storiesOf } from "@storybook/react";
import * as React from "react";

import MenuItemDialog, {
  MenuItemDialogProps
} from "../../../navigation/components/MenuItemDialog";
import Decorator from "../../Decorator";

const props: MenuItemDialogProps = {
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
  open: true,
  pages: []
};

storiesOf("Navigation / Menu item create", module)
  .addDecorator(Decorator)
  .add("default", () => <MenuItemDialog {...props} />);
