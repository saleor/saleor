import { storiesOf } from "@storybook/react";
import React from "react";

import Percent from "@saleor/components/Percent";
import CardDecorator from "../../CardDecorator";
import Decorator from "../../Decorator";

storiesOf("Generics / Percent formatting", module)
  .addDecorator(CardDecorator)
  .addDecorator(Decorator)
  .add("default", () => <Percent amount={96.14} />);
