import { storiesOf } from "@storybook/react";
import * as React from "react";

import Money, { MoneyProp } from "../../../components/Money";
import Decorator from "../../Decorator";

const moneyDetalis: MoneyProp = {
  amount: 12,
  currency: "EUR"
};

storiesOf("Generics / Money formatting", module)
  .addDecorator(Decorator)
  .add("default", () => <Money moneyDetalis={moneyDetalis} />);
