import { storiesOf } from "@storybook/react";
import React from "react";

import MoneyRange, { MoneyRangeProps } from "@saleor/components/MoneyRange";
import CardDecorator from "../../CardDecorator";
import Decorator from "../../Decorator";

const props: MoneyRangeProps = {
  from: {
    amount: 5.2,
    currency: "USD"
  },
  to: {
    amount: 10.6,
    currency: "USD"
  }
};

storiesOf("Generics / Money range", module)
  .addDecorator(CardDecorator)
  .addDecorator(Decorator)
  .add("from", () => <MoneyRange {...props} to={undefined} />)
  .add("to", () => <MoneyRange {...props} from={undefined} />)
  .add("range", () => <MoneyRange {...props} />);
