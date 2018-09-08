import { storiesOf } from "@storybook/react";
import * as React from "react";

import { configurationMenu } from "../../../configuration";
import ConfigurationPage from "../../../configuration/ConfigurationPage";
import Decorator from "../../Decorator";

storiesOf("Views / Configuration", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <ConfigurationPage
      menu={configurationMenu}
      onSectionClick={() => undefined}
    />
  ));
