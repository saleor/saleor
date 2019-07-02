import { storiesOf } from "@storybook/react";
import React from "react";

import StatusLabel from "@saleor/components/StatusLabel";
import CardDecorator from "../../CardDecorator";
import Decorator from "../../Decorator";

storiesOf("Generics / StatusLabel", module)
.addDecorator(CardDecorator)
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
