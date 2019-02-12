import { storiesOf } from "@storybook/react";
import * as React from "react";

import PageDetailsPage, {
  PageDetailsPageProps
} from "../../../pages/components/PageDetailsPage";
import { page } from "../../../pages/fixtures";
import Decorator from "../../Decorator";

const props: PageDetailsPageProps = {
  disabled: false,
  onBack: () => undefined,
  onRemove: () => undefined,
  onSubmit: () => undefined,
  page,
  saveButtonBarState: "default"
};

storiesOf("Views / Pages / Page details", module)
  .addDecorator(Decorator)
  .add("default", () => <PageDetailsPage {...props} />)
  .add("loading", () => (
    <PageDetailsPage {...props} disabled={true} page={undefined} />
  ));
