import { storiesOf } from "@storybook/react";
import React from "react";

import WeightRange, { WeightRangeProps } from "@saleor/components/WeightRange";
import CardDecorator from "../../CardDecorator";
import Decorator from "../../Decorator";

const props: WeightRangeProps = {
  from: {
    unit: "kg",
    value: 4.2
  },
  to: {
    unit: "kg",
    value: 81.9
  }
};

storiesOf("Generics / Weight range", module)
  .addDecorator(CardDecorator)
  .addDecorator(Decorator)
  .add("from", () => <WeightRange {...props} to={undefined} />)
  .add("to", () => <WeightRange {...props} from={undefined} />)
  .add("range", () => <WeightRange {...props} />);
