import { storiesOf } from "@storybook/react";
import { DialogContentText } from "material-ui/Dialog";
import * as React from "react";

import PageDetailsPage from "../../../pages/components/PageDetailsPage";
import { page } from "../../../pages/fixtures";

const callbacks = {
  onBack: () => {},
  onSubmit: () => {}
};

storiesOf("Views / Pages / Page details", module)
  .add("with initial data", () => (
    <PageDetailsPage page={page} {...callbacks} />
  ))
  .add("with delete button", () => (
    <PageDetailsPage page={page} {...callbacks} onDelete={() => {}} />
  ))
  .add("when loading", () => (
    <PageDetailsPage disabled={true} {...callbacks} />
  ));
