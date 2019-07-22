import { storiesOf } from "@storybook/react";
import React from "react";

import Money, { MoneyProps } from "@saleor/components/Money";
import CardDecorator from "../../CardDecorator";
import Decorator from "../../Decorator";

const props: MoneyProps = {
  money: {
    amount: 14,
    currency: "EUR"
  }
};

storiesOf("Generics / Money formatting", module)
  .addDecorator(CardDecorator)
  .addDecorator(Decorator)
  .add("default", () => <Money {...props} />);
