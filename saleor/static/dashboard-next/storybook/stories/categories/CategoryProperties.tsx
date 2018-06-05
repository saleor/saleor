import { storiesOf } from "@storybook/react";
import * as React from "react";

import CategoryProperties from "../../../categories/components/CategoryProperties";
import Decorator from "../../Decorator";

storiesOf("Categories / CategoryProperties", module)
  .addDecorator(Decorator)
  .add("default", () => <CategoryProperties />)
  .add("other", () => <CategoryProperties />);
