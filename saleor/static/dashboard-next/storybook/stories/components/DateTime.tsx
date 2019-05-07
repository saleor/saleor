import { storiesOf } from "@storybook/react";
import * as React from "react";

import { DateTime } from "../../../components/Date";
import Decorator from "../../Decorator";

storiesOf("Generics / DateTime", module)
  .addDecorator(Decorator)
  .add("default", () => <DateTime date="2018-04-07T10:44:44+00:00" />)
  .add("plain", () => (
    <DateTime date="2018-04-07T10:44:44+00:00" plain={true} />
  ));
