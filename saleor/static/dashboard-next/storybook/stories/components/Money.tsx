import { storiesOf } from "@storybook/react";
import * as React from "react";

import Money, { MoneyProps } from "../../../components/Money";
import Decorator from "../../Decorator";

const props: MoneyProps = {
  money: {
    amount: 14,
    currency: "EUR"
  }
};

storiesOf("Generics / Money formatting", module)
  .addDecorator(Decorator)
  .add("default", () => <Money {...props} />);
