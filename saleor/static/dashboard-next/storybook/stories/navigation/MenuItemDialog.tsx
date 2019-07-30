import { storiesOf } from "@storybook/react";
import React from "react";

import { formError } from "@saleor/storybook/misc";
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
  errors: [],
  loading: false,
  onClose: () => undefined,
  onQueryChange: () => undefined,
  onSubmit: () => undefined,
  open: true,
  pages: []
};

storiesOf("Navigation / Menu item", module)
  .addDecorator(Decorator)
  .add("default", () => <MenuItemDialog {...props} />)
  .add("edit", () => (
    <MenuItemDialog
      {...props}
      initial={{
        ...props.categories[0],
        type: "category"
      }}
      initialDisplayValue={props.categories[0].name}
    />
  ))
  .add("errors", () => (
    <MenuItemDialog
      {...props}
      errors={["", "", "name", "category"].map(formError)}
    />
  ));
