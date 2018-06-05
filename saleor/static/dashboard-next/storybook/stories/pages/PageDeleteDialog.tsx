import { storiesOf } from "@storybook/react";
import * as React from "react";

import PageDeleteDialog from "../../../pages/components/PageDeleteDialog";

storiesOf("Pages / PageDeleteDialog", module).add("default", () => (
  <PageDeleteDialog
    opened={true}
    onConfirm={() => {}}
    onClose={() => {}}
    title="Lorem Ipsum"
  />
));
