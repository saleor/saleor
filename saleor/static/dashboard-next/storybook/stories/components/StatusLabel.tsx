import { storiesOf } from "@storybook/react";
import * as React from "react";

import StatusLabel from "../../../components/StatusLabel";
import Decorator from "../../Decorator";

storiesOf("Generics / StatusLabel", module)
  .addDecorator(Decorator)
  .add("when success", () => (
    <StatusLabel label="Example label" status="success" />
  ))
  .add("when neutral", () => (
    <StatusLabel label="Example label" status="neutral" />
  ))
  .add("when error", () => (
    <StatusLabel label="Example label" status="error" />
  ));
