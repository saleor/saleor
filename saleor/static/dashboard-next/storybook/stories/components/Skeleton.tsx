import { storiesOf } from "@storybook/react";
import React from "react";

import Skeleton from "@saleor/components/Skeleton";
import CardDecorator from "../../CardDecorator";
import Decorator from "../../Decorator";

storiesOf("Generics / Skeleton", module)
  .addDecorator(CardDecorator)
  .addDecorator(Decorator)
  .add("default", () => <Skeleton />);
