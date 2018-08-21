import { storiesOf } from "@storybook/react";
import * as React from "react";

import PageContent from "../../../pages/components/PageContent";
import { page } from "../../../pages/fixtures";
import Decorator from "../../Decorator";

storiesOf("Pages / PageContent", module)
  .addDecorator(Decorator)
  .add("when loaded", () => <PageContent errors={{}} {...page} />)
  .add("when loading", () => (
    <PageContent errors={{}} loading={true} content="" title="" />
  ))
  .add("with errors", () => (
    <PageContent
      errors={{
        content: "Generic error",
        title: "Generic error"
      }}
      loading={true}
      content=""
      title=""
    />
  ));
