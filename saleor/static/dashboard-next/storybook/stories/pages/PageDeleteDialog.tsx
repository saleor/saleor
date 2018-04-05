import { storiesOf } from "@storybook/react";
import { DialogContentText } from "material-ui/Dialog";
import * as React from "react";

import PageDeleteDialog from "../../../page/components/PageDeleteDialog";

storiesOf("Pages / PageDeleteDialog", module).add("default", () => (
  <PageDeleteDialog opened={true}>
    <DialogContentText>
      Do you really want to delete this page?
    </DialogContentText>
  </PageDeleteDialog>
));
