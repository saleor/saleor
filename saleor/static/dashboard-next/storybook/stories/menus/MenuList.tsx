import { storiesOf } from "@storybook/react";
import * as React from "react";

import MenuList from "../../../menus/components/MenuList";
import Decorator from "../../Decorator";

storiesOf("Menus / MenuList", module)
  .addDecorator(Decorator)
  .add("default", () => <MenuList />)
  .add("other", () => <MenuList />);
