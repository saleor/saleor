import { storiesOf } from "@storybook/react";
import * as React from "react";
import * as moment from "moment";

import DateFormatter from "../../../components/DateFormatter";
import Decorator from "../../Decorator";

storiesOf("Generics / DateFormatter", module)
  .addDecorator(Decorator)
  .add("default", () => <DateFormatter date="2018-04-07T10:44:44+00:00" />)
  .add("without tooltip", () => (
    <DateFormatter date="2018-04-07T10:44:44+00:00" showTooltip={false} />
  ))
  .add("humanized", () => (
    <DateFormatter
      date={moment()
        .subtract(1, "days")
        .format()}
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
