import { storiesOf } from "@storybook/react";
import * as React from "react";

import MenuDetailsPage, {
  MenuDetailsPageProps
} from "../../../navigation/components/MenuDetailsPage";
import { menu } from "../../../navigation/fixtures";
import Decorator from "../../Decorator";

const props: MenuDetailsPageProps = {
  disabled: false,
  menu,
  onBack: () => undefined
};

storiesOf("Views / Navigation / Menu details", module)
  .addDecorator(Decorator)
  .add("default", () => <MenuDetailsPage {...props} />)
  .add("loading", () => (
    <MenuDetailsPage {...props} disabled={true} menu={undefined} />
  ));
