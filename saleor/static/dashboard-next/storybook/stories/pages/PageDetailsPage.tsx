import { Omit } from "@material-ui/core";
import { storiesOf } from "@storybook/react";
import * as React from "react";

import PageDetailsPage, {
  PageDetailsPageProps
} from "../../../pages/components/PageDetailsPage";
import { page } from "../../../pages/fixtures";
import Decorator from "../../Decorator";

const callbacks: Omit<PageDetailsPageProps, "classes"> = {
  onBack: () => undefined,
  onSubmit: () => undefined,
  saveButtonBarState: "default"
};

storiesOf("Views / Pages / Page details", module)
  .addDecorator(Decorator)
  .add("with initial data", () => (
    <PageDetailsPage title="Lorem Ipsum" page={page} {...callbacks} />
  ))
  .add("when loading", () => (
    <PageDetailsPage disabled={true} {...callbacks} />
  ));
