import { storiesOf } from "@storybook/react";
import * as React from "react";

import CategoryList from "../../../categories/components/CategoryList";
import Decorator from "../../Decorator";

storiesOf("Categories / CategoryList", module)
  .addDecorator(Decorator)
  .add("default", () => <CategoryList />)
  .add("other", () => <CategoryList />);
