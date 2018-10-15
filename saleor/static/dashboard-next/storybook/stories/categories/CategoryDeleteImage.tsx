import { storiesOf } from "@storybook/react";
import * as React from "react";

import CategoryDeleteImage from "../../../categories/components/CategoryDeleteImage";
import Decorator from "../../Decorator";

storiesOf("Views / Categories / Remove image dialog", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <CategoryDeleteImage
      open={true}
      onClose={undefined}
      onConfirm={undefined}
      title={"Remove"}
      dialogText={"Do you want to remove this image"}
    />
  ));
