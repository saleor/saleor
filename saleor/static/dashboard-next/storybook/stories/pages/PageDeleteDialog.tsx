import { storiesOf } from "@storybook/react";
import * as React from "react";

import PageDeleteDialog from "../../../pages/components/PageDeleteDialog";
import Decorator from "../../Decorator";

storiesOf("Pages / PageDeleteDialog", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <PageDeleteDialog
      opened={true}
      onConfirm={() => {}}
      onClose={() => {}}
      title="Lorem Ipsum"
    />
  ));
