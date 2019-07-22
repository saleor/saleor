import { storiesOf } from "@storybook/react";
import React from "react";

import { DateTime } from "@saleor/components/Date";
import CardDecorator from "../../CardDecorator";
import Decorator from "../../Decorator";

storiesOf("Generics / DateTime", module)
  .addDecorator(CardDecorator)
  .addDecorator(Decorator)
  .add("default", () => <DateTime date="2018-04-07T10:44:44+00:00" />)
  .add("plain", () => (
    <DateTime date="2018-04-07T10:44:44+00:00" plain={true} />
  ));
