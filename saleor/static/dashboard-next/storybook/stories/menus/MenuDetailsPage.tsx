import { storiesOf } from "@storybook/react";
import * as React from "react";

import { pageListProps } from "../../../fixtures";
import MenuDetailsPage from "../../../menus/components/MenuDetailsPage";
import { menu, menuItems } from "../../../menus/fixtures";
import Decorator from "../../Decorator";

storiesOf("Views / Menus / Menu details page", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <MenuDetailsPage
      menu={menu}
      menuItems={menuItems}
      onBack={() => undefined}
      onMenuItemAdd={undefined}
      {...pageListProps.default}
    />
  ))
  .add("loading", () => (
    <MenuDetailsPage
      onBack={() => undefined}
      onMenuItemAdd={undefined}
      {...pageListProps.loading}
    />
  ))
  .add("no items", () => (
    <MenuDetailsPage
      menu={menu}
      menuItems={[]}
      onBack={() => undefined}
      onMenuItemAdd={undefined}
      {...pageListProps.noData}
    />
  ));
