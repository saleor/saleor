import { storiesOf } from "@storybook/react";
import * as React from "react";

import { pageListProps } from "../../../fixtures";
import MenuListPage, {
  MenuListPageProps
} from "../../../navigation/components/MenuListPage";
import { menuList } from "../../../navigation/fixtures";
import Decorator from "../../Decorator";

const props: MenuListPageProps = {
  ...pageListProps.default,
  menus: menuList,
  onDelete: () => undefined
};

storiesOf("Views / Navigation / Menu list", module)
  .addDecorator(Decorator)
  .add("default", () => <MenuListPage {...props} />)
  .add("loading", () => <MenuListPage {...props} menus={undefined} />)
  .add("no data", () => <MenuListPage {...props} menus={[]} />);
