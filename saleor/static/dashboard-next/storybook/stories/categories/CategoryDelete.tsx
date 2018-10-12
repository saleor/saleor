import { storiesOf } from "@storybook/react";
import * as React from "react";

import CategoryDelete from "../../../categories/components/CategoryDelete";
import Decorator from "../../Decorator";

storiesOf("Categories / Remove image dialog", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <CategoryDelete
      open={true}
      onClose={undefined}
      onConfirm={undefined}
      title={"Remove"}
      dialogText={"Do you want to remove this"}
    />
  ));
