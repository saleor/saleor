import { storiesOf } from "@storybook/react";
import * as React from "react";

import Weight, { WeightProps } from "../../../components/Weight";
import Decorator from "../../Decorator";

const props: WeightProps = {
  weight: {
    unit: "kg",
    value: 8.4
  }
};

storiesOf("Generics / Weight", module)
  .addDecorator(Decorator)
  .add("default", () => <Weight {...props} />);
