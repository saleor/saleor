import { storiesOf } from "@storybook/react";
import * as React from "react";

import { pageListProps } from "../../../fixtures";
import MenuItemDetailsPage from "../../../menus/components/MenuItemDetailsPage";
import { menuItem, menuItems } from "../../../menus/fixtures";
import Decorator from "../../Decorator";

storiesOf("Views / Menus / Menu item details", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <MenuItemDetailsPage
      menuItem={menuItem}
      menuItems={menuItems}
      onBack={() => undefined}
      {...pageListProps.default}
    />
  ))
  .add("loading", () => (
    <MenuItemDetailsPage onBack={() => undefined} {...pageListProps.loading} />
  ))
  .add("no data", () => (
    <MenuItemDetailsPage
      menuItem={menuItem}
      menuItems={[]}
      onBack={() => undefined}
      {...pageListProps.noData}
    />
  ));
