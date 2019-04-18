import { storiesOf } from "@storybook/react";
import * as React from "react";

import MenuListPage, {
  MenuListPageProps
} from "../../../navigation/components/MenuListPage";
import Decorator from "../../Decorator";

const props: MenuListPageProps = {

};

storiesOf("Navigation / MenuListPage", module)
  .addDecorator(Decorator)
  .add("default", () => <MenuListPage {...props} />);
