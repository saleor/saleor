import { storiesOf } from "@storybook/react";
import * as React from "react";

import PageProperties from "../../../pages/components/PageProperties";
import { page } from "../../../pages/fixtures";
import Decorator from "../../Decorator";

storiesOf("Pages / PageProperties", module)
  .addDecorator(Decorator)
  .add("when loaded", () => <PageProperties {...page} />)
  .add("when loading", () => (
    <PageProperties loading={true} availableOn="" isVisible={false} />
  ));
