import { storiesOf } from "@storybook/react";
import * as React from "react";

import Percent from "@components/Percent";
import CardDecorator from "../../CardDecorator";
import Decorator from "../../Decorator";

storiesOf("Generics / Percent formatting", module)
  .addDecorator(CardDecorator)
  .addDecorator(Decorator)
  .add("default", () => <Percent amount={96.14} />);
