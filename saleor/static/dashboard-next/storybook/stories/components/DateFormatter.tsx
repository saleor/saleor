import { storiesOf } from "@storybook/react";
import * as React from "react";

import DateFormatter from "../../../components/DateFormatter";
import Decorator from "../../Decorator";

storiesOf("Generics / DateFormatter", module)
  .addDecorator(Decorator)
  .add("default", () => <DateFormatter date="2018-04-07T10:44:44+00:00" />);
