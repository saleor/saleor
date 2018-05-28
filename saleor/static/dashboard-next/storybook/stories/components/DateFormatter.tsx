import { storiesOf } from "@storybook/react";
import * as React from "react";

import DateFormatter from "../../../components/DateFormatter";
import Decorator from "../../Decorator";

storiesOf("Generics / DateFormatter", module)
  .addDecorator(Decorator)
  .add("default", () => <DateFormatter date="2018-04-07T10:44:44+00:00" />)
  .add("humanized", () => (
    <DateFormatter date={"2018-05-27T22:44:44+00:00"} dateNow={1527521275866} />
  ))
  .add("humanized without tooltip", () => (
    <DateFormatter
      date={"2018-05-27T22:44:44+00:00"}
      dateNow={1527521275866}
      showTooltip={false}
    />
  ))
  .add("with custom format", () => (
    <DateFormatter
      date="01.04.1999 14:30"
      showTooltip={false}
      inputFormat="DD.MM.YYYY HH:mm"
      outputFormat="MM/DD/YYYY"
    />
  ));
