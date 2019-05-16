import { storiesOf } from "@storybook/react";
import * as React from "react";

import { FilterContent, FilterContentProps } from "../../../components/Filter";
import CardDecorator from "../../CardDecorator";
import Decorator from "../../Decorator";

const props: FilterContentProps = {};

storiesOf("Generics / Filter", module)
  .addDecorator(CardDecorator)
  .addDecorator(Decorator)
  .add("default", () => <FilterContent {...props} />);
