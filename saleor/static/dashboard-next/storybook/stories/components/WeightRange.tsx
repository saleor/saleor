import { storiesOf } from "@storybook/react";
import * as React from "react";

import WeightRange, { WeightRangeProps } from "../../../components/WeightRange";
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
  .addDecorator(Decorator)
  .add("from", () => <WeightRange {...props} to={undefined} />)
  .add("to", () => <WeightRange {...props} from={undefined} />)
  .add("range", () => <WeightRange {...props} />);
