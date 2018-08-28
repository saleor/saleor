import { storiesOf } from "@storybook/react";
import * as React from "react";

import { pageListProps } from "../../../fixtures";
import MenuListPage from "../../../menus/components/MenuListPage";
import { menus } from "../../../menus/fixtures";
import Decorator from "../../Decorator";

storiesOf("Views / Menus / MenuListPage", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <MenuListPage menus={menus} {...pageListProps.default} />
  ))
  .add("loading", () => (
    <MenuListPage disabled={true} {...pageListProps.loading} />
  ));
