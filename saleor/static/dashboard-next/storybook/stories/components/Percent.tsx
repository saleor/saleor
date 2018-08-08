import { storiesOf } from "@storybook/react";
import * as React from "react";

import Percent from "../../../components/Percent";
import Decorator from "../../Decorator";

storiesOf("Generics / Percent formatting", module)
  .addDecorator(Decorator)
  .add("default", () => <Percent amount={96.14} />);
