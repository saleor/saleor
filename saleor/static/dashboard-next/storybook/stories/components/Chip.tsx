import { storiesOf } from "@storybook/react";
import React from "react";

import Chip, { ChipProps } from "@saleor/components/Chip";
import CardDecorator from "../../CardDecorator";
import Decorator from "../../Decorator";

const props: ChipProps = {
  label: "Lorem Ipsum"
};

storiesOf("Generics / Chip", module)
  .addDecorator(CardDecorator)
  .addDecorator(Decorator)
  .add("default", () => <Chip {...props} />)
  .add("with x", () => <Chip {...props} onClose={() => undefined} />);
