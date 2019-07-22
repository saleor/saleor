import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { storiesOf } from "@storybook/react";
import React from "react";

import AutocompleteSelectMenu, {
  AutocompleteSelectMenuProps
} from "@saleor/components/AutocompleteSelectMenu";
import Form from "@saleor/components/Form";
import { getMenuItemByValue, IMenu } from "../../../utils/menu";
import Decorator from "../../Decorator";

const menu: IMenu = [
  {
    children: [],
    data: null,
    label: "Item 1",
    value: "item1"
  },
  {
    children: [
      {
        children: [],
        data: null,
        label: "Item 1.1",
        value: "item1.1"
      },
      {
        children: [],
        data: null,
        label: "Item 1.2",
        value: "item1.2"
      }
    ],
    data: null,
    label: "Menu 1"
  },
  {
    children: [],
    data: null,
    label: "Item 3",
    value: "item3"
  },
  {
    children: [],
    data: null,
    label: "Item 4",
    value: "item4"
  },
  {
    children: [
      {
        children: [],
        data: null,
        label: "Item 5.1",
        value: "item5.1"
      },
      {
        children: [],
        data: null,
        label: "Item 5.2",
        value: "item5.2"
      }
    ],
    data: null,
    label: "Menu 5"
  }
];

const props: AutocompleteSelectMenuProps = {
  disabled: false,
  displayValue: menu[1].children[1].label.toString(),
  error: false,
  helperText: undefined,
  label: "Autocomplete Menu",
  loading: false,
  name: "menu",
  onChange: () => undefined,
  options: menu,
  placeholder: "Start typing to search ..."
};

storiesOf("Generics / Autocomplete Menu", module)
  .addDecorator(storyFn => (
    <Card
      style={{
        margin: "auto",
        overflow: "visible",
        width: 400
      }}
    >
      <CardContent>{storyFn()}</CardContent>
    </Card>
  ))
  .addDecorator(Decorator)
  .add("default", () => <AutocompleteSelectMenu {...props} />)
  .add("loading", () => <AutocompleteSelectMenu {...props} loading={true} />)
  .add("error", () => (
    <AutocompleteSelectMenu
      {...props}
      error={true}
      helperText="Generic form error"
    />
  ))
  .add("interactive", () => (
    <Form initial={{ menu: menu[1].children[1].value }}>
      {({ change, data }) => (
        <AutocompleteSelectMenu
          {...props}
          displayValue={getMenuItemByValue(menu, data.menu).label.toString()}
          onChange={change}
        />
      )}
    </Form>
  ));
